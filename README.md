# ExamPro – Advanced Examination Management System

An enterprise-grade, responsive, and secure web-based digital examination management platform designed for universities, colleges, and testing bodies to author, schedule, proctor, and evaluate examinations with real-time analytics.

---

## 1. Project Introduction

**ExamPro** is built from the ground up to eliminate the vulnerabilities and inefficiencies of manual and basic web examinations. It delivers a modern, high-performance SaaS-style experience with dedicated portals for:

1. **Students** – Distraction-free proctored examination rooms, countdown timers, real-time draft saving, instant circular scorecards, detailed review explanations, verified PDF certificates, and cognitive analytics.
2. **Teachers / Educators** – Multi-step examination creation wizards, centralized question bank repositories, CSV question bulk-importing, and submission evaluation.
3. **Administrators** – System-wide institutional control, student and faculty management, security proctoring audit trails, certificate registries, and performance indexes.

---

## 2. Technology Stack

Built strictly within the requested tech stack specifications with clean separation of concerns and zero unnecessary bloatware:

- **Frontend:**
  - **HTML5:** Semantic architecture, accessible forms, and modular templates.
  - **CSS3:** Custom design system, CSS variables with seamless **Light and Dark theme** toggling, responsive grid/flexbox layouts.
  - **Vanilla JavaScript:** DOM state management, real-time AJAX auto-saving, countdown timer engine, proctoring sensors, and modal controllers.
  - **Chart.js:** Real-time analytics, grade distributions, pass/fail ratios, and score progression trends.
  - **Font Awesome 6:** Vector iconography.
- **Backend:**
  - **Python 3.10+ / 3.14:** Core language runtime.
  - **Flask:** Modular blueprint-based microframework.
  - **Werkzeug:** Cryptographic password hashing (`scrypt`) and security utilities.
  - **ReportLab & Pillow:** Generation of PDF examination scorecards and certificates.
- **Database:**
  - **MySQL 8.0+:** Enterprise relational database with foreign key integrity, ACID transactions, and comprehensive indexes.
  - **Auto-Fallback Engine:** Seamlessly supports MySQL with zero configuration, and provides an automatic SQLite fallback (`database/exampro.sqlite`) for immediate evaluation out-of-the-box.

---

## 3. Key Features

### 🛡️ Distraction-Free Proctored Exam Room
- Fullscreen enforcement mode.
- Real-time countdown timer with visual and auditory warnings when under 5 minutes remaining.
- Automatic exam submission on timer expiration.
- Auto-save engine that asynchronously persists candidates' answers to the cloud in real time via AJAX.
- 5-state interactive Question Palette:
  - ⬜ **Grey:** Not Visited
  - 🔴 **Red:** Visited / Unanswered
  - 🟢 **Green:** Answered
  - 🟡 **Yellow:** Marked for Review
  - 🔵 **Blue:** Current Active Question
- Anti-cheating proctoring sensors detecting window blur, tab switching, right-click, and copy/paste attempts.

### 📝 Multi-Format Question Bank
- Single-Choice Multiple Choice (MCQ).
- Multiple-Choice (Multi-select checkbox).
- True / False statements.
- Fill in the Blanks (case-insensitive string evaluation).
- Descriptive / Essay-style responses.
- CSV question bulk import with formatting validator.

### 📊 Real-Time Automated Evaluation & Results
- Server-side scoring engine factoring in configurable negative marking penalty.
- Letter grade assignment (A+, A, B, C, D, E, F).
- Circular score percentage gauges.
- Comprehensive review displaying candidate's submitted answer versus correct answer and explanations.
- Downloadable official PDF scorecard.

### 🏆 Verified Digital Certificates
- Automated certificate issuance upon passing examination threshold.
- Unique certificate identification number (e.g. `EXAMPRO-EXAM-PY-2026-A1B2C3D4`).
- Public verification portal (`/verify-certificate/<certificate_code>`) for employers and academic bodies.
- High-resolution landscape PDF certificate generation.

### 📈 Cognitive Performance Analytics
- Score timeline tracking performance across successive attempts.
- Subject-wise and difficulty-wise performance breakdowns.
- Topic diagnostic highlighting strong areas ($\ge 70\%$) and weak areas ($< 70\%$).

---

## 4. Architecture & Folder Structure

