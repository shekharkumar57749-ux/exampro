import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from routes import role_required
from models.user_model import (
    get_all_students,
    get_all_teachers,
    toggle_user_status,
    create_student,
    create_teacher
)
from models.exam_model import get_all_exams, get_subjects, get_courses
from models.question_model import get_all_questions
from models.result_model import get_all_results
from models.notification_model import get_security_logs
from services.analytics_service import get_admin_analytics

logger = logging.getLogger('exampro.routes.admin')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@role_required(['admin'])
def admin_auth():
    pass

@admin_bp.route('/dashboard')
def dashboard():
    """Institutional administration overview with live metrics and charts."""
    analytics_data = get_admin_analytics()
    return render_template('admin/dashboard.html', analytics=analytics_data)

@admin_bp.route('/students')
def students():
    """Manage enrolled students."""
    search = request.args.get('search')
    status = request.args.get('status')
    students_list = get_all_students(search=search, status=status)
    courses = get_courses()
    return render_template(
        'admin/students.html',
        students=students_list,
        courses=courses,
        search_query=search,
        status_filter=status
    )

@admin_bp.route('/students/create', methods=['POST'])
def student_create():
    """Create student manually from admin interface."""
    data = request.form
    try:
        email = data.get('email', '').strip()
        username = email.split('@')[0]
        create_student(
            username=username,
            email=email,
            password=data.get('password', 'Student@123'),
            full_name=data.get('full_name', '').strip(),
            phone=data.get('phone', '').strip(),
            student_id=data.get('student_id', '').strip(),
            course=data.get('course', 'B.Tech Computer Science').strip(),
            college=data.get('college', 'Institute of Technology & Science').strip()
        )
        flash('Student account registered successfully.', 'success')
    except Exception as e:
        flash(f"Error registering student: {e}", 'danger')
    return redirect(url_for('admin.students'))

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
def user_toggle_status(user_id):
    """Enable or disable student or teacher account."""
    new_status = request.form.get('status', 'active')
    try:
        toggle_user_status(user_id, new_status)
        flash(f"Account status updated to {new_status}.", 'success')
    except Exception as e:
        flash(f"Status update failed: {e}", 'danger')
    
    referrer = request.referrer or url_for('admin.students')
    return redirect(referrer)

@admin_bp.route('/teachers')
def teachers():
    """Manage faculty and educators."""
    search = request.args.get('search')
    teachers_list = get_all_teachers(search=search)
    return render_template('admin/teachers.html', teachers=teachers_list, search_query=search)

@admin_bp.route('/teachers/create', methods=['POST'])
def teacher_create():
    """Add a new faculty member."""
    data = request.form
    try:
        email = data.get('email', '').strip()
        username = email.split('@')[0]
        create_teacher(
            username=username,
            email=email,
            password=data.get('password', 'Teacher@123'),
            full_name=data.get('full_name', '').strip(),
            phone=data.get('phone', '').strip(),
            employee_id=data.get('employee_id', '').strip(),
            department=data.get('department', 'Computer Science').strip(),
            designation=data.get('designation', 'Assistant Professor').strip(),
            assigned_subjects=data.get('assigned_subjects', '').strip()
        )
        flash('Faculty account created successfully.', 'success')
    except Exception as e:
        flash(f"Error adding faculty: {e}", 'danger')
    return redirect(url_for('admin.teachers'))

@admin_bp.route('/exams')
def exams():
    """Manage institutional exams."""
    search = request.args.get('search')
    status = request.args.get('status')
    exams_list = get_all_exams(status=status, search=search)
    return render_template('admin/exams.html', exams=exams_list, search_query=search, status_filter=status)

@admin_bp.route('/exams/create')
def exam_create():
    """Step-by-step examination builder."""
    subjects = get_subjects()
    questions = get_all_questions(limit=300)
    return render_template('admin/exam_create.html', subjects=subjects, questions=questions)

@admin_bp.route('/question-bank')
def question_bank():
    """Institutional question bank."""
    subject_id = request.args.get('subject_id')
    difficulty = request.args.get('difficulty')
    qtype = request.args.get('qtype')
    search = request.args.get('search')

    all_q = get_all_questions(subject_id=subject_id, difficulty=difficulty, qtype=qtype, search=search)
    subjects = get_subjects()

    return render_template(
        'admin/question_bank.html',
        questions=all_q,
        subjects=subjects,
        selected_subject=subject_id,
        selected_difficulty=difficulty,
        selected_type=qtype,
        search_query=search
    )

@admin_bp.route('/results')
def results():
    """All examination results."""
    search = request.args.get('search')
    status = request.args.get('status')
    results_list = get_all_results(search=search, status=status)
    return render_template('admin/results.html', results=results_list, search_query=search, status_filter=status)

@admin_bp.route('/analytics')
def analytics():
    """Global institutional performance metrics."""
    data = get_admin_analytics()
    return render_template('admin/analytics.html', analytics=data)

@admin_bp.route('/security-logs')
def security_logs():
    """Examination proctoring and audit trail logs."""
    logs = get_security_logs(limit=150)
    return render_template('admin/security_logs.html', logs=logs)

@admin_bp.route('/settings')
def settings():
    """Global system configuration."""
    return render_template('admin/settings.html')

