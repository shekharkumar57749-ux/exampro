import logging
from database.connection import query_db

logger = logging.getLogger('exampro.services.analytics')

def get_student_analytics(student_id):
    """
    Computes real analytics and data structures for student dashboard & analytics pages.
    """
    # 1. Overall Metrics
    summary = query_db("""
        SELECT 
            COUNT(r.id) as exams_completed,
            COALESCE(ROUND(AVG(r.percentage), 1), 0.0) as average_percentage,
            COALESCE(ROUND(MAX(r.percentage), 1), 0.0) as best_score,
            COALESCE(SUM(r.correct_count), 0) as total_correct,
            COALESCE(SUM(r.incorrect_count), 0) as total_incorrect,
            COALESCE(SUM(r.skipped_count), 0) as total_skipped,
            COALESCE(ROUND(AVG(r.accuracy), 1), 0.0) as overall_accuracy,
            COALESCE(ROUND(AVG(r.time_taken_seconds), 0), 0) as avg_time_seconds,
            (SELECT COUNT(*) FROM certificates c WHERE c.student_id = %s) as certificates_count
        FROM results r
        WHERE r.student_id = %s
    """, (student_id, student_id), one=True)

    # 2. Performance Over Time (for Chart.js Line Chart)
    timeline_rows = query_db("""
        SELECT r.id, e.title as exam_title, r.percentage, r.grade, r.published_at,
               DATE(r.published_at) as exam_date
        FROM results r
        JOIN exams e ON r.exam_id = e.id
        WHERE r.student_id = %s
        ORDER BY r.published_at ASC
        LIMIT 10
    """, (student_id,))

    chart_timeline = {
        'labels': [row['exam_title'][:15] + ('...' if len(row['exam_title']) > 15 else '') for row in timeline_rows],
        'scores': [float(row['percentage']) for row in timeline_rows],
        'dates': [str(row['exam_date']) for row in timeline_rows]
    }

    # 3. Subject-wise Performance
    subject_rows = query_db("""
        SELECT s.subject_name,
               COUNT(r.id) as attempts,
               ROUND(AVG(r.percentage), 1) as avg_percentage
        FROM results r
        JOIN exams e ON r.exam_id = e.id
        JOIN subjects s ON e.subject_id = s.id
        WHERE r.student_id = %s
        GROUP BY s.id, s.subject_name
        ORDER BY avg_percentage DESC
    """, (student_id,))

    chart_subjects = {
        'labels': [row['subject_name'] for row in subject_rows],
        'scores': [float(row['avg_percentage']) for row in subject_rows]
    }

    # 4. Strengths & Weaknesses (Topic Analysis)
    topic_rows = query_db("""
        SELECT q.topic, s.subject_name,
               COUNT(a.id) as total_questions,
               SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) as correct_questions,
               ROUND(SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(a.id), 1) as accuracy
        FROM answers a
        JOIN questions q ON a.question_id = q.id
        JOIN subjects s ON q.subject_id = s.id
        JOIN exam_attempts ea ON a.attempt_id = ea.id
        WHERE ea.student_id = %s AND a.is_answered = 1
        GROUP BY q.topic, s.subject_name
        ORDER BY accuracy DESC
    """, (student_id,))

    strong_areas = [t for t in topic_rows if float(t['accuracy'] or 0) >= 70.0]
    weak_areas = [t for t in topic_rows if float(t['accuracy'] or 0) < 70.0]

    # 5. Question Type Breakdown
    qtype_rows = query_db("""
        SELECT q.question_type,
               COUNT(a.id) as total,
               SUM(CASE WHEN a.is_correct = 1 THEN 1 ELSE 0 END) as correct
        FROM answers a
        JOIN questions q ON a.question_id = q.id
        JOIN exam_attempts ea ON a.attempt_id = ea.id
        WHERE ea.student_id = %s AND a.is_answered = 1
        GROUP BY q.question_type
    """, (student_id,))

    chart_types = {
        'labels': [r['question_type'].replace('_', ' ').title() for r in qtype_rows],
        'data': [r['total'] for r in qtype_rows]
    }

    return {
        'summary': summary,
        'timeline': chart_timeline,
        'subjects': chart_subjects,
        'strong_areas': strong_areas,
        'weak_areas': weak_areas,
        'qtypes': chart_types
    }

def get_admin_analytics():
    """
    Computes global institutional statistics and Chart.js datasets for Admin dashboard.
    """
    # 1. Key Performance Indicators
    kpis = query_db("""
        SELECT
            (SELECT COUNT(*) FROM students) as total_students,
            (SELECT COUNT(*) FROM teachers) as total_teachers,
            (SELECT COUNT(*) FROM exams WHERE status = 'active') as active_exams,
            (SELECT COUNT(*) FROM exams) as total_exams,
            (SELECT COUNT(*) FROM questions) as total_questions,
            (SELECT COUNT(*) FROM exam_attempts WHERE status IN ('submitted', 'auto_submitted')) as completed_attempts,
            (SELECT COALESCE(ROUND(AVG(percentage), 1), 0.0) FROM results) as average_score,
            (SELECT COUNT(*) FROM certificates WHERE is_valid = 1) as total_certificates
    """, one=True)

    # 2. Grade Distribution (A+, A, B, C, D, E, F)
    grade_rows = query_db("""
        SELECT grade, COUNT(*) as count 
        FROM results 
        GROUP BY grade 
        ORDER BY grade ASC
    """)
    grades_dict = {'A+': 0, 'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0}
    for g in grade_rows:
        if g['grade'] in grades_dict:
            grades_dict[g['grade']] = g['count']

    # 3. Pass vs Fail Ratio
    pass_fail = query_db("""
        SELECT 
            SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) as passed_count,
            SUM(CASE WHEN status = 'fail' THEN 1 ELSE 0 END) as failed_count
        FROM results
    """, one=True)

    # 4. Exam Participation & Performance per Subject
    exam_stats = query_db("""
        SELECT e.id, e.title, s.subject_name,
               COUNT(r.id) as attempts_count,
               COALESCE(ROUND(AVG(r.percentage), 1), 0.0) as avg_score,
               COALESCE(ROUND(AVG(r.accuracy), 1), 0.0) as avg_accuracy,
               SUM(CASE WHEN r.status = 'pass' THEN 1 ELSE 0 END) as pass_count
        FROM exams e
        JOIN subjects s ON e.subject_id = s.id
        LEFT JOIN results r ON e.id = r.exam_id
        GROUP BY e.id, e.title, s.subject_name
        ORDER BY attempts_count DESC
        LIMIT 8
    """)

    # 5. Recent System Activities
    recent_attempts = query_db("""
        SELECT r.id as result_id, r.score, r.percentage, r.grade, r.status, r.published_at,
               e.title as exam_title, u.full_name as student_name, stu.student_id as student_code
        FROM results r
        JOIN exams e ON r.exam_id = e.id
        JOIN students stu ON r.student_id = stu.id
        JOIN users u ON stu.user_id = u.id
        ORDER BY r.id DESC
        LIMIT 6
    """)

    recent_students = query_db("""
        SELECT u.full_name, u.email, u.created_at, s.student_id, s.course
        FROM students s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.id DESC
        LIMIT 5
    """)

    return {
        'kpis': kpis,
        'grades': grades_dict,
        'pass_fail': pass_fail,
        'exam_stats': exam_stats,
        'recent_attempts': recent_attempts,
        'recent_students': recent_students
    }