```
exampro/
│
├── app.py                      # Application entry point & factory
├── config.py                   # Centralized configuration & environment loader
├── requirements.txt            # Python dependencies
├── database.sql                # Complete MySQL 8.0 DDL & seed data script
├── README.md                   # Project documentation
├── .env.example                # Sample environment variables
│
├── database/
│   ├── connection.py           # Universal DB adapter (MySQL + SQLite fallback)
│   └── initialize_db.py       # Automated database table & seed data initializer
│
├── routes/
│   ├── __init__.py             # Auth & role-based access decorators
│   ├── auth_routes.py          # Registration, login, logout, notifications
│   ├── student_routes.py       # Student dashboard, exams, room, results, certificates
│   ├── teacher_routes.py       # Educator dashboard, exams, question bank, grading
│   ├── admin_routes.py         # Admin dashboard, students, teachers, security logs
│   ├── exam_routes.py          # Real-time answer saving, submission, security logging
│   ├── result_routes.py        # PDF scorecard & certificate downloads, public verification
│   └── analytics_routes.py     # JSON analytics endpoints for Chart.js
│
├── models/
│   ├── __init__.py
│   ├── user_model.py           # User, Student, Teacher, Admin models & auth queries
│   ├── exam_model.py           # Exam CRUD, attempts, answers map, courses & subjects
│   ├── question_model.py       # Question bank CRUD, exam linking, randomization
│   ├── result_model.py         # Results, detailed review questions, certificates
│   └── notification_model.py   # In-app notifications & proctoring security logs
│
├── services/
│   ├── __init__.py
│   ├── evaluation_service.py   # Automated grading, negative marking, grade calculator
│   ├── certificate_service.py  # ReportLab PDF certificate & scorecard generator
│   └── analytics_service.py    # Chart.js metrics, strength/weakness diagnostics
│
├── templates/
│   ├── base.html               # Master layout with theme toggler & notifications
│   ├── landing.html            # Commercial public landing page
│   ├── about.html              # System overview
│   ├── features.html           # Full capabilities
│   ├── contact.html            # Support portal
│   ├── verify_certificate.html # Public certificate verification portal
│   │
│   ├── auth/
│   │   ├── student_login.html  # Student portal login
│   │   ├── teacher_login.html  # Educator portal login
│   │   ├── admin_login.html    # Admin console login
│   │   └── register.html       # Candidate registration with password strength meter
│   │
│   ├── student/
│   │   ├── student_base.html   # Student layout with sidebar & topbar
│   │   ├── dashboard.html      # KPI cards, upcoming exams, recent results, chart
│   │   ├── exams.html          # Available exams list
│   │   ├── examination.html    # Proctored examination room
│   │   ├── results.html        # Results history
│   │   ├── result_detail.html  # Scorecard with question review
│   │   ├── analytics.html      # Detailed cognitive analytics
│   │   ├── certificates.html   # Earned certificates
│   │   ├── profile.html        # Student academic profile
│   │   └── settings.html       # Theme & password settings
│   │
│   ├── teacher/
│   │   ├── teacher_base.html   # Educator layout
│   │   ├── dashboard.html      # Teacher overview
│   │   ├── exams.html          # Manage teacher exams
│   │   ├── exam_create.html    # 4-step wizard examination builder
│   │   ├── questions.html      # Question bank repository & CSV import
│   │   └── results.html        # Candidate submissions
│   │
│   ├── admin/
│   │   ├── admin_base.html     # Admin layout
│   │   ├── dashboard.html      # Global institutional analytics
│   │   ├── students.html       # Student roster & status toggles
│   │   ├── teachers.html       # Faculty management
│   │   ├── exams.html          # Global exam management
│   │   ├── exam_create.html    # Exam creator
│   │   ├── question_bank.html  # Master repository
│   │   ├── results.html        # Results archive
│   │   ├── analytics.html      # Macro-level performance index
│   │   ├── security_logs.html  # Live anti-cheat incident audit log
│   │   └── settings.html       # Institutional configuration
│   │
│   └── errors/
│       ├── 403.html            # Forbidden
│       ├── 404.html            # Not Found
│       └── 500.html            # Internal Error
│
├── static/
│   ├── css/
│   │   ├── style.css           # Core design system & theme variables
│   │   ├── dashboard.css       # Sidebar, topbar, cards, tables, wizard
│   │   ├── examination.css     # Proctored room, timer, question palette
│   │   └── responsive.css      # Mobile drawer & adaptive breakpoints
│   │
│   ├── js/
│   │   ├── main.js             # Theme toggle, toasts, notifications, modals
│   │   ├── examination.js      # Exam engine, auto-save, timer, proctoring
│   │   ├── analytics.js        # Chart.js visualization engine
│   │   ├── dashboard.js        # Table filters & multi-step wizard
│   │   └── validation.js       # Password strength meter & client validation
│   │
│   └── images/
│       └── default-avatar.png
│
└── tests/
    ├── __init__.py
    ├── test_auth.py            # Authentication & role isolation tests
    ├── test_exams.py           # Exam attempt & real-time auto-saving tests
    └── test_results.py         # Grading, negative marking, PDF generation tests
```

