import os
import sys
import re
import sqlite3
import logging
from werkzeug.security import generate_password_hash

# Add parent directory to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import Config
from database.connection import try_mysql_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('exampro.init_db')

SQL_FILE_PATH = os.path.join(BASE_DIR, 'database.sql')
SQLITE_DB_PATH = Config.SQLITE_DB_PATH

def init_mysql():
    """Initializes MySQL database from database.sql file."""
    logger.info(f"Connecting to MySQL server at {Config.DB_HOST}:{Config.DB_PORT}...")
    
    # First connect without specifying database to create database if not exists
    conn = None
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            autocommit=True
        )
    except Exception as e:
        try:
            import pymysql
            conn = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                autocommit=True
            )
        except Exception as e2:
            logger.warning(f"Could not connect to MySQL server: {e2}")
            return False

    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    cursor.execute(f"USE `{Config.DB_NAME}`;")
    
    with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Split commands by semicolon while respecting comments and blocks
    commands = []
    current_cmd = []
    for line in sql_content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith('--') or trimmed.startswith('/*'):
            continue
        current_cmd.append(line)
        if trimmed.endswith(';'):
            cmd_str = '\n'.join(current_cmd)
            commands.append(cmd_str)
            current_cmd = []

    logger.info(f"Executing {len(commands)} SQL statements into MySQL database '{Config.DB_NAME}'...")
    for cmd in commands:
        if cmd.strip():
            try:
                cursor.execute(cmd)
            except Exception as ex:
                logger.debug(f"Statement notice/warning: {ex}")

    cursor.close()
    conn.close()
    logger.info("MySQL database initialization completed successfully!")
    return True

