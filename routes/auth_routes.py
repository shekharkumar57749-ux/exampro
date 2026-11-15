import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash
from models.user_model import (
    get_user_by_username_or_email,
    get_user_by_id,
    create_student,
    get_student_profile,
    update_user_profile,
    update_student_academic,
    change_password
)
from models.notification_model import get_user_notifications, get_unread_count, mark_as_read, mark_all_as_read
from routes import login_required

logger = logging.getLogger('exampro.routes.auth')
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Student registration page and submission handler."""
    if 'user_id' in session:
        return redirect_role_dashboard(session.get('role'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        student_id = request.form.get('student_id', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        course = request.form.get('course', 'B.Tech Computer Science').strip()
        college = request.form.get('college', 'Institute of Technology & Science').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        if not full_name or not student_id or not email or not password:
            flash('All required fields must be completed.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match. Please re-enter.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must contain at least 6 characters.', 'danger')
            return render_template('auth/register.html')

        username = email.split('@')[0]
        try:
            create_student(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                phone=phone,
                student_id=student_id,
                course=course,
                college=college
            )
            flash('Registration successful! Please log in with your credentials.', 'success')
            return redirect(url_for('auth.student_login'))
        except ValueError as ve:
            flash(str(ve), 'danger')
            return render_template('auth/register.html')
        except Exception as e:
            logger.error(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register.html')

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/auth/student-login', methods=['GET', 'POST'])
def student_login():
    """Student login view and authentication handler."""
    if 'user_id' in session:
        return redirect_role_dashboard(session.get('role'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not identifier or not password:
            flash('Please enter your email or Student ID and password.', 'danger')
            return render_template('auth/student_login.html')

        user = get_user_by_username_or_email(identifier)
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid login credentials. Please verify your details.', 'danger')
            return render_template('auth/student_login.html')

        if user['status'] != 'active':
            flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            return render_template('auth/student_login.html')

        # Set session
        set_user_session(user, remember)
        flash(f"Welcome back, {user['full_name']}!", 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect_role_dashboard(user['role'])

    return render_template('auth/student_login.html')

@auth_bp.route('/auth/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Administrator portal login view."""
    if 'user_id' in session and session.get('role') == 'admin':
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        admin_code = request.form.get('admin_code', '').strip()

        user = get_user_by_username_or_email(identifier)
        if not user or user['role'] != 'admin' or not check_password_hash(user['password_hash'], password):
            flash('Invalid administrator credentials.', 'danger')
            return render_template('auth/admin_login.html')

        set_user_session(user, remember=False)
        flash(f"Administrator access granted. Welcome, {user['full_name']}.", 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('auth/admin_login.html')

@auth_bp.route('/auth/teacher-login', methods=['GET', 'POST'])
def teacher_login():
    """Educator / Teacher login view."""
    if 'user_id' in session and session.get('role') == 'teacher':
        return redirect(url_for('teacher.dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        user = get_user_by_username_or_email(identifier)
        if not user or user['role'] != 'teacher' or not check_password_hash(user['password_hash'], password):
            flash('Invalid educator credentials. Please check your email or employee ID.', 'danger')
            return render_template('auth/teacher_login.html')

        set_user_session(user, remember=False)
        flash(f"Welcome, {user['full_name']}!", 'success')
        return redirect(url_for('teacher.dashboard'))

    return render_template('auth/teacher_login.html')

@auth_bp.route('/logout')
def logout():
    """Clears user session and redirects to landing page."""
    session.clear()
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('landing'))

# --- Helper APIs for In-App Notifications ---

@auth_bp.route('/api/notifications')
@login_required
def api_get_notifications():
    """Fetch recent notifications and unread count."""
    notifs = get_user_notifications(session['user_id'], limit=10)
    unread_count = get_unread_count(session['user_id'])
    return jsonify({
        'success': True,
        'unread_count': unread_count,
        'notifications': notifs
    })

@auth_bp.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def api_mark_notification_read(notif_id):
    """Mark a notification as read."""
    mark_as_read(notif_id, session['user_id'])
    return jsonify({'success': True})

@auth_bp.route('/api/notifications/read-all', methods=['POST'])
@login_required
def api_mark_all_read():
    """Mark all user notifications as read."""
    mark_all_as_read(session['user_id'])
    return jsonify({'success': True})

# --- Profile and Password update helper ---

@auth_bp.route('/api/profile/update', methods=['POST'])
@login_required
def api_update_profile():
    """Update user contact and academic info."""
    data = request.json or request.form
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    
    if not full_name:
        return jsonify({'success': False, 'error': 'Full name is required'}), 400

    update_user_profile(session['user_id'], full_name, phone)
    session['full_name'] = full_name

    if session.get('role') == 'student':
        course = data.get('course', '').strip()
        college = data.get('college', '').strip()
        semester = int(data.get('semester', 1))
        update_student_academic(session['user_id'], course, college, semester)

    return jsonify({'success': True, 'message': 'Profile updated successfully'})

@auth_bp.route('/api/profile/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Change account password securely."""
    data = request.json or request.form
    old_pwd = data.get('old_password', '')
    new_pwd = data.get('new_password', '')
    
    if len(new_pwd) < 6:
        return jsonify({'success': False, 'error': 'New password must be at least 6 characters'}), 400

    try:
        change_password(session['user_id'], old_pwd, new_pwd)
        return jsonify({'success': True, 'message': 'Password updated successfully'})
    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400

def set_user_session(user, remember=False):
    """Stores user information in encrypted session."""
    session.permanent = remember
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['email'] = user['email']
    session['full_name'] = user['full_name']
    session['role'] = user['role']
    session['avatar_url'] = user.get('avatar_url', '/static/images/default-avatar.png')
    
    # Store student/teacher specific identifiers
    if user['role'] == 'student':
        stu = get_student_profile(user['id'])
        if stu:
            session['student_table_id'] = stu['student_table_id']
            session['student_id'] = stu['student_id']
            session['course'] = stu['course']
    elif user['role'] == 'teacher':
        session['employee_id'] = user.get('employee_id', '')

def redirect_role_dashboard(role):
    """Direct user to their designated dashboard."""
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher.dashboard'))
    else:
        return redirect(url_for('student.dashboard'))