---

## 5. Database Design & Tables

The schema comprises 16 normalized relational tables:

1. `users` – Core user accounts (email, password hash, role, status).
2. `students` – Student profiles (student ID, course, college, cgpa).
3. `teachers` – Faculty profiles (employee ID, department, designation).
4. `admins` – Administrator credentials (admin code, office).
5. `courses` – Academic degree programs.
6. `subjects` – Course modules and curriculum codes.
7. `exams` – Examination metadata, durations, passing %, negative marks, and randomization flags.
8. `questions` – Multi-format question bank repository.
9. `question_options` – Answer choices with correctness flags.
10. `exam_questions` – Associative link between exams and selected questions.
11. `exam_attempts` – Candidate test attempts, IP addresses, user agents, and status.
12. `answers` – Student choices, review marks, and time spent per item.
13. `results` – Evaluated marks, percentages, accuracy %, and letter grades.
14. `certificates` – Issued digital credentials and verification codes.
15. `notifications` – In-app alerts and notifications.
16. `security_logs` – Anti-cheating proctoring event logs.

---

## 6. Installation & Execution Guide

### Step 1: Clone or Navigate to Directory
```bash
cd c:\Users\shekh\Desktop\exampro
```

### Step 2: Set Up Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
```
Activate on Windows:
```bash
venv\Scripts\activate
```

### Step 3: Install Required Packages
```bash
pip install -r requirements.txt
```

### Step 4: Configure Database Credentials (Optional for MySQL)
Create a `.env` file from `.env.example`:
```ini
FLASK_ENV=development
SECRET_KEY=exampro-enterprise-secure-key-2026-v1
PORT=5000

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=exampro_db
```
*Note: If MySQL is not running or credentials are not supplied, ExamPro automatically switches to its SQLite database (`database/exampro.sqlite`), ensuring instant out-of-the-box functionality!*

### Step 5: Initialize Database & Seed Records
```bash
python database/initialize_db.py
```

### Step 6: Run Automated Tests
```bash
python -m unittest discover tests
```

### Step 7: Launch the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 7. Demonstration Accounts

| Role | Email / Identifier | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Student** | `student@exampro.com` or `STU-1001` | `Student@123` | Take active exams, review scorecards, view analytics, download certificates |
| **Student 2** | `priya@exampro.com` or `STU-1002` | `Student@123` | Take active exams, review results |
| **Teacher** | `teacher@exampro.com` or `TCH-101` | `Teacher@123` | Create exams, add questions, import CSV questions, grade submissions |
| **Admin** | `admin@exampro.com` | `Admin@123` | Manage students/teachers, view security logs, platform analytics |

---

## 8. Academic Presentation & Defense Highlights

When presenting this project for major academic evaluations or portfolio reviews, highlight these key engineering strengths:

1. **Robust Separation of Concerns:** Database layers, data models, business logic (evaluation, PDF generation, analytics), routes, and vanilla frontend scripts are strictly decoupled.
2. **Real-Time Data Persistence:** Candidate answers are saved asynchronously over AJAX to prevent data loss on accidental browser refreshes.
3. **ReportLab Document Processing:** Commercial PDF certificates with custom vector graphics and score reports are generated programmatically on the server.
4. **Proctoring Sensor Architecture:** Browser visibility change and window focus listeners detect and log tab switching and copy-paste events directly into `security_logs`.
5. **No Bulky Framework Dependencies:** 100% vanilla JavaScript with clean CSS custom properties, ensuring lightning-fast load times and maintainability.

---

## 9. License

Developed for Academic and Portfolio Demonstration. All rights reserved.

