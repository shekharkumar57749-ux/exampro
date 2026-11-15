import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application Configuration Settings"""
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'exampro-enterprise-secure-key-2026-v1')
    
    # Session Security
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set to True in production HTTPS
    
    # MySQL Database Configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'exampro_db')
    
    # SQLite fallback database file (used if MySQL is not reachable or credentials not set)
    SQLITE_DB_PATH = os.path.join(BASE_DIR, 'database', 'exampro.sqlite')
    
    # File upload and certificate paths
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    CERTIFICATES_FOLDER = os.path.join(BASE_DIR, 'static', 'certificates')
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'static', 'reports')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    
    # Examination Rules Defaults
    DEFAULT_EXAM_DURATION = 60 # minutes
    DEFAULT_PASSING_PERCENTAGE = 40.0
    WARNING_LIMIT = 3 # Tab switch / blur violations limit before auto-alert

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    DB_NAME = 'exampro_test_db'

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
