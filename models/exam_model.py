import logging
from datetime import datetime
from database.connection import query_db, execute_commit

logger = logging.getLogger('exampro.models.exam')

def get_all_exams(status=None, created_by=None, search=None):
    """Retrieve exams list with optional filters."""
    sql = """
        SELECT e.*, s.subject_name, s.subject_code, c.course_name, u.full_name as creator_name,
               (SELECT COUNT(*) FROM exam_questions eq WHERE eq.exam_id = e.id) as total_questions,
               (SELECT COUNT(*) FROM exam_attempts ea WHERE ea.exam_id = e.id) as total_attempts
        FROM exams e
        JOIN subjects s ON e.subject_id = s.id
        LEFT JOIN courses c ON s.course_id = c.id
        JOIN users u ON e.created_by = u.id
        WHERE 1=1
    """
    params = []
    if status and status != 'all':
        sql += " AND e.status = %s"
        params.append(status)
    if created_by:
        sql += " AND e.created_by = %s"
        params.append(created_by)
    if search:
        pattern = f"%{search.strip()}%"
        sql += " AND (e.title LIKE %s OR e.exam_code LIKE %s OR s.subject_name LIKE %s)"
        params.extend([pattern, pattern, pattern])

    sql += " ORDER BY e.id DESC"
    return query_db(sql, tuple(params))

def get_exam_by_id(exam_id):
    """Get single exam by ID with full details."""
    sql = """
        SELECT e.*, s.subject_name, s.subject_code, c.course_name, u.full_name as creator_name,
               (SELECT COUNT(*) FROM exam_questions eq WHERE eq.exam_id = e.id) as total_questions,
               (SELECT COUNT(*) FROM exam_attempts ea WHERE ea.exam_id = e.id) as total_attempts
        FROM exams e
        JOIN subjects s ON e.subject_id = s.id
        LEFT JOIN courses c ON s.course_id = c.id
        JOIN users u ON e.created_by = u.id
        WHERE e.id = %s
    """
    return query_db(sql, (exam_id,), one=True)

