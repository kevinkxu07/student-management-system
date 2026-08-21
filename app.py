from flask import Flask, render_template, request, redirect, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from functools import wraps
import pymysql
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-local-only')
app.permanent_session_lifetime = timedelta(minutes=30)


@app.before_request
def refresh_session():
    session.modified = True


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'admin' not in session:
            return jsonify({'error': '未登录或登录已过期'}), 401
        return f(*args, **kwargs)
    return wrapper


def get_db():
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'student_system'),
        charset='utf8mb4'
    )


# ==================== 页面路由 ====================

@app.route('/vue')
def vue_page():
    return render_template('vue_students.html')


@app.route('/students')
def students():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student")
    data = cursor.fetchall()
    conn.close()
    return render_template('students.html', students=data)


@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO student (student_no, name, gender, class_name, major, enroll_year) VALUES (%s, %s, %s, %s, %s, %s)",
            (request.form['student_no'], request.form['name'], request.form['gender'],
             request.form['class_name'], request.form['major'], request.form['enroll_year'])
        )
        conn.commit()
        conn.close()
        return redirect('/students')
    return render_template('add.html')


# ==================== 登录认证 ====================

@app.route('/api/init-admin')
def init_admin():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin WHERE username = %s", ('admin',))
    if cursor.fetchone():
        conn.close()
        return jsonify({'message': '管理员已存在'})
    hashed = generate_password_hash('admin123')
    cursor.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", ('admin', hashed))
    conn.commit()
    conn.close()
    return jsonify({'message': '管理员创建成功，账号 admin 密码 admin123'})


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('username').strip():
        return jsonify({'success': False, 'message': '用户名不能为空'})
    if not data.get('password'):
        return jsonify({'success': False, 'message': '密码不能为空'})

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM admin WHERE username = %s", (data['username'].strip(),))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['password'], data['password']):
        session.permanent = True
        session['admin'] = user['username']
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '用户名或密码错误'})


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('admin', None)
    return jsonify({'success': True})


@app.route('/api/check-login')
def check_login():
    if 'admin' in session:
        return jsonify({'logged_in': True, 'username': session['admin']})
    return jsonify({'logged_in': False})


# ==================== 学生管理 ====================

@app.route('/api/students')
@login_required
def api_students():
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM student ORDER BY id")
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


@app.route('/api/students', methods=['POST'])
@login_required
def api_add_student():
    data = request.get_json()
    student_no = str(data.get('student_no', '')).strip()
    name = str(data.get('name', '')).strip()

    if not student_no or not name:
        return jsonify({'success': False, 'message': '学号和姓名不能为空'})
    if not student_no.isdigit():
        return jsonify({'success': False, 'message': '学号只能包含数字'})
    if len(student_no) > 20:
        return jsonify({'success': False, 'message': '学号不能超过 20 位'})
    if len(name) > 50:
        return jsonify({'success': False, 'message': '姓名不能超过 50 个字符'})

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO student (student_no, name, gender, class_name, major, enroll_year) VALUES (%s, %s, %s, %s, %s, %s)",
            (student_no, name, data['gender'], data['class_name'], data['major'], data['enroll_year'])
        )
        conn.commit()
    except pymysql.err.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': '学号 ' + student_no + ' 已存在，请使用其他学号'})
    except pymysql.err.DataError:
        conn.close()
        return jsonify({'success': False, 'message': '输入内容过长，请检查各字段长度'})
    conn.close()
    return jsonify({'success': True})


@app.route('/api/students/<int:id>', methods=['PUT'])
@login_required
def api_update_student(id):
    data = request.get_json()
    student_no = str(data.get('student_no', '')).strip()
    name = str(data.get('name', '')).strip()

    if not student_no or not name:
        return jsonify({'success': False, 'message': '学号和姓名不能为空'})
    if not student_no.isdigit():
        return jsonify({'success': False, 'message': '学号只能包含数字'})
    if len(student_no) > 20:
        return jsonify({'success': False, 'message': '学号不能超过 20 位'})
    if len(name) > 50:
        return jsonify({'success': False, 'message': '姓名不能超过 50 个字符'})

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE student SET student_no=%s, name=%s, gender=%s, class_name=%s, major=%s, enroll_year=%s WHERE id=%s",
            (student_no, name, data['gender'], data['class_name'], data['major'], data['enroll_year'], id)
        )
        conn.commit()
    except pymysql.err.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': '学号 ' + student_no + ' 已存在，请使用其他学号'})
    except pymysql.err.DataError:
        conn.close()
        return jsonify({'success': False, 'message': '输入内容过长，请检查各字段长度'})
    conn.close()
    return jsonify({'success': True})


