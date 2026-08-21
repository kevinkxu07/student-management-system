-- ============================================
-- 1. 建表：major（专业表）
-- ============================================
CREATE TABLE major (
    id INT AUTO_INCREMENT PRIMARY KEY,
    major_name VARCHAR(100) NOT NULL COMMENT '专业名称',
    department VARCHAR(100) COMMENT '所属院系'
);

-- ============================================
-- 2. 建表：class（班级表）
-- major_id 关联 major.id，代表这个班级属于哪个专业
-- ============================================
CREATE TABLE class (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(100) NOT NULL COMMENT '班级名称',
    major_id INT COMMENT '关联的专业id',
    grade VARCHAR(20) COMMENT '年级',
    FOREIGN KEY (major_id) REFERENCES major(id)
);

-- ============================================
-- 3. 从 student.major 中提取去重的专业名称，插入 major 表
-- ============================================
INSERT INTO major (major_name)
SELECT DISTINCT major FROM student
WHERE major IS NOT NULL AND major != '';

-- ============================================
-- 4. 从 student.class_name 中提取去重的班级，插入 class 表
-- 通过 student.major 关联到刚插入的 major.id
-- ============================================
INSERT INTO class (class_name, major_id)
SELECT DISTINCT s.class_name, m.id
FROM student s
JOIN major m ON s.major = m.major_name
WHERE s.class_name IS NOT NULL AND s.class_name != '';
