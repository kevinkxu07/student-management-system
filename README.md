# Student Information Management System

A full-stack web application for managing student records, built during a software engineering internship at Jiangsu Xinshiyun Technology (Nanjing, China). The system handles student information, academic programs, classes, courses, and grades, with search and statistical visualization.

The interface is in Chinese, as it was built to a Chinese-language requirements specification.

## Features

| Module | Description |
|---|---|
| Authentication | Admin login with hashed passwords, session management, 30-minute inactivity timeout |
| Student Management | Full CRUD with multi-field fuzzy search |
| Major Management | CRUD with referential integrity checks before deletion |
| Class Management | CRUD with foreign key relationship to majors |
| Course Management | CRUD with referential integrity checks before deletion |
| Grade Management | Score entry and maintenance using three-table JOIN queries, color-coded by grade range |
| Statistics | Summary cards plus distribution charts by class, major, gender, and enrollment year |

## Tech Stack

- **Backend:** Python 3 + Flask
- **Database:** MySQL 8 (utf8mb4 / InnoDB)
- **Database driver:** PyMySQL
- **Frontend:** Vue 3 + Ant Design Vue 4 (loaded via CDN, no build step)
- **Charts:** Chart.js
- **Password hashing:** Werkzeug (salted hash)

The frontend uses CDN imports rather than npm and a bundler. This keeps deployment simple and requires no Node.js environment. The trade-off is that components can't be split into single-file modules, and Ant Design Vue's CDN build required manually resolving seven dayjs plugin dependencies.

## Requirements

- Python 3.9+
- MySQL 8.0+

## Setup

**1. Create the database**

```sql
CREATE DATABASE student_system CHARACTER SET utf8mb4;
```

**2. Import the schema**

```bash
mysql -u root -p student_system < schema.sql
```

**3. Install Python dependencies**

```bash
pip3 install -r requirements.txt
```

**4. Configure the database connection**

In `app.py`, update the `get_db()` function with your local MySQL password:

```python
def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='your_mysql_password',   # ← change this
        database='student_system',
        charset='utf8mb4'
    )
```

**5. Run the server**

```bash
python3 app.py
```

**6. Initialize the admin account**

Visit `http://127.0.0.1:5000/api/init-admin` once in a browser.

**7. Open the application**

```
http://127.0.0.1:5000/vue
```

Default credentials: `admin` / `admin123`

## Project Structure

```
.
├── app.py                  Flask backend, all API routes
├── schema.sql              Database schema
├── requirements.txt        Python dependencies
├── README.md
└── templates/
    ├── vue_students.html   Main SPA interface
    ├── students.html       Earlier Jinja version (retained)
    └── add.html            Earlier Jinja version (retained)
```

## Database Schema

Six tables:

| Table | Purpose |
|---|---|
| `admin` | Administrator accounts, passwords stored as salted hashes |
| `major` | Academic programs |
| `class` | Classes, foreign key to `major` |
| `student` | Student records |
| `course` | Courses |
| `score` | Grades, foreign keys to `student` and `course` |

**Relationships:** one major has many classes; students and courses form a many-to-many relationship resolved through the `score` junction table.

## Design Notes

**Normalization.** Majors and classes were initially stored as free-text fields on the student table. This caused a data integrity problem: `SELECT DISTINCT` returned two entries for the same major because one record contained a full-width space (U+3000) from Chinese IME input — invisible on screen, and not removable by `TRIM()`, which only handles ASCII whitespace. The fix was to extract these into their own tables and change the student form to dropdown selection, eliminating the class of problem at the input layer rather than cleaning it up afterward.

**Validation at two layers.** All input is validated in both the frontend and the backend. Frontend validation is for user experience; backend validation is for correctness, since the frontend can be bypassed entirely by constructing requests directly.

**Error handling around database constraints.** Constraints like `UNIQUE` on student numbers correctly reject bad data, but an uncaught `IntegrityError` produces a hung modal with no feedback. Every constraint has a corresponding error path that returns a readable message.

## Security

Implemented:

- All SQL queries use parameterized statements
- Passwords stored as salted hashes, never plaintext
- All data endpoints protected by a `@login_required` decorator
- Sessions expire after 30 minutes of inactivity
- Input validation on both frontend and backend

## Known Limitations

- Database credentials and `secret_key` are hardcoded; production deployment should use environment variables
- No HTTPS — login credentials are transmitted in plaintext, suitable only for local development
- Single administrator role, no permission tiers
- The `student` table still stores class and major as text rather than foreign keys
- Search is performed client-side; large datasets would require server-side queries with pagination
- The `/api/init-admin` endpoint should be removed after initialization
- The default password is weak and intended only for local testing

## Context

Built over approximately two weeks with no prior web development experience. Development was AI-assisted; the accompanying project report documents where AI-generated code required correction — including missing CDN dependencies, duplicate route definitions, and SQL that was syntactically correct but failed against real data.
