import logging
from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from routes import role_required
from models.user_model import get_student_profile
from models.exam_model import (
    get_student_available_exams,
    get_exam_by_id,
    create_attempt,
    get_attempt_by_id,
    get_attempt_answers_map
)
from models.question_model import get_questions_for_exam
from models.result_model import (
    get_student_results,
    get_result_by_id,
    get_result_detailed_breakdown,
    get_student_certificates
)
from services.analytics_service import get_student_analytics

logger = logging.getLogger('exampro.routes.student')
student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.before_request
@role_required(['student'])
def enforce_student_role():
    """Ensure student session and table ID are loaded."""
    if 'student_table_id' not in session:
        stu = get_student_profile(session['user_id'])
        if stu:
            session['student_table_id'] = stu['student_table_id']
            session['student_id'] = stu['student_id']
            session['course'] = stu['course']

@student_bp.route('/dashboard')
def dashboard():
    """Student central command dashboard."""
    student_id = session.get('student_table_id')
    profile = get_student_profile(session['user_id'])
    
    # Real database statistics and analytics
    analytics_data = get_student_analytics(student_id)
    summary = analytics_data['summary']

    # Available and upcoming examinations
    available_exams = get_student_available_exams(student_id)
    
    # Recent results
    recent_results = get_student_results(student_id)[:5]

    # Greeting based on local time
    hour = datetime.now().hour
    greeting = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 18 else "Good Evening")

    return render_template(
        'student/dashboard.html',
        profile=profile,
        summary=summary,
        available_exams=available_exams,
        recent_results=recent_results,
        greeting=greeting,
        analytics=analytics_data
    )

@student_bp.route('/exams')
def exams():
    """List of all examinations available to this student."""
    student_id = session.get('student_table_id')
    all_exams = get_student_available_exams(student_id)
    return render_template('student/exams.html', exams=all_exams)

@student_bp.route('/exam/<int:exam_id>/take')
def take_exam(exam_id):
    """
    Dedicated, distraction-free examination screen:
    Loads questions, existing answer draft, and countdown timer.
    """
    student_id = session.get('student_table_id')
    exam = get_exam_by_id(exam_id)
    if not exam:
        flash('Examination not found.', 'danger')
        return redirect(url_for('student.exams'))

    if exam['status'] != 'active':
        flash('This examination is currently not active or has concluded.', 'warning')
        return redirect(url_for('student.exams'))

    # Check or create attempt
    try:
        attempt_id = create_attempt(
            exam_id=exam_id,
            student_id=student_id,
            ip_address=request.remote_addr,
            browser_agent=request.user_agent.string
        )
    except ValueError as ve:
        flash(str(ve), 'danger')
        return redirect(url_for('student.exams'))

    attempt = get_attempt_by_id(attempt_id)
    if attempt['status'] in ('submitted', 'auto_submitted'):
        flash('You have already submitted this examination attempt.', 'info')
        return redirect(url_for('student.results'))

    # Fetch exam questions with options
    questions = get_questions_for_exam(
        exam_id=exam_id,
        randomize_questions=bool(exam['randomize_questions']),
        randomize_options=bool(exam['randomize_options'])
    )

    # Fetch any already saved answers for this attempt (state recovery)
    answers_map = get_attempt_answers_map(attempt_id)

    # Calculate remaining seconds on countdown timer
    now = datetime.now()
    start_time = attempt['start_time']
    if isinstance(start_time, str):
        try:
            start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        except Exception:
            start_dt = now
    else:
        start_dt = start_time

    elapsed_seconds = int((now - start_dt).total_seconds())
    total_seconds = exam['duration_minutes'] * 60
    remaining_seconds = max(0, total_seconds - elapsed_seconds)

    # Map question states for palette:
    # 'not_visited', 'visited', 'answered', 'review', 'unanswered'
    palette_states = {}
    for q in questions:
        qid = q['id']
        ans = answers_map.get(qid)
        if not ans:
            palette_states[qid] = 'not_visited'
        elif ans['is_marked_for_review']:
            palette_states[qid] = 'review'
        elif ans['is_answered']:
            palette_states[qid] = 'answered'
        elif ans['is_visited']:
            palette_states[qid] = 'unanswered'
        else:
            palette_states[qid] = 'not_visited'

    return render_template(
        'student/examination.html',
        exam=exam,
        attempt=attempt,
        questions=questions,
        answers_map=answers_map,
        palette_states=palette_states,
        remaining_seconds=remaining_seconds
    )

@student_bp.route('/results')
def results():
    """List of all examination results for this student."""
    student_id = session.get('student_table_id')
    student_results = get_student_results(student_id)
    return render_template('student/results.html', results=student_results)

@student_bp.route('/results/<int:result_id>')
def result_detail(result_id):
    """Detailed score report and question breakdown."""
    student_id = session.get('student_table_id')
    result, questions = get_result_detailed_breakdown(result_id)
    
    if not result:
        flash('Result not found.', 'danger')
        return redirect(url_for('student.results'))

    if result['student_id'] != student_id and session.get('role') != 'admin':
        flash('Unauthorized access to result.', 'danger')
        return redirect(url_for('student.results'))

    return render_template('student/result_detail.html', result=result, questions=questions)

@student_bp.route('/analytics')
def analytics():
    """Dedicated student performance analytics page."""
    student_id = session.get('student_table_id')
    data = get_student_analytics(student_id)
    profile = get_student_profile(session['user_id'])
    return render_template('student/analytics.html', analytics=data, profile=profile)

@student_bp.route('/certificates')
def certificates():
    """View and download earned certificates."""
    student_id = session.get('student_table_id')
    certs = get_student_certificates(student_id)
    return render_template('student/certificates.html', certificates=certs)

@student_bp.route('/profile')
def profile():
    """Student profile view."""
    profile_data = get_student_profile(session['user_id'])
    return render_template('student/profile.html', profile=profile_data)

@student_bp.route('/settings')
def settings():
    """Student settings page."""
    profile_data = get_student_profile(session['user_id'])
    return render_template('student/settings.html', profile=profile_data)

