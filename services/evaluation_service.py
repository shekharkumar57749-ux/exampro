import logging
import uuid
from datetime import datetime
from database.connection import query_db, execute_commit
from models.exam_model import get_exam_by_id, get_attempt_by_id
from models.notification_model import create_notification
from services.certificate_service import generate_pdf_certificate

logger = logging.getLogger('exampro.services.evaluation')

def calculate_grade(percentage):
    """Determine standard letter grade based on percentage."""
    if percentage >= 90.0:
        return 'A+'
    elif percentage >= 80.0:
        return 'A'
    elif percentage >= 70.0:
        return 'B'
    elif percentage >= 60.0:
        return 'C'
    elif percentage >= 50.0:
        return 'D'
    elif percentage >= 40.0:
        return 'E'
    else:
        return 'F'

def evaluate_exam_submission(attempt_id, is_auto_submit=False):
    """
    Evaluates all answers submitted for an exam attempt:
    - Calculates points for each question based on question type
    - Applies negative marking where configured
    - Tallies correct, incorrect, skipped questions
    - Records final result and triggers certificate if student passed
    """
    attempt = get_attempt_by_id(attempt_id)
    if not attempt:
        raise ValueError(f"Attempt #{attempt_id} not found.")

    exam = get_exam_by_id(attempt['exam_id'])
    student_id = attempt['student_id']

    # Fetch all questions and their configured marks for this exam
    sql_questions = """
        SELECT eq.question_id, eq.marks, eq.negative_marks, q.question_type, q.question_text
        FROM exam_questions eq
        JOIN questions q ON eq.question_id = q.id
        WHERE eq.exam_id = %s
        ORDER BY eq.question_order ASC
    """
    exam_questions = query_db(sql_questions, (exam['id'],))

    # Fetch student answers for this attempt
    sql_answers = "SELECT * FROM answers WHERE attempt_id = %s"
    student_answers_list = query_db(sql_answers, (attempt_id,))
    answers_by_qid = {ans['question_id']: ans for ans in student_answers_list}

    total_possible_marks = 0.0
    total_score_awarded = 0.0
    correct_count = 0
    incorrect_count = 0
    skipped_count = 0

    for eq in exam_questions:
        qid = eq['question_id']
        qtype = eq['question_type']
        q_marks = float(eq['marks'])
        q_neg = float(eq['negative_marks']) if exam['negative_marking'] else 0.0
        total_possible_marks += q_marks

        # Correct options for this question
        correct_opts = query_db("SELECT id, option_text FROM question_options WHERE question_id = %s AND is_correct = 1", (qid,))
        correct_opt_ids = {str(opt['id']) for opt in correct_opts}
        correct_opt_texts = [opt['option_text'].strip().lower() for opt in correct_opts]

        ans = answers_by_qid.get(qid)
        is_correct = False
        marks_for_this = 0.0

        if not ans or not (ans['selected_option_ids'] or ans['text_answer']):
            # Skipped question
            skipped_count += 1
            is_correct = None
            marks_for_this = 0.0
        else:
            if qtype in ('single_choice', 'true_false'):
                selected = str(ans['selected_option_ids']).strip()
                if selected in correct_opt_ids:
                    is_correct = True
                    marks_for_this = q_marks
                    correct_count += 1
                else:
                    is_correct = False
                    marks_for_this = -abs(q_neg)
                    incorrect_count += 1

            elif qtype == 'multiple_choice':
                selected_ids = {s.strip() for s in str(ans['selected_option_ids']).split(',') if s.strip()}
                if selected_ids == correct_opt_ids:
                    is_correct = True
                    marks_for_this = q_marks
                    correct_count += 1
                else:
                    is_correct = False
                    marks_for_this = -abs(q_neg)
                    incorrect_count += 1

            elif qtype == 'fill_blank':
                stu_text = (ans['text_answer'] or '').strip().lower()
                if stu_text and stu_text in correct_opt_texts:
                    is_correct = True
                    marks_for_this = q_marks
                    correct_count += 1
                else:
                    is_correct = False
                    marks_for_this = -abs(q_neg)
                    incorrect_count += 1

            elif qtype == 'descriptive':
                # For automated mock scoring on descriptive answers:
                stu_text = (ans['text_answer'] or '').strip().lower()
                if len(stu_text) > 15:
                    # Non-empty thoughtful response awards base points
                    is_correct = True
                    marks_for_this = q_marks
                    correct_count += 1
                else:
                    is_correct = False
                    marks_for_this = 0.0
                    incorrect_count += 1
            else:
                selected = str(ans['selected_option_ids']).strip()
                if selected in correct_opt_ids:
                    is_correct = True
                    marks_for_this = q_marks
                    correct_count += 1
                else:
                    is_correct = False
                    marks_for_this = -abs(q_neg)
                    incorrect_count += 1

        total_score_awarded += marks_for_this

        # Update answers table with outcome
        if ans:
            execute_commit("""
                UPDATE answers 
                SET is_correct = %s, marks_awarded = %s, is_answered = %s
                WHERE attempt_id = %s AND question_id = %s
            """, (
                1 if is_correct is True else (0 if is_correct is False else None),
                marks_for_this,
                0 if is_correct is None else 1,
                attempt_id, qid
            ))
        else:
            execute_commit("""
                INSERT INTO answers (attempt_id, question_id, is_visited, is_answered, is_correct, marks_awarded)
                VALUES (%s, %s, 1, 0, NULL, 0.0)
            """, (attempt_id, qid))

    # Score should not fall below 0 unless configured
    final_score = max(0.0, round(total_score_awarded, 2))
    total_marks = max(1.0, round(total_possible_marks, 2))
    percentage = round((final_score / total_marks) * 100.0, 2)
    passed = percentage >= float(exam['passing_percentage'])
    grade = calculate_grade(percentage)
    status_str = 'pass' if passed else 'fail'

    attempt_status = 'auto_submitted' if is_auto_submit else 'submitted'
    
    # Calculate time spent
    submit_time = datetime.now()
    start_time = attempt['start_time']
    time_spent_secs = 0
    if isinstance(start_time, str):
        try:
            start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            time_spent_secs = int((submit_time - start_dt).total_seconds())
        except Exception:
            time_spent_secs = exam['duration_minutes'] * 60
    elif isinstance(start_time, datetime):
        time_spent_secs = int((submit_time - start_time).total_seconds())
    
    time_spent_secs = min(time_spent_secs, exam['duration_minutes'] * 60)

    # 1. Update Attempt
    execute_commit("""
        UPDATE exam_attempts 
        SET submit_time = %s, time_spent_seconds = %s, status = %s,
            total_score = %s, percentage = %s, passed = %s
        WHERE id = %s
    """, (submit_time.strftime('%Y-%m-%d %H:%M:%S'), time_spent_secs, attempt_status, final_score, percentage, 1 if passed else 0, attempt_id))

    # 2. Insert or Update Results
    total_answered = correct_count + incorrect_count
    accuracy = round((correct_count / total_answered * 100.0), 2) if total_answered > 0 else 0.0

    feedback_text = (
        f"Excellent performance! You passed with distinction." if percentage >= 85
        else (f"Well done! You demonstrated solid understanding." if passed
        else f"Did not meet passing criteria ({exam['passing_percentage']}%). Review your mistakes and attempt again.")
    )

    # Check if result row exists
    existing_result = query_db("SELECT id FROM results WHERE attempt_id = %s", (attempt_id,), one=True)
    if existing_result:
        result_id = existing_result['id']
        execute_commit("""
            UPDATE results 
            SET score = %s, total_marks = %s, percentage = %s, grade = %s, status = %s,
                correct_count = %s, incorrect_count = %s, skipped_count = %s, accuracy = %s,
                time_taken_seconds = %s, feedback = %s
            WHERE id = %s
        """, (final_score, total_marks, percentage, grade, status_str, correct_count, incorrect_count, skipped_count, accuracy, time_spent_secs, feedback_text, result_id))
    else:
        result_id = execute_commit("""
            INSERT INTO results (attempt_id, exam_id, student_id, score, total_marks, percentage, grade, status,
                                correct_count, incorrect_count, skipped_count, accuracy, time_taken_seconds, feedback)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (attempt_id, exam['id'], student_id, final_score, total_marks, percentage, grade, status_str, correct_count, incorrect_count, skipped_count, accuracy, time_spent_secs, feedback_text))

    # 3. Generate Certificate if Passed
    if passed:
        existing_cert = query_db("SELECT id FROM certificates WHERE result_id = %s", (result_id,), one=True)
        if not existing_cert:
            cert_code = f"EXAMPRO-{exam['exam_code']}-{uuid.uuid4().hex[:8].upper()}"
            issue_date = datetime.now().strftime('%Y-%m-%d')
            cert_path = f"/static/certificates/cert_{result_id}.pdf"
            
            execute_commit("""
                INSERT INTO certificates (result_id, student_id, exam_id, certificate_code, issue_date, grade, percentage, file_path, is_valid)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
            """, (result_id, student_id, exam['id'], cert_code, issue_date, grade, percentage, cert_path))
            
            # Generate the actual PDF file on disk
            try:
                generate_pdf_certificate(result_id)
            except Exception as e:
                logger.error(f"Failed to generate certificate PDF: {e}")

    # 4. Notify Student
    user_stu = query_db("SELECT user_id FROM students WHERE id = %s", (student_id,), one=True)
    if user_stu:
        create_notification(
            user_id=user_stu['user_id'],
            title=f"Result Published: {exam['title']}",
            message=f"You scored {final_score}/{total_marks} ({percentage}%) with Grade {grade}.",
            notif_type='success' if passed else 'warning',
            link=f"/student/results/{result_id}"
        )

    return result_id