@app.route('/api/students/<int:id>', methods=['DELETE'])
@login_required
def api_delete_student(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM score WHERE student_id = %s", (id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return jsonify({'success': False, 'message': '该学生已有成绩记录，无法删除'})
    cursor.execute("DELETE FROM student WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== 专业管理 ====================

@app.route('/api/majors')
@login_required
def api_majors():
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM major ORDER BY id")
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


@app.route('/api/majors', methods=['POST'])
@login_required
def api_add_major():
    data = request.get_json()
    major_name = str(data.get('major_name', '')).strip()
    department = str(data.get('department', '') or '').strip()
    if not major_name:
        return jsonify({'success': False, 'message': '专业名称不能为空'})
    if len(major_name) > 100 or len(department) > 100:
        return jsonify({'success': False, 'message': '输入内容过长，最多 100 个字符'})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO major (major_name, department) VALUES (%s, %s)", (major_name, department))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/majors/<int:id>', methods=['PUT'])
@login_required
def api_update_major(id):
    data = request.get_json()
    major_name = str(data.get('major_name', '')).strip()
    department = str(data.get('department', '') or '').strip()
    if not major_name:
        return jsonify({'success': False, 'message': '专业名称不能为空'})
    if len(major_name) > 100 or len(department) > 100:
        return jsonify({'success': False, 'message': '输入内容过长，最多 100 个字符'})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE major SET major_name=%s, department=%s WHERE id=%s", (major_name, department, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/majors/<int:id>', methods=['DELETE'])
@login_required
def api_delete_major(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM class WHERE major_id = %s", (id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return jsonify({'success': False, 'message': '该专业下还有班级，无法删除'})
    cursor.execute("DELETE FROM major WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== 班级管理 ====================

@app.route('/api/classes')
@login_required
def api_classes():
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT c.id, c.class_name, c.major_id, c.grade, m.major_name
        FROM class c
        LEFT JOIN major m ON c.major_id = m.id
        ORDER BY c.id
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


@app.route('/api/classes', methods=['POST'])
@login_required
def api_add_class():
    data = request.get_json()
    class_name = str(data.get('class_name', '')).strip()
    grade = str(data.get('grade', '') or '').strip()
    if not class_name:
        return jsonify({'success': False, 'message': '班级名称不能为空'})
    if len(class_name) > 100:
        return jsonify({'success': False, 'message': '班级名称不能超过 100 个字符'})
    if len(grade) > 20:
        return jsonify({'success': False, 'message': '年级不能超过 20 个字符'})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO class (class_name, major_id, grade) VALUES (%s, %s, %s)",
                   (class_name, data['major_id'], grade))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/classes/<int:id>', methods=['PUT'])
@login_required
def api_update_class(id):
    data = request.get_json()
    class_name = str(data.get('class_name', '')).strip()
    grade = str(data.get('grade', '') or '').strip()
    if not class_name:
        return jsonify({'success': False, 'message': '班级名称不能为空'})
    if len(class_name) > 100:
        return jsonify({'success': False, 'message': '班级名称不能超过 100 个字符'})
    if len(grade) > 20:
        return jsonify({'success': False, 'message': '年级不能超过 20 个字符'})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE class SET class_name=%s, major_id=%s, grade=%s WHERE id=%s",
                   (class_name, data['major_id'], grade, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/classes/<int:id>', methods=['DELETE'])
@login_required
def api_delete_class(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM class WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== 课程管理 ====================

@app.route('/api/courses')
@login_required
def api_courses():
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM course ORDER BY id")
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


@app.route('/api/courses', methods=['POST'])
@login_required
def api_add_course():
    data = request.get_json()
    course_name = str(data.get('course_name', '')).strip()
    if not course_name:
        return jsonify({'success': False, 'message': '课程名称不能为空'})
    if len(course_name) > 100:
        return jsonify({'success': False, 'message': '课程名称不能超过 100 个字符'})
    if data.get('credit') is None or data['credit'] < 0 or data['credit'] > 20:
        return jsonify({'success': False, 'message': '学分必须在 0 到 20 之间'})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO course (course_name, credit) VALUES (%s, %s)", (course_name, data['credit']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/courses/<int:id>', methods=['PUT'])
@login_required
def api_update_course(id):
    data = request.get_json()
    course_name = str(data.get('course_name', '')).strip()
    if not course_name:
        return jsonify({'success': False, 'message': '课程名称不能为空'})
    if len(course_name) > 100:
        return jsonify({'success': False, 'message': '课程名称不能超过 100 个字符'})
    if data.get('credit') is None or data['credit'] < 0 or data['credit'] > 20:
        return jsonify({'success': False, 'message': '学分必须在 0 到 20 之间'})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE course SET course_name=%s, credit=%s WHERE id=%s", (course_name, data['credit'], id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/courses/<int:id>', methods=['DELETE'])
@login_required
def api_delete_course(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM score WHERE course_id = %s", (id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return jsonify({'success': False, 'message': '该课程下已有成绩记录，无法删除'})
    cursor.execute("DELETE FROM course WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== 成绩管理 ====================

@app.route('/api/scores')
@login_required
def api_scores():
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT
            sc.id, sc.student_id, sc.course_id, sc.score, sc.term,
            st.name AS student_name, st.student_no, st.class_name,
            c.course_name, c.credit
        FROM score sc
        INNER JOIN student st ON sc.student_id = st.id
        INNER JOIN course c ON sc.course_id = c.id
        ORDER BY st.student_no, c.id
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)


@app.route('/api/scores', methods=['POST'])
@login_required
def api_add_score():
    data = request.get_json()
    if not data.get('student_id') or not data.get('course_id'):
        return jsonify({'success': False, 'message': '请选择学生和课程'})
    if data.get('score') is None or data['score'] < 0 or data['score'] > 100:
        return jsonify({'success': False, 'message': '分数必须在 0 到 100 之间'})
    term = str(data.get('term', '') or '').strip()
    if len(term) > 20:
        return jsonify({'success': False, 'message': '学期不能超过 20 个字符'})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO score (student_id, course_id, score, term) VALUES (%s, %s, %s, %s)",
                   (data['student_id'], data['course_id'], data['score'], term))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/scores/<int:id>', methods=['PUT'])
@login_required
def api_update_score(id):
    data = request.get_json()
    if not data.get('student_id') or not data.get('course_id'):
        return jsonify({'success': False, 'message': '请选择学生和课程'})
    if data.get('score') is None or data['score'] < 0 or data['score'] > 100:
        return jsonify({'success': False, 'message': '分数必须在 0 到 100 之间'})
    term = str(data.get('term', '') or '').strip()
    if len(term) > 20:
        return jsonify({'success': False, 'message': '学期不能超过 20 个字符'})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE score SET student_id=%s, course_id=%s, score=%s, term=%s WHERE id=%s",
                   (data['student_id'], data['course_id'], data['score'], term, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/scores/<int:id>', methods=['DELETE'])
@login_required
def api_delete_score(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM score WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== 统计分析 ====================

@app.route('/api/statistics')
@login_required
def api_statistics():
    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT COUNT(*) AS total FROM student")
    total = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM major")
    major_count = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM class")
    class_count = cursor.fetchone()['total']

    cursor.execute("SELECT class_name, COUNT(*) AS count FROM student GROUP BY class_name ORDER BY class_name")
    by_class = cursor.fetchall()

    cursor.execute("SELECT major, COUNT(*) AS count FROM student GROUP BY major ORDER BY count DESC")
    by_major = cursor.fetchall()

    cursor.execute("SELECT gender, COUNT(*) AS count FROM student GROUP BY gender")
    by_gender = cursor.fetchall()

    cursor.execute("SELECT enroll_year, COUNT(*) AS count FROM student GROUP BY enroll_year ORDER BY enroll_year")
    by_year = cursor.fetchall()

    conn.close()
    return jsonify({
        'total': total,
        'major_count': major_count,
        'class_count': class_count,
        'by_class': by_class,
        'by_major': by_major,
        'by_gender': by_gender,
        'by_year': by_year
    })


if __name__ == '__main__':
    app.run(debug=True)