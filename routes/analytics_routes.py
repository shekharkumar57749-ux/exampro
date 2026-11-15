import logging
from flask import Blueprint, jsonify, session
from routes import login_required, role_required
from services.analytics_service import get_student_analytics, get_admin_analytics

logger = logging.getLogger('exampro.routes.analytics')
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/student')
@login_required
def api_student_analytics():
    """Returns JSON payload of student performance metrics for Chart.js."""
    student_id = session.get('student_table_id')
    if not student_id:
        return jsonify({'success': False, 'error': 'Student profile not associated'}), 400

    data = get_student_analytics(student_id)
    return jsonify({'success': True, 'data': data})

@analytics_bp.route('/admin')
@login_required
@role_required(['admin'])
def api_admin_analytics():
    """Returns JSON payload of administrative statistics for Chart.js."""
    data = get_admin_analytics()
    return jsonify({'success': True, 'data': data})

