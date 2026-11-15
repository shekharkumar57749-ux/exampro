import random
import logging
from database.connection import query_db, execute_commit

logger = logging.getLogger('exampro.models.question')

def get_all_questions(subject_id=None, topic=None, difficulty=None, qtype=None, search=None, limit=100, offset=0):
    """Retrieve filtered list of questions with subject details."""
    sql = """
        SELECT q.*, s.subject_name, s.subject_code, u.full_name as author_name,
               (SELECT COUNT(*) FROM question_options qo WHERE qo.question_id = q.id) as option_count
        FROM questions q
        JOIN subjects s ON q.subject_id = s.id
        LEFT JOIN users u ON q.created_by = u.id
        WHERE 1=1
    """
    params = []
    if subject_id and subject_id != 'all':
        sql += " AND q.subject_id = %s"
        params.append(subject_id)
    if topic and topic != 'all':
        sql += " AND q.topic = %s"
        params.append(topic)
    if difficulty and difficulty != 'all':
        sql += " AND q.difficulty = %s"
        params.append(difficulty)
    if qtype and qtype != 'all':
        sql += " AND q.question_type = %s"
        params.append(qtype)
    if search:
        p = f"%{search.strip()}%"
        sql += " AND (q.question_text LIKE %s OR q.topic LIKE %s OR s.subject_name LIKE %s)"
        params.extend([p, p, p])

    sql += " ORDER BY q.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    return query_db(sql, tuple(params))

def get_question_by_id(question_id):
    """Retrieve question with its options."""
    q = query_db("""
        SELECT q.*, s.subject_name, s.subject_code, u.full_name as author_name
        FROM questions q
        JOIN subjects s ON q.subject_id = s.id
        LEFT JOIN users u ON q.created_by = u.id
        WHERE q.id = %s
    """, (question_id,), one=True)
    if not q:
        return None
    
    options = query_db("""
        SELECT * FROM question_options 
        WHERE question_id = %s 
        ORDER BY option_order ASC, id ASC
    """, (question_id,))
    q['options'] = options
    return q

def create_question(data, options=None):
    """
    Insert question and its options into DB.
    options: list of dicts [{'text': '...', 'is_correct': True/False, 'order': 1}, ...]
    """
    sql = """
        INSERT INTO questions (subject_id, topic, question_text, question_type, difficulty, marks, negative_marks, explanation, image_url, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        data.get('subject_id'),
        data.get('topic', 'General'),
        data.get('question_text'),
        data.get('question_type', 'single_choice'),
        data.get('difficulty', 'medium'),
        float(data.get('marks', 1.0)),
        float(data.get('negative_marks', 0.0)),
        data.get('explanation', ''),
        data.get('image_url', None),
        data.get('created_by')
    )
    question_id = execute_commit(sql, params)

    if options:
        for idx, opt in enumerate(options):
            execute_commit("""
                INSERT INTO question_options (question_id, option_text, is_correct, option_order)
                VALUES (%s, %s, %s, %s)
            """, (question_id, opt.get('text', '').strip(), 1 if opt.get('is_correct') else 0, opt.get('order', idx + 1)))

    return question_id

def update_question(question_id, data, options=None):
    """Update question content and replace its options."""
    sql = """
        UPDATE questions 
        SET subject_id = %s, topic = %s, question_text = %s, question_type = %s,
            difficulty = %s, marks = %s, negative_marks = %s, explanation = %s, image_url = %s
        WHERE id = %s
    """
    params = (
        data.get('subject_id'),
        data.get('topic', 'General'),
        data.get('question_text'),
        data.get('question_type', 'single_choice'),
        data.get('difficulty', 'medium'),
        float(data.get('marks', 1.0)),
        float(data.get('negative_marks', 0.0)),
        data.get('explanation', ''),
        data.get('image_url', None),
        question_id
    )
    execute_commit(sql, params)

    if options is not None:
        execute_commit("DELETE FROM question_options WHERE question_id = %s", (question_id,))
        for idx, opt in enumerate(options):
            execute_commit("""
                INSERT INTO question_options (question_id, option_text, is_correct, option_order)
                VALUES (%s, %s, %s, %s)
            """, (question_id, opt.get('text', '').strip(), 1 if opt.get('is_correct') else 0, opt.get('order', idx + 1)))

    return True

def delete_question(question_id):
    """Delete a question."""
    return execute_commit("DELETE FROM questions WHERE id = %s", (question_id,))

def get_questions_for_exam(exam_id, randomize_questions=False, randomize_options=False):
    """
    Retrieve questions linked to an exam, with their options.
    Honors randomization flags if enabled.
    """
    sql = """
        SELECT q.*, eq.marks as exam_marks, eq.negative_marks as exam_negative_marks, eq.question_order
        FROM exam_questions eq
        JOIN questions q ON eq.question_id = q.id
        WHERE eq.exam_id = %s
        ORDER BY eq.question_order ASC
    """
    questions = query_db(sql, (exam_id,))

    if randomize_questions:
        random.seed()
        random.shuffle(questions)

    for q in questions:
        options = query_db("""
            SELECT id, question_id, option_text, option_order, is_correct
            FROM question_options
            WHERE question_id = %s
            ORDER BY option_order ASC
        """, (q['id'],))
        
        if randomize_options and len(options) > 1:
            opts_list = list(options)
            random.shuffle(opts_list)
            q['options'] = opts_list
        else:
            q['options'] = options

    return questions

def attach_questions_to_exam(exam_id, question_ids):
    """Link multiple question IDs to an exam."""
    execute_commit("DELETE FROM exam_questions WHERE exam_id = %s", (exam_id,))
    total_marks = 0.0
    for order, q_id in enumerate(question_ids, start=1):
        q = query_db("SELECT marks, negative_marks FROM questions WHERE id = %s", (q_id,), one=True)
        marks = q['marks'] if q else 1.0
        neg = q['negative_marks'] if q else 0.0
        total_marks += float(marks)
        execute_commit("""
            INSERT INTO exam_questions (exam_id, question_id, marks, negative_marks, question_order)
            VALUES (%s, %s, %s, %s, %s)
        """, (exam_id, q_id, marks, neg, order))
    
    # Update total_marks in exam
    execute_commit("UPDATE exams SET total_marks = %s WHERE id = %s", (total_marks, exam_id))
    return True

