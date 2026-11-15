import logging
import uuid
from datetime import datetime
from database.connection import query_db, execute_commit

logger = logging.getLogger('exampro.models.result')

def get_result_by_id(result_id):
    """Retrieve result record with exam and student info."""
    sql = """
        SELECT r.*, e.title as exam_title, e.exam_code, e.passing_percentage, e.duration_minutes,
               s.subject_name, s.subject_code, stu.student_id as student_code, u.full_name as student_name,
               u.email as student_email, c.id as certificate_id, c.certificate_code
        FROM results r
        JOIN exams e ON r.exam_id = e.id
        JOIN subjects s ON e.subject_id = s.id
        JOIN students stu ON r.student_id = stu.id
        JOIN users u ON stu.user_id = u.id
        LEFT JOIN certificates c ON r.id = c.result_id
        WHERE r.id = %s
    """
    return query_db(sql, (result_id,), one=True)

def get_result_by_attempt_id(attempt_id):
    """Retrieve result linked to an attempt."""
    sql = """
        SELECT r.*, e.title as exam_title, e.exam_code, e.passing_percentage,
               s.subject_name, stu.student_id as student_code, u.full_name as student_name,
               c.certificate_code
        FROM results r
        JOIN exams e ON r.exam_id = e.id
        JOIN subjects s ON e.subject_id = s.id
        JOIN students stu ON r.student_id = stu.id
        JOIN users u ON stu.user_id = u.id
        LEFT JOIN certificates c ON r.id = c.result_id
        WHERE r.attempt_id = %s
    """
    return query_db(sql, (attempt_id,), one=True)

def get_student_results(student_id):
    """Retrieve all results for a student ordered by newest first."""
    sql = """
        SELECT r.*, e.title as exam_title, e.exam_code, s.subject_name,
               c.id as certificate_id, c.certificate_code
        FROM results r
        JOIN exams e ON r.exam_id = e.id
        JOIN subjects s ON e.subject_id = s.id
        LEFT JOIN certificates c ON r.id = c.result_id
        WHERE r.student_id = %s
        ORDER BY r.published_at DESC
    """
    return query_db(sql, (student_id,))

def get_all_results(search=None, status=None, limit=100, offset=0):
    """Retrieve global results list for admin/teachers."""
    sql = """
        SELECT r.*, e.title as exam_title, e.exam_code, s.subject_name,
               stu.student_id as student_code, u.full_name as student_name, u.email as student_email,
               c.certificate_code
        FROM results r
        JOIN exams e ON r.exam_id = e.id
        JOIN subjects s ON e.subject_id = s.id
        JOIN students stu ON r.student_id = stu.id
        JOIN users u ON stu.user_id = u.id
        WHERE 1=1
    """
    params = []
    if search:
        p = f"%{search.strip()}%"
        sql += " AND (u.full_name LIKE %s OR stu.student_id LIKE %s OR e.title LIKE %s)"
        params.extend([p, p, p])
    if status and status != 'all':
        sql += " AND r.status = %s"
        params.append(status)

    sql += " ORDER BY r.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return query_db(sql, tuple(params))

def get_result_detailed_breakdown(result_id):
    """
    Returns full question-by-question review data:
    question text, chosen answer, correct answer, explanation, marks obtained, status.
    """
    result = get_result_by_id(result_id)
    if not result:
        return None, []

    sql = """
        SELECT q.id as question_id, q.question_text, q.question_type, q.difficulty,
               q.topic, q.explanation, q.image_url,
               eq.marks as max_marks, eq.negative_marks,
               a.selected_option_ids, a.text_answer, a.is_correct, a.marks_awarded,
               a.is_marked_for_review, a.is_answered, a.time_spent_seconds
        FROM exam_questions eq
        JOIN questions q ON eq.question_id = q.id
        LEFT JOIN answers a ON (a.question_id = q.id AND a.attempt_id = %s)
        WHERE eq.exam_id = %s
        ORDER BY eq.question_order ASC
    """
    questions = query_db(sql, (result['attempt_id'], result['exam_id']))

    # Attach all options for each question to render student choice vs correct answer
    for q in questions:
        options = query_db("SELECT * FROM question_options WHERE question_id = %s ORDER BY option_order ASC", (q['question_id'],))
        q['options'] = options
        
        # Parse selected option ids into set
        selected_set = set()
        if q['selected_option_ids']:
            selected_set = set(str(q['selected_option_ids']).split(','))
        q['selected_set'] = selected_set

    return result, questions

def get_certificate_by_code(code):
    """Find certificate by its unique code."""
    sql = """
        SELECT c.*, r.score, r.total_marks, r.percentage as result_percentage, r.grade as result_grade,
               e.title as exam_title, e.exam_code, s.subject_name,
               stu.student_id as student_code, u.full_name as student_name, u.email as student_email
        FROM certificates c
        JOIN results r ON c.result_id = r.id
        JOIN exams e ON c.exam_id = e.id
        JOIN subjects s ON e.subject_id = s.id
        JOIN students stu ON c.student_id = stu.id
        JOIN users u ON stu.user_id = u.id
        WHERE c.certificate_code = %s
    """
    return query_db(sql, (code.strip(),), one=True)

def get_student_certificates(student_id):
    """Retrieve all certificates earned by student."""
    sql = """
        SELECT c.*, e.title as exam_title, s.subject_name, r.score, r.total_marks
        FROM certificates c
        JOIN exams e ON c.exam_id = e.id
        JOIN subjects s ON e.subject_id = s.id
        JOIN results r ON c.result_id = r.id
        WHERE c.student_id = %s AND c.is_valid = 1
        ORDER BY c.issue_date DESC
    """
    return query_db(sql, (student_id,))

