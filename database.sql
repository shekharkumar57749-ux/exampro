-- ========================================================
-- ExamPro - Advanced Examination Management System
-- Database Schema & Comprehensive Seed Data
-- Compatible with MySQL 8.0+
-- ========================================================

CREATE DATABASE IF NOT EXISTS exampro_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE exampro_db;

-- Disable foreign key checks during initialization
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Users Table
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'teacher', 'student') NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(20) DEFAULT NULL,
    avatar_url VARCHAR(255) DEFAULT '/static/images/default-avatar.png',
    status ENUM('active', 'disabled', 'pending') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_email (email),
    INDEX idx_user_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Students Profile Table
DROP TABLE IF EXISTS students;
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    student_id VARCHAR(50) NOT NULL UNIQUE,
    course VARCHAR(100) NOT NULL DEFAULT 'B.Tech Computer Science',
    college VARCHAR(150) NOT NULL DEFAULT 'Institute of Technology & Science',
    enrollment_year INT DEFAULT 2024,
    semester INT DEFAULT 4,
    cgpa DECIMAL(3, 2) DEFAULT 8.50,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_student_code (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Teachers Profile Table
DROP TABLE IF EXISTS teachers;
CREATE TABLE teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    employee_id VARCHAR(50) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL DEFAULT 'Computer Science & Engineering',
    designation VARCHAR(100) NOT NULL DEFAULT 'Associate Professor',
    assigned_subjects TEXT DEFAULT NULL,
    qualification VARCHAR(100) DEFAULT 'Ph.D. in Computer Science',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Admins Profile Table
DROP TABLE IF EXISTS admins;
CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    admin_code VARCHAR(50) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL DEFAULT 'Examination Controller Office',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Courses Table
DROP TABLE IF EXISTS courses;
CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    course_name VARCHAR(150) NOT NULL,
    department VARCHAR(100) NOT NULL,
    duration_years INT DEFAULT 4,
    description TEXT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Subjects Table
DROP TABLE IF EXISTS subjects;
CREATE TABLE subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT DEFAULT NULL,
    subject_code VARCHAR(30) NOT NULL UNIQUE,
    subject_name VARCHAR(150) NOT NULL,
    description TEXT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Exams Table
DROP TABLE IF EXISTS exams;
CREATE TABLE exams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    exam_code VARCHAR(50) NOT NULL UNIQUE,
    subject_id INT NOT NULL,
    created_by INT NOT NULL,
    description TEXT DEFAULT NULL,
    instructions TEXT DEFAULT NULL,
    duration_minutes INT NOT NULL DEFAULT 60,
    total_marks DECIMAL(6, 2) NOT NULL DEFAULT 100.00,
    passing_percentage DECIMAL(5, 2) NOT NULL DEFAULT 40.00,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status ENUM('draft', 'published', 'active', 'completed', 'archived') DEFAULT 'draft',
    randomize_questions BOOLEAN DEFAULT TRUE,
    randomize_options BOOLEAN DEFAULT TRUE,
    negative_marking BOOLEAN DEFAULT FALSE,
    negative_mark_value DECIMAL(4, 2) DEFAULT 0.25,
    max_attempts INT DEFAULT 1,
    result_release_mode ENUM('immediate', 'scheduled', 'manual') DEFAULT 'immediate',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_exam_status (status),
    INDEX idx_exam_dates (start_time, end_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Questions Table
DROP TABLE IF EXISTS questions;
CREATE TABLE questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    topic VARCHAR(100) DEFAULT 'General',
    question_text TEXT NOT NULL,
    question_type ENUM('single_choice', 'multiple_choice', 'true_false', 'fill_blank', 'descriptive', 'image_based') NOT NULL DEFAULT 'single_choice',
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    marks DECIMAL(5, 2) NOT NULL DEFAULT 1.00,
    negative_marks DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    explanation TEXT DEFAULT NULL,
    image_url VARCHAR(255) DEFAULT NULL,
    created_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_question_type (question_type),
    INDEX idx_question_difficulty (difficulty)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Question Options Table
DROP TABLE IF EXISTS question_options;
CREATE TABLE question_options (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    option_order INT DEFAULT 1,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Exam Questions Association Table
DROP TABLE IF EXISTS exam_questions;
CREATE TABLE exam_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    question_id INT NOT NULL,
    marks DECIMAL(5, 2) NOT NULL DEFAULT 1.00,
    negative_marks DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    question_order INT DEFAULT 1,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    UNIQUE KEY uk_exam_question (exam_id, question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. Exam Attempts Table
DROP TABLE IF EXISTS exam_attempts;
CREATE TABLE exam_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    student_id INT NOT NULL,
    attempt_number INT DEFAULT 1,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    submit_time DATETIME DEFAULT NULL,
    time_spent_seconds INT DEFAULT 0,
    status ENUM('in_progress', 'submitted', 'auto_submitted', 'disqualified') DEFAULT 'in_progress',
    total_score DECIMAL(6, 2) DEFAULT 0.00,
    percentage DECIMAL(5, 2) DEFAULT 0.00,
    passed BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(45) DEFAULT NULL,
    browser_agent VARCHAR(255) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    INDEX idx_attempt_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. Student Answers Table
DROP TABLE IF EXISTS answers;
CREATE TABLE answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attempt_id INT NOT NULL,
    question_id INT NOT NULL,
    selected_option_ids TEXT DEFAULT NULL, -- JSON or comma-separated option IDs
    text_answer TEXT DEFAULT NULL,         -- For fill in blank and descriptive
    is_marked_for_review BOOLEAN DEFAULT FALSE,
    is_visited BOOLEAN DEFAULT FALSE,
    is_answered BOOLEAN DEFAULT FALSE,
    is_correct BOOLEAN DEFAULT NULL,
    marks_awarded DECIMAL(5, 2) DEFAULT 0.00,
    time_spent_seconds INT DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    UNIQUE KEY uk_attempt_question (attempt_id, question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 13. Results Table
DROP TABLE IF EXISTS results;
CREATE TABLE results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attempt_id INT NOT NULL UNIQUE,
    exam_id INT NOT NULL,
    student_id INT NOT NULL,
    score DECIMAL(6, 2) NOT NULL DEFAULT 0.00,
    total_marks DECIMAL(6, 2) NOT NULL DEFAULT 100.00,
    percentage DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    grade VARCHAR(5) NOT NULL DEFAULT 'F',
    status ENUM('pass', 'fail') NOT NULL DEFAULT 'fail',
    correct_count INT DEFAULT 0,
    incorrect_count INT DEFAULT 0,
    skipped_count INT DEFAULT 0,
    accuracy DECIMAL(5, 2) DEFAULT 0.00,
    time_taken_seconds INT DEFAULT 0,
    feedback TEXT DEFAULT NULL,
    published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 14. Certificates Table
DROP TABLE IF EXISTS certificates;
CREATE TABLE certificates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    result_id INT NOT NULL UNIQUE,
    student_id INT NOT NULL,
    exam_id INT NOT NULL,
    certificate_code VARCHAR(64) NOT NULL UNIQUE,
    issue_date DATE NOT NULL,
    grade VARCHAR(10) NOT NULL,
    percentage DECIMAL(5, 2) NOT NULL,
    file_path VARCHAR(255) DEFAULT NULL,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (result_id) REFERENCES results(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    INDEX idx_cert_code (certificate_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 15. Notifications Table
DROP TABLE IF EXISTS notifications;
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type ENUM('info', 'warning', 'success', 'exam') DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    link VARCHAR(255) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_notification (user_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 16. Security Logs Table
DROP TABLE IF EXISTS security_logs;
CREATE TABLE security_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attempt_id INT DEFAULT NULL,
    student_id INT NOT NULL,
    exam_id INT NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- 'tab_switch', 'fullscreen_exit', 'copy_paste', 'right_click', 'window_blur'
    details TEXT DEFAULT NULL,
    severity ENUM('low', 'medium', 'high') DEFAULT 'medium',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE SET NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- ========================================================
-- SEED DATA
-- Default Passwords (all hashed using werkzeug.security generate_password_hash):
-- Admin:    Admin@123   (scrypt:32768:8:1$...)
-- Teacher:  Teacher@123 (scrypt:32768:8:1$...)
-- Student:  Student@123 (scrypt:32768:8:1$...)
-- ========================================================

-- Insert Users
INSERT INTO users (id, username, email, password_hash, role, full_name, phone, avatar_url, status) VALUES
(1, 'admin', 'admin@exampro.com', 'scrypt:32768:8:1$K7pGv9zZ3QeL$b6cfcf64f9f7dc8ba3eb85aa5996ff56f3453b76964a2754687d605151ee688ae56d56d787d55f0b5d53a9482fce0a7e08f5d0f11075ffcb3a89196b025e1430', 'admin', 'Dr. Sarah Jenkins', '+1 (555) 019-2834', '/static/images/avatars/admin.png', 'active'),
(2, 'teacher', 'teacher@exampro.com', 'scrypt:32768:8:1$K7pGv9zZ3QeL$b6cfcf64f9f7dc8ba3eb85aa5996ff56f3453b76964a2754687d605151ee688ae56d56d787d55f0b5d53a9482fce0a7e08f5d0f11075ffcb3a89196b025e1430', 'teacher', 'Prof. Marcus Vance', '+1 (555) 482-9102', '/static/images/avatars/teacher.png', 'active'),
(3, 'student', 'student@exampro.com', 'scrypt:32768:8:1$K7pGv9zZ3QeL$b6cfcf64f9f7dc8ba3eb85aa5996ff56f3453b76964a2754687d605151ee688ae56d56d787d55f0b5d53a9482fce0a7e08f5d0f11075ffcb3a89196b025e1430', 'student', 'Aman Sharma', '+91 98765 43210', '/static/images/avatars/student1.png', 'active'),
(4, 'priya', 'priya@exampro.com', 'scrypt:32768:8:1$K7pGv9zZ3QeL$b6cfcf64f9f7dc8ba3eb85aa5996ff56f3453b76964a2754687d605151ee688ae56d56d787d55f0b5d53a9482fce0a7e08f5d0f11075ffcb3a89196b025e1430', 'student', 'Priya Patel', '+91 98123 45678', '/static/images/avatars/student2.png', 'active'),
(5, 'rahul', 'rahul@exampro.com', 'scrypt:32768:8:1$K7pGv9zZ3QeL$b6cfcf64f9f7dc8ba3eb85aa5996ff56f3453b76964a2754687d605151ee688ae56d56d787d55f0b5d53a9482fce0a7e08f5d0f11075ffcb3a89196b025e1430', 'student', 'Rahul Verma', '+91 98987 65432', '/static/images/avatars/student3.png', 'active');

-- Insert Admins Profile
INSERT INTO admins (id, user_id, admin_code, department) VALUES
(1, 1, 'ADM-001', 'Office of the Controller of Examinations');

-- Insert Teachers Profile
INSERT INTO teachers (id, user_id, employee_id, department, designation, assigned_subjects, qualification) VALUES
(1, 2, 'TCH-101', 'Computer Science & Engineering', 'Head of Department', 'Python Programming, Database Systems', 'Ph.D. in Computer Science');

-- Insert Students Profile
INSERT INTO students (id, user_id, student_id, course, college, enrollment_year, semester, cgpa) VALUES
(1, 3, 'STU-1001', 'B.Tech Computer Science & Engineering', 'Apex Institute of Technology', 2023, 6, 8.85),
(2, 4, 'STU-1002', 'B.Tech Information Technology', 'Apex Institute of Technology', 2023, 6, 9.10),
(3, 5, 'STU-1003', 'B.Tech Artificial Intelligence', 'Apex Institute of Technology', 2024, 4, 8.40);

-- Insert Courses
INSERT INTO courses (id, course_code, course_name, department, duration_years, description) VALUES
(1, 'CSE-BTECH', 'B.Tech Computer Science & Engineering', 'School of Computing', 4, 'Comprehensive study of computing paradigms, algorithms, and systems.'),
(2, 'IT-BTECH', 'B.Tech Information Technology', 'School of Computing', 4, 'Applied computing, networked applications, security, and cloud architectures.'),
(3, 'AI-BTECH', 'B.Tech Artificial Intelligence & Machine Learning', 'School of Computing', 4, 'Foundations of intelligent machines, deep learning, NLP, and computer vision.');

-- Insert Subjects
INSERT INTO subjects (id, course_id, subject_code, subject_name, description) VALUES
(1, 1, 'CS301', 'Python Programming & Data Structures', 'Core Python semantics, OOP, generators, decorators, and data structure implementations.'),
(2, 1, 'CS302', 'Database Management Systems', 'Relational design, normalization, ACID properties, transaction processing, and SQL optimization.'),
(3, 1, 'CS303', 'Computer Networks & Distributed Systems', 'OSI/TCP-IP models, socket programming, routing protocols, flow and congestion control.'),
(4, 2, 'IT204', 'Modern Full-Stack Web Development', 'HTML5, CSS3, JavaScript, DOM architecture, RESTful APIs, and responsive design systems.');

-- Insert Exams
INSERT INTO exams (id, title, exam_code, subject_id, created_by, description, instructions, duration_minutes, total_marks, passing_percentage, start_time, end_time, status, randomize_questions, randomize_options, negative_marking, negative_mark_value, max_attempts, result_release_mode) VALUES
(1, 'Python Core & Advanced Assessment 2026', 'EXAM-PY-2026', 1, 2, 
 'Comprehensive examination evaluating Python memory management, list comprehensions, decorators, and functional tools.', 
 '1. The exam contains 10 questions of multiple types.\n2. Do not switch tabs or exit fullscreen.\n3. Each wrong answer in negative marking questions incurs -0.25 penalty.\n4. Answers are auto-saved automatically.', 
 45, 20.00, 40.00, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 'active', TRUE, TRUE, TRUE, 0.25, 3, 'immediate'),

(2, 'Database Management Systems Mid-Term Exam', 'EXAM-DBMS-MID', 2, 2, 
 'Mid-term evaluation covering ER Modeling, 3NF/BCNF normalization, and ACID transaction isolation levels.', 
 '1. Attempt all questions within the 60-minute window.\n2. Negative marking is disabled for this exam.\n3. Keep your webcam clear and avoid moving out of frame.', 
 60, 25.00, 50.00, '2026-02-01 00:00:00', '2026-12-31 23:59:59', 'active', TRUE, TRUE, FALSE, 0.00, 2, 'immediate'),

(3, 'Computer Networks & Security Assessment', 'EXAM-NET-SEC', 3, 2, 
 'Evaluation of TCP/IP protocol suite, subnetting, symmetric vs asymmetric encryption, and firewalls.', 
 '1. Fullscreen mode is strictly enforced.\n2. Review palette shows unanswered questions in red.\n3. Make sure to submit before timer expires.', 
 50, 20.00, 45.00, '2026-01-15 00:00:00', '2026-12-31 23:59:59', 'active', TRUE, FALSE, TRUE, 0.50, 1, 'immediate'),

(4, 'Web Development & Modern JavaScript Challenge', 'EXAM-WEB-DEV', 4, 1, 
 'Practical quiz testing modern DOM, event propagation, async/await, and CSS grid layout models.', 
 '1. Timer starts immediately upon launch.\n2. Auto-submission occurs at 00:00.', 
 30, 15.00, 40.00, '2026-03-01 00:00:00', '2026-12-31 23:59:59', 'active', FALSE, FALSE, FALSE, 0.00, 5, 'immediate');

-- Insert Questions for Python (Subject 1)
INSERT INTO questions (id, subject_id, topic, question_text, question_type, difficulty, marks, negative_marks, explanation, created_by) VALUES
(1, 1, 'Data Types', 'What will be the output of the following Python expression: `bool([]) + bool([0])`?', 'single_choice', 'easy', 2.00, 0.50, 'An empty list `[]` evaluates to False (0), whereas a non-empty list `[0]` evaluates to True (1). 0 + 1 = 1.', 2),
(2, 1, 'Memory Management', 'In Python, which built-in function returns the unique identity (memory address) of an object?', 'single_choice', 'easy', 2.00, 0.50, 'The id() function returns the identity of the object, which is guaranteed to be unique and constant for this object during its lifetime.', 2),
(3, 1, 'Data Structures', 'Which of the following built-in collection types in Python are mutable? (Select all that apply)', 'multiple_choice', 'medium', 2.00, 0.50, 'Lists, dictionaries, and sets are mutable. Tuples and frozensets are immutable.', 2),
(4, 1, 'Language Semantics', 'Python uses GIL (Global Interpreter Lock) to synchronize thread execution in CPython.', 'true_false', 'easy', 2.00, 0.00, 'CPython employs the Global Interpreter Lock (GIL) to protect concurrent access to Python objects across threads.', 2),
(5, 1, 'Functions', 'What keyword is used in Python to create an anonymous function?', 'fill_blank', 'easy', 2.00, 0.00, 'The `lambda` keyword is used to create small, anonymous inline functions in Python.', 2),
(6, 1, 'OOP', 'Explain the purpose of the `__init__` method in Python classes.', 'descriptive', 'medium', 2.00, 0.00, '`__init__` is the constructor method in Python. It is automatically called when a new instance of a class is created to initialize instance attributes.', 2),
(7, 1, 'Generators', 'What keyword pauses function execution and returns a value to the caller in a Python generator?', 'single_choice', 'medium', 2.00, 0.50, 'The `yield` statement is used in generators to yield a value and suspend execution state.', 2),
(8, 1, 'Decorators', 'A Python decorator is syntactic sugar for passing a function as an argument to another callable and returning a replacement.', 'true_false', 'medium', 2.00, 0.00, 'True: `@dec` preceding `def func():` is equivalent to `func = dec(func)`.', 2);

-- Insert Options for Question 1
INSERT INTO question_options (id, question_id, option_text, is_correct, option_order) VALUES
(1, 1, '0', FALSE, 1),
(2, 1, '1', TRUE, 2),
(3, 1, '2', FALSE, 3),
(4, 1, 'TypeError', FALSE, 4);

-- Insert Options for Question 2
INSERT INTO question_options (id, question_id, option_text, is_correct, option_order) VALUES
(5, 2, 'id()', TRUE, 1),
(6, 2, 'ref()', FALSE, 2),
(7, 2, 'memory()', FALSE, 3),
(8, 2, 'address()', FALSE, 4);

-- Insert Options for Question 3 (Multiple Choice)
INSERT INTO question_options (id, question_id, option_text, is_correct, option_order) VALUES
(9, 3, 'List', TRUE, 1),
(10, 3, 'Tuple', FALSE, 2),
(11, 3, 'Dictionary', TRUE, 3),
(12, 3, 'Set', TRUE, 4);

-- Insert Options for Question 4 (True/False)
INSERT INTO question_options (id, question_id, option_text, is_correct, option_order) VALUES
(13, 4, 'True', TRUE, 1),
(14, 4, 'False', FALSE, 2);

-- Question 5 is Fill in Blank: option text holds acceptable answer
INSERT INTO question_options (id, question_id, option_text, is_correct, option_order) VALUES
(15, 5, 'lambda', TRUE, 1);

-- Question 6 is descriptive: option holds sample model answer
INSERT INTO question_options (id, question_id, option_text, is_correct, option_order) VALUES
(16, 6, 'Constructor/initializer method that assigns initial attributes to object instances upon instantiation.', TRUE, 1);

-- Question 7 Options
INSERT INTO question_options (id, question_id, option_text, is_correct, option_order) VALUES
(17, 7, 'return', FALSE, 1),
(18, 7, 'yield', TRUE, 2),
(19, 7, 'pause', FALSE, 3),
(20, 7, 'produce', FALSE, 4);

-- Question 8 Options
INSERT INTO question_options (id, question_id, option_text, is_correct, option_order) VALUES
(21, 8, 'True', TRUE, 1),
(22, 8, 'False', FALSE, 2);

-- Insert Questions for DBMS (Subject 2)
INSERT INTO questions (id, subject_id, topic, question_text, question_type, difficulty, marks, negative_marks, explanation, created_by) VALUES
(9, 2, 'ACID Properties', 'Which ACID property guarantees that transactions are processed reliably and completely, or not at all?', 'single_choice', 'easy', 2.50, 0.00, 'Atomicity ensures that all statements in a transaction are executed as a single indivisible unit.', 2),
(10, 2, 'Normalization', 'A relation is in Boyce-Codd Normal Form (BCNF) if and only if for every non-trivial functional dependency X -> Y, X is a superkey.', 'true_false', 'medium', 2.50, 0.00, 'By definition, BCNF requires the determinant X to be a super key for every non-trivial dependency.', 2),
(11, 2, 'SQL & Keys', 'Which SQL constraint uniquely identifies each record in a database table without accepting NULL values?', 'single_choice', 'easy', 2.50, 0.00, 'A PRIMARY KEY uniquely identifies rows and never accepts NULL values (unlike UNIQUE which allows one or more NULLs depending on SQL engine).', 2),
(12, 2, 'Joins', 'Which join type returns all rows from the left table, and matching rows from the right table, filling missing right values with NULL?', 'single_choice', 'easy', 2.50, 0.00, 'LEFT OUTER JOIN (or LEFT JOIN) keeps all records from the left relation.', 2);

INSERT INTO question_options (id, question_id, option_text, is_correct, option_order) VALUES
(23, 9, 'Atomicity', TRUE, 1),
(24, 9, 'Consistency', FALSE, 2),
(25, 9, 'Isolation', FALSE, 3),
(26, 9, 'Durability', FALSE, 4),
(27, 10, 'True', TRUE, 1),
(28, 10, 'False', FALSE, 2),
(29, 11, 'PRIMARY KEY', TRUE, 1),
(30, 11, 'UNIQUE', FALSE, 2),
(31, 11, 'FOREIGN KEY', FALSE, 3),
(32, 11, 'CHECK', FALSE, 4),
(33, 12, 'LEFT JOIN', TRUE, 1),
(34, 12, 'RIGHT JOIN', FALSE, 2),
(35, 12, 'INNER JOIN', FALSE, 3),
(36, 12, 'FULL JOIN', FALSE, 4);

-- Associate Questions with Exam 1 (Python Exam)
INSERT INTO exam_questions (exam_id, question_id, marks, negative_marks, question_order) VALUES
(1, 1, 2.00, 0.50, 1),
(1, 2, 2.00, 0.50, 2),
(1, 3, 2.00, 0.50, 3),
(1, 4, 2.00, 0.00, 4),
(1, 5, 2.00, 0.00, 5),
(1, 6, 2.00, 0.00, 6),
(1, 7, 2.00, 0.50, 7),
(1, 8, 2.00, 0.00, 8);

-- Associate Questions with Exam 2 (DBMS Exam)
INSERT INTO exam_questions (exam_id, question_id, marks, negative_marks, question_order) VALUES
(2, 9, 2.50, 0.00, 1),
(2, 10, 2.50, 0.00, 2),
(2, 11, 2.50, 0.00, 3),
(2, 12, 2.50, 0.00, 4);

-- Insert Sample Exam Attempts & Results for Demonstration
-- Attempt 1: Aman Sharma completed Python Exam with 87.5% score
INSERT INTO exam_attempts (id, exam_id, student_id, attempt_number, start_time, submit_time, time_spent_seconds, status, total_score, percentage, passed, ip_address, browser_agent) VALUES
(1, 1, 1, 1, '2026-03-10 10:00:00', '2026-03-10 10:28:45', 1725, 'submitted', 14.00, 87.50, TRUE, '192.168.1.102', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)');

-- Answers for Attempt 1
INSERT INTO answers (attempt_id, question_id, selected_option_ids, text_answer, is_marked_for_review, is_visited, is_answered, is_correct, marks_awarded, time_spent_seconds) VALUES
(1, 1, '2', NULL, FALSE, TRUE, TRUE, TRUE, 2.00, 120),
(1, 2, '5', NULL, FALSE, TRUE, TRUE, TRUE, 2.00, 95),
(1, 3, '9,11,12', NULL, FALSE, TRUE, TRUE, TRUE, 2.00, 210),
(1, 4, '13', NULL, FALSE, TRUE, TRUE, TRUE, 2.00, 80),
(1, 5, NULL, 'lambda', FALSE, TRUE, TRUE, TRUE, 2.00, 110),
(1, 6, NULL, 'Initializes an object instance with attributes.', FALSE, TRUE, TRUE, TRUE, 2.00, 350),
(1, 7, '18', NULL, FALSE, TRUE, TRUE, TRUE, 2.00, 140),
(1, 8, '22', NULL, FALSE, TRUE, TRUE, FALSE, -0.00, 90); -- wrong answer

-- Result for Attempt 1
INSERT INTO results (id, attempt_id, exam_id, student_id, score, total_marks, percentage, grade, status, correct_count, incorrect_count, skipped_count, accuracy, time_taken_seconds, feedback, published_at) VALUES
(1, 1, 1, 1, 14.00, 16.00, 87.50, 'A+', 'pass', 7, 1, 0, 87.50, 1725, 'Outstanding grasp of Python syntax, collections, and functional programming!', '2026-03-10 10:28:46');

-- Certificate for Result 1
INSERT INTO certificates (id, result_id, student_id, exam_id, certificate_code, issue_date, grade, percentage, file_path, is_valid) VALUES
(1, 1, 1, 1, 'EXAMPRO-CERT-PY-882941', '2026-03-10', 'A+', 87.50, '/static/certificates/cert_1.pdf', TRUE);

-- Notifications
INSERT INTO notifications (id, user_id, title, message, type, is_read, link) VALUES
(1, 3, 'Exam Completed Successfully', 'Your attempt for Python Core & Advanced Assessment has been evaluated with a score of 87.5%.', 'success', TRUE, '/student/results/1'),
(2, 3, 'Certificate Generated', 'Your certificate of excellence for Python Core & Advanced Assessment is now ready for download.', 'info', FALSE, '/student/certificates'),
(3, 3, 'Upcoming Exam Notice', 'Database Management Systems Mid-Term is scheduled. Verify your device readiness.', 'exam', FALSE, '/student/exams'),
(4, 1, 'New Student Registration', 'Student Rahul Verma has registered with ID STU-1003.', 'info', FALSE, '/admin/students'),
(5, 2, 'Exam Attempt Submitted', 'Aman Sharma submitted Python Core & Advanced Assessment.', 'info', TRUE, '/teacher/results');

-- Security Logs (Demonstration log of violation detection)
INSERT INTO security_logs (id, attempt_id, student_id, exam_id, event_type, details, severity, created_at) VALUES
(1, 1, 1, 1, 'tab_switch', 'User switched browser tab or focus lost for 4 seconds.', 'low', '2026-03-10 10:14:22'),
(2, 1, 1, 1, 'copy_paste', 'Blocked clipboard copy attempt on question 3.', 'medium', '2026-03-10 10:18:05');

