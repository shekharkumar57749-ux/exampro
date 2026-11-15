import logging
from werkzeug.security import generate_password_hash, check_password_hash
from database.connection import query_db, execute_commit

logger = logging.getLogger('exampro.models.user')

def get_user_by_id(user_id):
    """Retrieve user record by primary key."""
    return query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)

def get_user_by_email(email):
    """Retrieve user record by email."""
    return query_db("SELECT * FROM users WHERE email = %s", (email.strip().lower(),), one=True)

def get_user_by_username_or_email(identifier):
    """Retrieve user by username, email, or student ID."""
    clean_id = identifier.strip().lower()
    # Check users table
    user = query_db("""
        SELECT u.*, s.student_id, s.course, s.college, t.employee_id, t.department 
        FROM users u 
        LEFT JOIN students s ON u.id = s.user_id 
        LEFT JOIN teachers t ON u.id = t.user_id 
        WHERE LOWER(u.email) = %s OR LOWER(u.username) = %s OR LOWER(s.student_id) = %s
    """, (clean_id, clean_id, clean_id), one=True)
    return user

def create_student(username, email, password, full_name, phone, student_id, course='B.Tech Computer Science', college='Institute of Technology & Science'):
    """Register a new student."""
    # Check duplicate
    if get_user_by_email(email):
        raise ValueError("An account with this email address already exists.")
    
    existing_stu = query_db("SELECT id FROM students WHERE student_id = %s", (student_id.strip(),), one=True)
    if existing_stu:
        raise ValueError("This Student ID is already registered.")

    pwd_hash = generate_password_hash(password)
    user_id = execute_commit("""
        INSERT INTO users (username, email, password_hash, role, full_name, phone, status)
        VALUES (%s, %s, %s, 'student', %s, %s, 'active')
    """, (username.strip().lower(), email.strip().lower(), pwd_hash, full_name.strip(), phone.strip() if phone else None))

    execute_commit("""
        INSERT INTO students (user_id, student_id, course, college)
        VALUES (%s, %s, %s, %s)
    """, (user_id, student_id.strip(), course, college))

    return user_id

def create_teacher(username, email, password, full_name, phone, employee_id, department, designation, assigned_subjects=''):
    """Create a new teacher account."""
    if get_user_by_email(email):
        raise ValueError("An account with this email address already exists.")
    
    pwd_hash = generate_password_hash(password)
    user_id = execute_commit("""
        INSERT INTO users (username, email, password_hash, role, full_name, phone, status)
        VALUES (%s, %s, %s, 'teacher', %s, %s, 'active')
    """, (username.strip().lower(), email.strip().lower(), pwd_hash, full_name.strip(), phone.strip() if phone else None))

    execute_commit("""
        INSERT INTO teachers (user_id, employee_id, department, designation, assigned_subjects)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, employee_id.strip(), department, designation, assigned_subjects))

    return user_id

def get_student_profile(user_id):
    """Retrieve full student profile with user attributes."""
    return query_db("""
        SELECT u.id as user_id, u.username, u.email, u.full_name, u.phone, u.avatar_url, u.status, u.created_at,
               s.id as student_table_id, s.student_id, s.course, s.college, s.enrollment_year, s.semester, s.cgpa
        FROM users u
        JOIN students s ON u.id = s.user_id
        WHERE u.id = %s
    """, (user_id,), one=True)

def get_student_by_student_table_id(student_id):
    """Retrieve student profile by students.id."""
    return query_db("""
        SELECT u.id as user_id, u.username, u.email, u.full_name, u.phone, u.avatar_url, u.status,
               s.id as student_table_id, s.student_id, s.course, s.college, s.enrollment_year, s.semester, s.cgpa
        FROM students s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = %s
    """, (student_id,), one=True)

def get_all_students(search=None, status=None, limit=100, offset=0):
    """List students with search and filter support."""
    sql = """
        SELECT u.id as user_id, u.username, u.email, u.full_name, u.phone, u.status, u.created_at,
               s.id as student_table_id, s.student_id, s.course, s.college, s.semester, s.cgpa,
               (SELECT COUNT(*) FROM exam_attempts ea WHERE ea.student_id = s.id AND ea.status IN ('submitted', 'auto_submitted')) as exams_completed,
               (SELECT ROUND(AVG(r.percentage), 1) FROM results r WHERE r.student_id = s.id) as avg_score
        FROM students s
        JOIN users u ON s.user_id = u.id
        WHERE 1=1
    """
    params = []
    if search:
        search_pattern = f"%{search.strip()}%"
        sql += " AND (u.full_name LIKE %s OR u.email LIKE %s OR s.student_id LIKE %s OR s.course LIKE %s)"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
    if status and status != 'all':
        sql += " AND u.status = %s"
        params.append(status)
    
    sql += " ORDER BY s.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return query_db(sql, tuple(params))

def get_all_teachers(search=None, limit=100, offset=0):
    """List teachers with search."""
    sql = """
        SELECT u.id as user_id, u.username, u.email, u.full_name, u.phone, u.status, u.created_at,
               t.id as teacher_table_id, t.employee_id, t.department, t.designation, t.assigned_subjects, t.qualification,
               (SELECT COUNT(*) FROM exams e WHERE e.created_by = u.id) as exams_created
        FROM teachers t
        JOIN users u ON t.user_id = u.id
        WHERE 1=1
    """
    params = []
    if search:
        search_pattern = f"%{search.strip()}%"
        sql += " AND (u.full_name LIKE %s OR u.email LIKE %s OR t.employee_id LIKE %s OR t.department LIKE %s)"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
        
    sql += " ORDER BY t.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return query_db(sql, tuple(params))

def update_user_profile(user_id, full_name, phone, avatar_url=None):
    """Update user basic profile."""
    if avatar_url:
        return execute_commit("""
            UPDATE users SET full_name = %s, phone = %s, avatar_url = %s WHERE id = %s
        """, (full_name.strip(), phone.strip() if phone else None, avatar_url, user_id))
    else:
        return execute_commit("""
            UPDATE users SET full_name = %s, phone = %s WHERE id = %s
        """, (full_name.strip(), phone.strip() if phone else None, user_id))

def update_student_academic(user_id, course, college, semester):
    """Update student academic details."""
    return execute_commit("""
        UPDATE students SET course = %s, college = %s, semester = %s WHERE user_id = %s
    """, (course.strip(), college.strip(), semester, user_id))

def toggle_user_status(user_id, new_status):
    """Change status of user ('active' or 'disabled')."""
    return execute_commit("UPDATE users SET status = %s WHERE id = %s", (new_status, user_id))

def change_password(user_id, old_password, new_password):
    """Securely verify old password and update to new password hash."""
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError("User not found.")
    if not check_password_hash(user['password_hash'], old_password):
        raise ValueError("Current password is incorrect.")
    
    new_hash = generate_password_hash(new_password)
    execute_commit("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
    return True

