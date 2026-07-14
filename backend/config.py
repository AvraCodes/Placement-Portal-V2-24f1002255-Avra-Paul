import os

# Base directory represents the absolute path to the 'backend' folder.
# This helps locate the SQLite database file and file upload/export directories.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # SECRET_KEY is used by Flask for securely signing session cookies and tokens.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ppa-secret-key-2024')

    # SQLite Database URI: pointing to ppa.db located in the backend directory.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'ppa.db')
    # Track modifications is disabled to reduce overhead and improve performance.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration: Used to sign access tokens for secure client-server API requests.
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'ppa-jwt-secret-2024')
    # Access token valid for 24 hours (defined in seconds).
    JWT_ACCESS_TOKEN_EXPIRES = 86400

    # Flask-Caching via Redis: stores temporary cache entries on database 0 of Redis.
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/0')
    # Default cache lifespan: 60 seconds.
    CACHE_DEFAULT_TIMEOUT = 60

    # Celery configuration: specifies the Redis broker and backend using Redis database 1.
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

    # Mail configuration: details for SMTP server configuration to send emails.
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@ppa.com')

    # File uploads: paths to folders storing student resumes and generated CSV reports.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')
    # Restrict file uploads to a maximum size of 5 MB.
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # Default admin credentials created automatically on application start.
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'
    ADMIN_EMAIL = 'admin@placement.com'

