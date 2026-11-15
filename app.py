import os
import logging
from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, flash, request

from config import config_by_name, Config
from database.initialize_db import initialize_database
from models.notification_model import get_unread_count

# Configure root logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('exampro')

def create_app(config_name='default'):
    """Application factory for ExamPro platform."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Ensure required runtime storage directories exist
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.CERTIFICATES_FOLDER, exist_ok=True)
    os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(Config.BASE_DIR, 'static', 'images', 'avatars'), exist_ok=True)

    # Initialize database tables and seed records if needed
    try:
        initialize_database()
    except Exception as e:
        logger.error(f"Database auto-initialization error: {e}")

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.student_routes import student_bp
    from routes.teacher_routes import teacher_bp
    from routes.admin_routes import admin_bp
    from routes.exam_routes import exam_bp
    from routes.result_routes import result_bp
    from routes.analytics_routes import analytics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(result_bp)
    app.register_blueprint(analytics_bp)

    # Global Context Processor
    @app.context_processor
    def inject_global_template_data():
        unread_count = 0
        if 'user_id' in session:
            try:
                unread_count = get_unread_count(session['user_id'])
            except Exception:
                unread_count = 0

        return {
            'now': datetime.now(),
            'current_year': datetime.now().year,
            'user_logged_in': 'user_id' in session,
            'user_role': session.get('role'),
            'user_name': session.get('full_name'),
            'user_email': session.get('email'),
            'user_avatar': session.get('avatar_url', '/static/images/default-avatar.png'),
            'unread_notifications_count': unread_count
        }

    # Public Routes
    @app.route('/')
    def landing():
        """Public commercial-grade landing page."""
        return render_template('landing.html')

    @app.route('/about')
    def about():
        """Public about page."""
        return render_template('about.html')

    @app.route('/features')
    def features():
        """Features overview."""
        return render_template('features.html')

    @app.route('/contact')
    def contact():
        """Contact page."""
        return render_template('contact.html')

    # Global Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Internal server error: {e}")
        return render_template('errors/500.html'), 500

    return app

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"ExamPro server starting at http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)