def init_sqlite():
    """Initializes local SQLite database with the full ExamPro schema and rich seed data."""
    logger.info(f"Initializing SQLite fallback database at: {SQLITE_DB_PATH}")
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    schema_statements = [
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
            full_name TEXT NOT NULL,
            phone TEXT,
            avatar_url TEXT DEFAULT '/static/images/default-avatar.png',
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'disabled', 'pending')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            student_id TEXT NOT NULL UNIQUE,
            course TEXT NOT NULL DEFAULT 'B.Tech Computer Science',
            college TEXT NOT NULL DEFAULT 'Institute of Technology & Science',
            enrollment_year INTEGER DEFAULT 2024,
            semester INTEGER DEFAULT 4,
            cgpa REAL DEFAULT 8.50,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            employee_id TEXT NOT NULL UNIQUE,
            department TEXT NOT NULL DEFAULT 'Computer Science & Engineering',
            designation TEXT NOT NULL DEFAULT 'Associate Professor',
            assigned_subjects TEXT,
            qualification TEXT DEFAULT 'Ph.D. in Computer Science',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            admin_code TEXT NOT NULL UNIQUE,
            department TEXT NOT NULL DEFAULT 'Examination Controller Office',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL UNIQUE,
            course_name TEXT NOT NULL,
            department TEXT NOT NULL,
            duration_years INTEGER DEFAULT 4,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );""",
        """CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            subject_code TEXT NOT NULL UNIQUE,
            subject_name TEXT NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
        );""",
        """CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            exam_code TEXT NOT NULL UNIQUE,
            subject_id INTEGER NOT NULL,
            created_by INTEGER NOT NULL,
            description TEXT,
            instructions TEXT,
            duration_minutes INTEGER NOT NULL DEFAULT 60,
            total_marks REAL NOT NULL DEFAULT 100.0,
            passing_percentage REAL NOT NULL DEFAULT 40.0,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'published', 'active', 'completed', 'archived')),
            randomize_questions INTEGER DEFAULT 1,
            randomize_options INTEGER DEFAULT 1,
            negative_marking INTEGER DEFAULT 0,
            negative_mark_value REAL DEFAULT 0.25,
            max_attempts INTEGER DEFAULT 1,
            result_release_mode TEXT DEFAULT 'immediate',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            topic TEXT DEFAULT 'General',
            question_text TEXT NOT NULL,
            question_type TEXT NOT NULL DEFAULT 'single_choice',
            difficulty TEXT DEFAULT 'medium' CHECK(difficulty IN ('easy', 'medium', 'hard')),
            marks REAL NOT NULL DEFAULT 1.0,
            negative_marks REAL NOT NULL DEFAULT 0.0,
            explanation TEXT,
            image_url TEXT,
            created_by INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS question_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            option_text TEXT NOT NULL,
            is_correct INTEGER NOT NULL DEFAULT 0,
            option_order INTEGER DEFAULT 1,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS exam_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            marks REAL NOT NULL DEFAULT 1.0,
            negative_marks REAL NOT NULL DEFAULT 0.0,
            question_order INTEGER DEFAULT 1,
            FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
            UNIQUE(exam_id, question_id)
        );""",
        """CREATE TABLE IF NOT EXISTS exam_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            attempt_number INTEGER DEFAULT 1,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            submit_time DATETIME,
            time_spent_seconds INTEGER DEFAULT 0,
            status TEXT DEFAULT 'in_progress',
            total_score REAL DEFAULT 0.0,
            percentage REAL DEFAULT 0.0,
            passed INTEGER DEFAULT 0,
            ip_address TEXT,
            browser_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            selected_option_ids TEXT,
            text_answer TEXT,
            is_marked_for_review INTEGER DEFAULT 0,
            is_visited INTEGER DEFAULT 0,
            is_answered INTEGER DEFAULT 0,
            is_correct INTEGER,
            marks_awarded REAL DEFAULT 0.0,
            time_spent_seconds INTEGER DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
            UNIQUE(attempt_id, question_id)
        );""",
        """CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL UNIQUE,
            exam_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            score REAL NOT NULL DEFAULT 0.0,
            total_marks REAL NOT NULL DEFAULT 100.0,
            percentage REAL NOT NULL DEFAULT 0.0,
            grade TEXT NOT NULL DEFAULT 'F',
            status TEXT NOT NULL DEFAULT 'fail',
            correct_count INTEGER DEFAULT 0,
            incorrect_count INTEGER DEFAULT 0,
            skipped_count INTEGER DEFAULT 0,
            accuracy REAL DEFAULT 0.0,
            time_taken_seconds INTEGER DEFAULT 0,
            feedback TEXT,
            published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE,
            FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER NOT NULL UNIQUE,
            student_id INTEGER NOT NULL,
            exam_id INTEGER NOT NULL,
            certificate_code TEXT NOT NULL UNIQUE,
            issue_date DATE NOT NULL,
            grade TEXT NOT NULL,
            percentage REAL NOT NULL,
            file_path TEXT,
            is_valid INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (result_id) REFERENCES results(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            link TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );""",
        """CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER,
            student_id INTEGER NOT NULL,
            exam_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            details TEXT,
            severity TEXT DEFAULT 'medium',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE SET NULL,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
        );"""
    ]

    for stmt in schema_statements:
        cursor.execute(stmt)

    # Check if seed data exists
    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        logger.info("Seeding initial data into SQLite database...")
        # Hash passwords
        admin_hash = generate_password_hash('Admin@123')
        teacher_hash = generate_password_hash('Teacher@123')
        student_hash = generate_password_hash('Student@123')

        # Insert users
        users_data = [
            (1, 'admin', 'admin@exampro.com', admin_hash, 'admin', 'Dr. Sarah Jenkins', '+1 (555) 019-2834', '/static/images/avatars/admin.png', 'active'),
            (2, 'teacher', 'teacher@exampro.com', teacher_hash, 'teacher', 'Prof. Marcus Vance', '+1 (555) 482-9102', '/static/images/avatars/teacher.png', 'active'),
            (3, 'student', 'student@exampro.com', student_hash, 'student', 'Aman Sharma', '+91 98765 43210', '/static/images/avatars/student1.png', 'active'),
            (4, 'priya', 'priya@exampro.com', student_hash, 'student', 'Priya Patel', '+91 98123 45678', '/static/images/avatars/student2.png', 'active'),
            (5, 'rahul', 'rahul@exampro.com', student_hash, 'student', 'Rahul Verma', '+91 98987 65432', '/static/images/avatars/student3.png', 'active')
        ]
        cursor.executemany("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)", users_data)

        # Profiles
        cursor.execute("INSERT INTO admins (id, user_id, admin_code, department) VALUES (1, 1, 'ADM-001', 'Office of the Controller of Examinations');")
        cursor.execute("INSERT INTO teachers (id, user_id, employee_id, department, designation, assigned_subjects, qualification) VALUES (1, 2, 'TCH-101', 'Computer Science & Engineering', 'Head of Department', 'Python Programming, Database Systems', 'Ph.D. in Computer Science');")
        cursor.executemany("INSERT INTO students (id, user_id, student_id, course, college, enrollment_year, semester, cgpa) VALUES (?,?,?,?,?,?,?,?)", [
            (1, 3, 'STU-1001', 'B.Tech Computer Science & Engineering', 'Apex Institute of Technology', 2023, 6, 8.85),
            (2, 4, 'STU-1002', 'B.Tech Information Technology', 'Apex Institute of Technology', 2023, 6, 9.10),
            (3, 5, 'STU-1003', 'B.Tech Artificial Intelligence', 'Apex Institute of Technology', 2024, 4, 8.40)
        ])

        # Courses & Subjects
        cursor.executemany("INSERT INTO courses (id, course_code, course_name, department, duration_years, description) VALUES (?,?,?,?,?,?)", [
            (1, 'CSE-BTECH', 'B.Tech Computer Science & Engineering', 'School of Computing', 4, 'Comprehensive study of computing paradigms, algorithms, and systems.'),
            (2, 'IT-BTECH', 'B.Tech Information Technology', 'School of Computing', 4, 'Applied computing, networked applications, security, and cloud architectures.'),
            (3, 'AI-BTECH', 'B.Tech Artificial Intelligence & Machine Learning', 'School of Computing', 4, 'Foundations of intelligent machines, deep learning, NLP, and computer vision.')
        ])

        cursor.executemany("INSERT INTO subjects (id, course_id, subject_code, subject_name, description) VALUES (?,?,?,?,?)", [
            (1, 1, 'CS301', 'Python Programming & Data Structures', 'Core Python semantics, OOP, generators, decorators, and data structure implementations.'),
            (2, 1, 'CS302', 'Database Management Systems', 'Relational design, normalization, ACID properties, transaction processing, and SQL optimization.'),
            (3, 1, 'CS303', 'Computer Networks & Distributed Systems', 'OSI/TCP-IP models, socket programming, routing protocols, flow and congestion control.'),
            (4, 2, 'IT204', 'Modern Full-Stack Web Development', 'HTML5, CSS3, JavaScript, DOM architecture, RESTful APIs, and responsive design systems.')
        ])

        # Exams
        cursor.executemany("INSERT INTO exams (id, title, exam_code, subject_id, created_by, description, instructions, duration_minutes, total_marks, passing_percentage, start_time, end_time, status, randomize_questions, randomize_options, negative_marking, negative_mark_value, max_attempts, result_release_mode) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
            (1, 'Python Core & Advanced Assessment 2026', 'EXAM-PY-2026', 1, 2, 'Comprehensive examination evaluating Python memory management, list comprehensions, decorators, and functional tools.', '1. Contains 8 multi-format questions.\n2. Do not switch tabs or exit fullscreen.\n3. Negative marking is -0.5 for wrong answers.\n4. Answers auto-save in real time.', 45, 16.0, 40.0, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 'active', 1, 1, 1, 0.50, 3, 'immediate'),
            (2, 'Database Management Systems Mid-Term Exam', 'EXAM-DBMS-MID', 2, 2, 'Mid-term evaluation covering ER Modeling, 3NF/BCNF normalization, and ACID transaction isolation levels.', '1. Attempt all questions.\n2. Keep your screen active.\n3. Timer auto-submits upon completion.', 60, 20.0, 50.0, '2026-02-01 00:00:00', '2026-12-31 23:59:59', 'active', 1, 1, 0, 0.00, 2, 'immediate'),
            (3, 'Computer Networks & Security Assessment', 'EXAM-NET-SEC', 3, 2, 'Evaluation of TCP/IP protocol suite, subnetting, symmetric vs asymmetric encryption, and firewalls.', '1. Fullscreen mode is strictly enforced.\n2. Question palette shows unanswered items in red.', 50, 20.0, 45.0, '2026-01-15 00:00:00', '2026-12-31 23:59:59', 'active', 1, 0, 1, 0.50, 1, 'immediate'),
            (4, 'Web Development & Modern JavaScript Challenge', 'EXAM-WEB-DEV', 4, 1, 'Practical quiz testing modern DOM, event propagation, async/await, and CSS grid layout models.', '1. Test your JavaScript and CSS knowledge.', 30, 15.0, 40.0, '2026-03-01 00:00:00', '2026-12-31 23:59:59', 'active', 0, 0, 0, 0.00, 5, 'immediate')
        ])

        # Questions for Python (Exam 1)
        cursor.executemany("INSERT INTO questions (id, subject_id, topic, question_text, question_type, difficulty, marks, negative_marks, explanation, created_by) VALUES (?,?,?,?,?,?,?,?,?,?)", [
            (1, 1, 'Data Types', 'What will be the output of the following Python expression: `bool([]) + bool([0])`?', 'single_choice', 'easy', 2.0, 0.5, 'An empty list `[]` evaluates to False (0), whereas a non-empty list `[0]` evaluates to True (1). 0 + 1 = 1.', 2),
            (2, 1, 'Memory Management', 'In Python, which built-in function returns the unique identity (memory address) of an object?', 'single_choice', 'easy', 2.0, 0.5, 'The id() function returns the identity of the object, which is guaranteed to be unique and constant for this object during its lifetime.', 2),
            (3, 1, 'Data Structures', 'Which of the following built-in collection types in Python are mutable? (Select all that apply)', 'multiple_choice', 'medium', 2.0, 0.5, 'Lists, dictionaries, and sets are mutable. Tuples and frozensets are immutable.', 2),
            (4, 1, 'Language Semantics', 'Python uses GIL (Global Interpreter Lock) to synchronize thread execution in CPython.', 'true_false', 'easy', 2.0, 0.0, 'CPython employs the Global Interpreter Lock (GIL) to protect concurrent access to Python objects across threads.', 2),
            (5, 1, 'Functions', 'What keyword is used in Python to create an anonymous function?', 'fill_blank', 'easy', 2.0, 0.0, 'The `lambda` keyword is used to create small, anonymous inline functions in Python.', 2),
            (6, 1, 'OOP', 'Explain the purpose of the `__init__` method in Python classes.', 'descriptive', 'medium', 2.0, 0.0, '`__init__` is the constructor method in Python. It is automatically called when a new instance of a class is created to initialize instance attributes.', 2),
            (7, 1, 'Generators', 'What keyword pauses function execution and returns a value to the caller in a Python generator?', 'single_choice', 'medium', 2.0, 0.5, 'The `yield` statement is used in generators to yield a value and suspend execution state.', 2),
            (8, 1, 'Decorators', 'A Python decorator is syntactic sugar for passing a function as an argument to another callable and returning a replacement.', 'true_false', 'medium', 2.0, 0.0, 'True: `@dec` preceding `def func():` is equivalent to `func = dec(func)`.', 2),
            (9, 2, 'ACID Properties', 'Which ACID property guarantees that transactions are processed reliably and completely, or not at all?', 'single_choice', 'easy', 2.5, 0.0, 'Atomicity ensures that all statements in a transaction are executed as a single indivisible unit.', 2),
            (10, 2, 'Normalization', 'A relation is in Boyce-Codd Normal Form (BCNF) if and only if for every non-trivial functional dependency X -> Y, X is a superkey.', 'true_false', 'medium', 2.5, 0.0, 'By definition, BCNF requires the determinant X to be a super key for every non-trivial dependency.', 2),
            (11, 2, 'SQL & Keys', 'Which SQL constraint uniquely identifies each record in a database table without accepting NULL values?', 'single_choice', 'easy', 2.5, 0.0, 'A PRIMARY KEY uniquely identifies rows and never accepts NULL values.', 2),
            (12, 2, 'Joins', 'Which join type returns all rows from the left table, and matching rows from the right table, filling missing right values with NULL?', 'single_choice', 'easy', 2.5, 0.0, 'LEFT OUTER JOIN (or LEFT JOIN) keeps all records from the left relation.', 2)
        ])

        # Question Options
        cursor.executemany("INSERT INTO question_options (id, question_id, option_text, is_correct, option_order) VALUES (?,?,?,?,?)", [
            (1, 1, '0', 0, 1), (2, 1, '1', 1, 2), (3, 1, '2', 0, 3), (4, 1, 'TypeError', 0, 4),
            (5, 2, 'id()', 1, 1), (6, 2, 'ref()', 0, 2), (7, 2, 'memory()', 0, 3), (8, 2, 'address()', 0, 4),
            (9, 3, 'List', 1, 1), (10, 3, 'Tuple', 0, 2), (11, 3, 'Dictionary', 1, 3), (12, 3, 'Set', 1, 4),
            (13, 4, 'True', 1, 1), (14, 4, 'False', 0, 2),
            (15, 5, 'lambda', 1, 1),
            (16, 6, 'Constructor/initializer method that assigns initial attributes to object instances upon instantiation.', 1, 1),
            (17, 7, 'return', 0, 1), (18, 7, 'yield', 1, 2), (19, 7, 'pause', 0, 3), (20, 7, 'produce', 0, 4),
            (21, 8, 'True', 1, 1), (22, 8, 'False', 0, 2),
            (23, 9, 'Atomicity', 1, 1), (24, 9, 'Consistency', 0, 2), (25, 9, 'Isolation', 0, 3), (26, 9, 'Durability', 0, 4),
            (27, 10, 'True', 1, 1), (28, 10, 'False', 0, 2),
            (29, 11, 'PRIMARY KEY', 1, 1), (30, 11, 'UNIQUE', 0, 2), (31, 11, 'FOREIGN KEY', 0, 3), (32, 11, 'CHECK', 0, 4),
            (33, 12, 'LEFT JOIN', 1, 1), (34, 12, 'RIGHT JOIN', 0, 2), (35, 12, 'INNER JOIN', 0, 3), (36, 12, 'FULL JOIN', 0, 4)
        ])

        # Exam Questions
        cursor.executemany("INSERT INTO exam_questions (exam_id, question_id, marks, negative_marks, question_order) VALUES (?,?,?,?,?)", [
            (1, 1, 2.0, 0.5, 1), (1, 2, 2.0, 0.5, 2), (1, 3, 2.0, 0.5, 3), (1, 4, 2.0, 0.0, 4),
            (1, 5, 2.0, 0.0, 5), (1, 6, 2.0, 0.0, 6), (1, 7, 2.0, 0.5, 7), (1, 8, 2.0, 0.0, 8),
            (2, 9, 2.5, 0.0, 1), (2, 10, 2.5, 0.0, 2), (2, 11, 2.5, 0.0, 3), (2, 12, 2.5, 0.0, 4)
        ])

        # Completed attempt & result for Aman Sharma (student id 1)
        cursor.execute("INSERT INTO exam_attempts (id, exam_id, student_id, attempt_number, start_time, submit_time, time_spent_seconds, status, total_score, percentage, passed, ip_address, browser_agent) VALUES (1, 1, 1, 1, '2026-03-10 10:00:00', '2026-03-10 10:28:45', 1725, 'submitted', 14.0, 87.5, 1, '127.0.0.1', 'Chrome/120.0');")
        
        cursor.executemany("INSERT INTO answers (attempt_id, question_id, selected_option_ids, text_answer, is_marked_for_review, is_visited, is_answered, is_correct, marks_awarded, time_spent_seconds) VALUES (?,?,?,?,?,?,?,?,?,?)", [
            (1, 1, '2', None, 0, 1, 1, 1, 2.0, 120),
            (1, 2, '5', None, 0, 1, 1, 1, 2.0, 95),
            (1, 3, '9,11,12', None, 0, 1, 1, 1, 2.0, 210),
            (1, 4, '13', None, 0, 1, 1, 1, 2.0, 80),
            (1, 5, None, 'lambda', 0, 1, 1, 1, 2.0, 110),
            (1, 6, None, 'Initializes an object instance with attributes.', 0, 1, 1, 1, 2.0, 350),
            (1, 7, '18', None, 0, 1, 1, 1, 2.0, 140),
            (1, 8, '22', None, 0, 1, 1, 0, 0.0, 90)
        ])

        cursor.execute("INSERT INTO results (id, attempt_id, exam_id, student_id, score, total_marks, percentage, grade, status, correct_count, incorrect_count, skipped_count, accuracy, time_taken_seconds, feedback, published_at) VALUES (1, 1, 1, 1, 14.0, 16.0, 87.5, 'A+', 'pass', 7, 1, 0, 87.5, 1725, 'Outstanding grasp of Python syntax, collections, and functional programming!', '2026-03-10 10:28:46');")
        cursor.execute("INSERT INTO certificates (id, result_id, student_id, exam_id, certificate_code, issue_date, grade, percentage, file_path, is_valid) VALUES (1, 1, 1, 1, 'EXAMPRO-CERT-PY-882941', '2026-03-10', 'A+', 87.5, '/static/certificates/cert_1.pdf', 1);")

        cursor.executemany("INSERT INTO notifications (id, user_id, title, message, type, is_read, link) VALUES (?,?,?,?,?,?,?)", [
            (1, 3, 'Exam Completed Successfully', 'Your attempt for Python Core & Advanced Assessment has been evaluated with a score of 87.5%.', 'success', 1, '/student/results/1'),
            (2, 3, 'Certificate Generated', 'Your certificate of excellence for Python Core & Advanced Assessment is now ready for download.', 'info', 0, '/student/certificates'),
            (3, 3, 'Upcoming Exam Notice', 'Database Management Systems Mid-Term is scheduled. Verify your device readiness.', 'exam', 0, '/student/exams'),
            (4, 1, 'New Student Registration', 'Student Rahul Verma has registered with ID STU-1003.', 'info', 0, '/admin/students'),
            (5, 2, 'Exam Attempt Submitted', 'Aman Sharma submitted Python Core & Advanced Assessment.', 'info', 1, '/teacher/results')
        ])

        cursor.executemany("INSERT INTO security_logs (id, attempt_id, student_id, exam_id, event_type, details, severity, created_at) VALUES (?,?,?,?,?,?,?,?)", [
            (1, 1, 1, 1, 'tab_switch', 'User switched browser tab or focus lost for 4 seconds.', 'low', '2026-03-10 10:14:22'),
            (2, 1, 1, 1, 'copy_paste', 'Blocked clipboard copy attempt on question 3.', 'medium', '2026-03-10 10:18:05')
        ])

    conn.commit()
    conn.close()
    logger.info("SQLite database initialized and populated with seed data successfully!")
    return True

def initialize_database(silent_if_exists=True):
    """
    Master database initialization function.
    Attempts MySQL first; falls back to SQLite.
    """
    # Check if database already initialized
    try:
        from database.connection import query_db
        cnt = query_db("SELECT COUNT(*) as cnt FROM users", one=True)
        if cnt and cnt['cnt'] > 0 and silent_if_exists:
            return
    except Exception:
        pass

    logger.info("Starting ExamPro Database Initialization...")
    
    # Check if MySQL is available
    mysql_success = False
    try:
        mysql_success = init_mysql()
    except Exception as e:
        logger.warning(f"MySQL initialization encountered an error: {e}")
        
    if not mysql_success:
        logger.info("MySQL unavailable or credentials not set. Falling back to SQLite for flawless operation.")
        init_sqlite()
    else:
        logger.info("MySQL database initialized successfully.")

if __name__ == '__main__':
    initialize_database()