def create_exam(data):
    """Insert a new exam."""
    sql = """
        INSERT INTO exams (title, exam_code, subject_id, created_by, description, instructions,
                           duration_minutes, total_marks, passing_percentage, start_time, end_time,
                           status, randomize_questions, randomize_options, negative_marking,
                           negative_mark_value, max_attempts, result_release_mode)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        data.get('title'),
        data.get('exam_code'),
        data.get('subject_id'),
        data.get('created_by'),
        data.get('description', ''),
        data.get('instructions', ''),
        int(data.get('duration_minutes', 60)),
        float(data.get('total_marks', 100)),
        float(data.get('passing_percentage', 40)),
        data.get('start_time'),
        data.get('end_time'),
        data.get('status', 'active'),
        1 if data.get('randomize_questions') else 0,
        1 if data.get('randomize_options') else 0,
        1 if data.get('negative_marking') else 0,
        float(data.get('negative_mark_value', 0.25)),
        int(data.get('max_attempts', 1)),
        data.get('result_release_mode', 'immediate')
    )
    return execute_commit(sql, params)

def update_exam(exam_id, data):
    """Update exam details."""
    sql = """
        UPDATE exams SET title=%s, exam_code=%s, subject_id=%s, description=%s, instructions=%s,
                         duration_minutes=%s, total_marks=%s, passing_percentage=%s, start_time=%s,
                         end_time=%s, status=%s, randomize_questions=%s, randomize_options=%s,
                         negative_marking=%s, negative_mark_value=%s, max_attempts=%s, result_release_mode=%s
        WHERE id = %s
    """
    params = (
        data.get('title'),
        data.get('exam_code'),
        data.get('subject_id'),
        data.get('description'),
        data.get('instructions'),
        int(data.get('duration_minutes', 60)),
        float(data.get('total_marks', 100)),
        float(data.get('passing_percentage', 40)),
        data.get('start_time'),
        data.get('end_time'),
        data.get('status', 'active'),
        1 if data.get('randomize_questions') else 0,
        1 if data.get('randomize_options') else 0,
        1 if data.get('negative_marking') else 0,
        float(data.get('negative_mark_value', 0.25)),
        int(data.get('max_attempts', 1)),
        data.get('result_release_mode', 'immediate'),
        exam_id
    )
    return execute_commit(sql, params)

def delete_exam(exam_id):
    """Delete an exam."""
    return execute_commit("DELETE FROM exams WHERE id = %s", (exam_id,))

def get_student_available_exams(student_id):
    """
    Retrieve active exams for a student, with attempt status and attempt counts.
    """
    sql = """
        SELECT e.*, s.subject_name, s.subject_code,
               (SELECT COUNT(*) FROM exam_questions eq WHERE eq.exam_id = e.id) as question_count,
               (SELECT COUNT(*) FROM exam_attempts ea WHERE ea.exam_id = e.id AND ea.student_id = %s) as student_attempts_count,
               (SELECT ea.id FROM exam_attempts ea WHERE ea.exam_id = e.id AND ea.student_id = %s AND ea.status = 'in_progress' ORDER BY ea.id DESC LIMIT 1) as in_progress_attempt_id,
               (SELECT r.id FROM results r JOIN exam_attempts ea ON r.attempt_id = ea.id WHERE ea.exam_id = e.id AND ea.student_id = %s ORDER BY r.id DESC LIMIT 1) as latest_result_id
        FROM exams e
        JOIN subjects s ON e.subject_id = s.id
        WHERE e.status = 'active'
        ORDER BY e.start_time ASC
    """
    return query_db(sql, (student_id, student_id, student_id))

def get_courses():
    """Retrieve all available courses."""
    return query_db("SELECT * FROM courses ORDER BY course_name ASC")

def get_subjects(course_id=None):
    """Retrieve subjects, optionally filtered by course."""
    if course_id:
        return query_db("SELECT s.*, c.course_name FROM subjects s LEFT JOIN courses c ON s.course_id = c.id WHERE s.course_id = %s ORDER BY s.subject_name ASC", (course_id,))
    return query_db("SELECT s.*, c.course_name FROM subjects s LEFT JOIN courses c ON s.course_id = c.id ORDER BY s.subject_name ASC")

def get_attempt_by_id(attempt_id):
    """Retrieve single attempt record."""
    sql = """
        SELECT ea.*, e.title as exam_title, e.duration_minutes, e.total_marks as exam_total_marks,
               e.passing_percentage, e.negative_marking, e.negative_mark_value, e.instructions,
               s.subject_name, stu.student_id as student_code, u.full_name as student_name
        FROM exam_attempts ea
        JOIN exams e ON ea.exam_id = e.id
        JOIN subjects s ON e.subject_id = s.id
        JOIN students stu ON ea.student_id = stu.id
        JOIN users u ON stu.user_id = u.id
        WHERE ea.id = %s
    """
    return query_db(sql, (attempt_id,), one=True)

def create_attempt(exam_id, student_id, ip_address='127.0.0.1', browser_agent=''):
    """Create a new exam attempt for a student."""
    # Check max attempts limit
    exam = get_exam_by_id(exam_id)
    if not exam:
        raise ValueError("Exam does not exist.")
    
    attempts_done = query_db("""
        SELECT COUNT(*) as cnt FROM exam_attempts 
        WHERE exam_id = %s AND student_id = %s AND status IN ('submitted', 'auto_submitted')
    """, (exam_id, student_id), one=True)
    
    if attempts_done and attempts_done['cnt'] >= exam['max_attempts']:
        raise ValueError(f"You have reached the maximum allowed attempts ({exam['max_attempts']}) for this examination.")

    # Check if there is already an in-progress attempt to resume
    active_attempt = query_db("""
        SELECT id FROM exam_attempts 
        WHERE exam_id = %s AND student_id = %s AND status = 'in_progress'
        ORDER BY id DESC LIMIT 1
    """, (exam_id, student_id), one=True)
    
    if active_attempt:
        return active_attempt['id']

    next_num = (attempts_done['cnt'] if attempts_done else 0) + 1
    attempt_id = execute_commit("""
        INSERT INTO exam_attempts (exam_id, student_id, attempt_number, status, ip_address, browser_agent)
        VALUES (%s, %s, %s, 'in_progress', %s, %s)
    """, (exam_id, student_id, next_num, ip_address, browser_agent))

    # Pre-seed blank answer records for each exam question so student navigation state is preserved
    exam_questions = query_db("SELECT question_id FROM exam_questions WHERE exam_id = %s", (exam_id,))
    for eq in exam_questions:
        execute_commit("""
            INSERT OR IGNORE INTO answers (attempt_id, question_id, is_visited, is_marked_for_review, is_answered)
            VALUES (%s, %s, 0, 0, 0)
        """ if query_db("SELECT 1 FROM sqlite_master", one=True) else """
            INSERT IGNORE INTO answers (attempt_id, question_id, is_visited, is_marked_for_review, is_answered)
            VALUES (%s, %s, 0, 0, 0)
        """, (attempt_id, eq['question_id']))

    return attempt_id

def save_answer(attempt_id, question_id, selected_option_ids=None, text_answer=None, is_marked_for_review=False, is_visited=True, time_spent_seconds=0):
    """Save or update student answer for a question in real-time via AJAX."""
    has_answer = False
    if selected_option_ids and str(selected_option_ids).strip():
        has_answer = True
    elif text_answer and str(text_answer).strip():
        has_answer = True

    # Check if answer row exists
    existing = query_db("SELECT id FROM answers WHERE attempt_id = %s AND question_id = %s", (attempt_id, question_id), one=True)
    
    if existing:
        sql = """
            UPDATE answers 
            SET selected_option_ids = %s, text_answer = %s, is_marked_for_review = %s,
                is_visited = %s, is_answered = %s, time_spent_seconds = time_spent_seconds + %s
            WHERE attempt_id = %s AND question_id = %s
        """
        execute_commit(sql, (
            selected_option_ids, text_answer, 1 if is_marked_for_review else 0,
            1 if is_visited else 0, 1 if has_answer else 0, int(time_spent_seconds),
            attempt_id, question_id
        ))
    else:
        sql = """
            INSERT INTO answers (attempt_id, question_id, selected_option_ids, text_answer,
                                is_marked_for_review, is_visited, is_answered, time_spent_seconds)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_commit(sql, (
            attempt_id, question_id, selected_option_ids, text_answer,
            1 if is_marked_for_review else 0, 1 if is_visited else 0,
            1 if has_answer else 0, int(time_spent_seconds)
        ))
    return True

def get_attempt_answers_map(attempt_id):
    """Retrieve all student responses for an attempt indexed by question_id."""
    rows = query_db("SELECT * FROM answers WHERE attempt_id = %s", (attempt_id,))
    answers_map = {}
    for r in rows:
        answers_map[r['question_id']] = r
    return answers_map

