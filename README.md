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
| `course`