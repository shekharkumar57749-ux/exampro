import logging
import json
from flask import Blueprint, request, jsonify, session
from routes import login_required, role_required
from models.exam_model import (
    get_exam_by_id,
    get_attempt_by_id,
    save_answer,
    create_exam,
    update_exam,
    delete_exam
)
from models.question_model import attach_questions_to_exam
from models.notification_model import log_security_event
from services.evaluation_service import evaluate_exam_submission

logger = logging.getLogger('exampro.routes.exam')
exam_bp = Blueprint('exam', __name__)

@exam_bp.route('/api/exam/attempt/<int:attempt_id>/save-answer', methods=['POST'])
@login_required
def api_save_answer(attempt_id):
    """
    Saves or updates a candidate's answer to the backend database in real time.
    Called whenever candidate selects an option, types, or navigates between questions.
    """
    attempt = get_attempt_by_id(attempt_id)
    if not attempt:
        return jsonify({'success': False, 'error': 'Invalid examination attempt'}), 404

    # Security check: verify this attempt belongs to the logged-in student
    student_id = session.get('student_table_id')
    if attempt['student_id'] != student_id and session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    if attempt['status'] in ('submitted', 'auto_submitted', 'disqualified'):
        return jsonify({'success': False, 'error': 'Attempt has already concluded and is locked'}), 400

    data = request.json or request.form
    question_id = data.get('question_id')
    selected_option_ids = data.get('selected_option_ids') # comma-separated string or list
    text_answer = data.get('text_answer')
    is_marked_for_review = bool(data.get('is_marked_for_review', False))
    is_visited = bool(data.get('is_visited', True))
    time_spent = int(data.get('time_spent_seconds', 0))

    if isinstance(selected_option_ids, list):
        selected_option_ids = ','.join(str(x) for x in selected_option_ids)

    try:
        save_answer(
            attempt_id=attempt_id,
            question_id=int(question_id),
            selected_option_ids=selected_option_ids,
            text_answer=text_answer,
            is_marked_for_review=is_marked_for_review,
            is_visited=is_visited,
            time_spent_seconds=time_spent
        )
        return jsonify({'success': True, 'saved_at': 'Saved to cloud'})
    except Exception as e:
        logger.error(f"Error saving answer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@exam_bp.route('/api/exam/attempt/<int:attempt_id>/submit', methods=['POST'])
@login_required
def api_submit_exam(attempt_id):
    """
    Finalizes the examination attempt:
    - Stops timer and locks further answer editing
    - Performs server-side automated evaluation
    - Computes score, negative marking, percentage, and grade
    - Returns result ID for instant redirection
    """
    attempt = get_attempt_by_id(attempt_id)
    if not attempt:
        return jsonify({'success': False, 'error': 'Invalid examination attempt'}), 404

    student_id = session.get('student_table_id')
    if attempt['student_id'] != student_id and session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    if attempt['status'] in ('submitted', 'auto_submitted'):
        return jsonify({'success': False, 'error': 'Examination already submitted', 'redirect_url': '/student/results'}), 200

    data = request.json or {}
    is_auto = bool(data.get('is_auto_submit', False))

    try:
        result_id = evaluate_exam_submission(attempt_id, is_auto_submit=is_auto)
        return jsonify({
            'success': True,
            'message': 'Examination submitted and evaluated successfully!',
            'result_id': result_id,
            'redirect_url': f'/student/results/{result_id}'
        })
    except Exception as e:
        logger.error(f"Error during submission evaluation: {e}")
        return jsonify({'success': False, 'error': f"Evaluation error: {str(e)}"}), 500

@exam_bp.route('/api/exam/attempt/<int:attempt_id>/log-security', methods=['POST'])
@login_required
def api_log_security(attempt_id):
    """
    Records proctoring and security incidents (tab switch, window blur, fullscreen exit, copy/paste).
    """
    attempt = get_attempt_by_id(attempt_id)
    if not attempt:
        return jsonify({'success': False, 'error': 'Invalid attempt'}), 404

    data = request.json or {}
    event_type = data.get('event_type', 'unknown')
    details = data.get('details', '')
    severity = data.get('severity', 'medium')

    try:
        log_security_event(
            attempt_id=attempt_id,
            student_id=attempt['student_id'],
            exam_id=attempt['exam_id'],
            event_type=event_type,
            details=details,
            severity=severity
        )
        return jsonify({'success': True, 'logged': True})
    except Exception as e:
        logger.error(f"Error logging security event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# --- Exam Management CRUD APIs (Admin & Teacher) ---

@exam_bp.route('/api/exams/create', methods=['POST'])
@login_required
@role_required(['admin', 'teacher'])
def api_create_exam():
    """Create a new exam with questions."""
    data = request.json or request.form
    try:
        exam_data = {
            'title': data.get('title'),
            'exam_code': data.get('exam_code'),
            'subject_id': int(data.get('subject_id')),
            'created_by': session['user_id'],
            'description': data.get('description', ''),
            'instructions': data.get('instructions', ''),
            'duration_minutes': int(data.get('duration_minutes', 60)),
            'total_marks': float(data.get('total_marks', 100)),
            'passing_percentage': float(data.get('passing_percentage', 40)),
            'start_time': data.get('start_time'),
            'end_time': data.get('end_time'),
            'status': data.get('status', 'active'),
            'randomize_questions': bool(data.get('randomize_questions')),
            'randomize_options': bool(data.get('randomize_options')),
            'negative_marking': bool(data.get('negative_marking')),
            'negative_mark_value': float(data.get('negative_mark_value', 0.25)),
            'max_attempts': int(data.get('max_attempts', 1)),
            'result_release_mode': data.get('result_release_mode', 'immediate')
        }
        
        exam_id = create_exam(exam_data)
        
        # Link questions if provided
        question_ids = data.get('question_ids', [])
        if isinstance(question_ids, str):
            question_ids = [int(q.strip()) for q in question_ids.split(',') if q.strip()]
        if question_ids:
            attach_questions_to_exam(exam_id, question_ids)

        return jsonify({'success': True, 'exam_id': exam_id, 'message': 'Examination created successfully'})
    except Exception as e:
        logger.error(f"Exam creation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@exam_bp.route('/api/exams/<int:exam_id>/delete', methods=['POST'])
@login_required
@role_required(['admin', 'teacher'])
def api_delete_exam(exam_id):
    """Delete an exam."""
    try:
        delete_exam(exam_id)
        return jsonify({'success': True, 'message': 'Exam deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

