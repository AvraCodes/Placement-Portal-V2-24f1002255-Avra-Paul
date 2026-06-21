"""
Configuration file for the Placement Portal Application.
Contains all settings for Flask, SQLite, Redis, Celery, and Mail.
"""
import os

# Base directory of the backend folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Main configuration class. All settings are defined here."""

    # --- Flask Settings ---
    SECRET_KEY = os.environ.get('SECRET_KEY', 'placement-portal-secret-key-change-in-production')
    DEBUG = True

    # --- SQLite Database ---
    # Database file is stored in the backend folder
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'placement_portal.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable event tracking to save memory

    # --- JWT (JSON Web Token) Settings ---
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # Token expires in 24 hours (in seconds)

    # --- Redis Cache Settings ---
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 60  # Default cache expiry: 60 seconds

    # --- Celery Settings ---
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

    # --- Mail Settings (for sending reminders and reports) ---
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')  # Set your email here
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')  # Set your app password here
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@placement.com')

    # --- File Upload Settings ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Max upload size: 5 MB

    # --- Admin Credentials (created on first run) ---
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'
    ADMIN_EMAIL = 'admin@placement.com'
