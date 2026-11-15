from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify

def login_required(f):
    """Decorator to enforce user authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.student_login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Decorator to enforce role-based authorization (e.g. admin, teacher, student)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Authentication required'}), 401
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('auth.student_login'))
            
            user_role = session.get('role')
            if user_role not in allowed_roles:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'error': 'Unauthorized access'}), 403
                flash('You do not have permission to access that resource.', 'danger')
                
                # Redirect to appropriate dashboard
                if user_role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif user_role == 'teacher':
                    return redirect(url_for('teacher.dashboard'))
                else:
                    return redirect(url_for('student.dashboard'))
                    
            return f(*args, **kwargs)
        return decorated_function
    return decorator

