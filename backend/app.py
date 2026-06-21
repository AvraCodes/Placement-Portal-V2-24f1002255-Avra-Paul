"""
Main Flask Application for the Placement Portal.

This file:
    - Creates and configures the Flask app
    - Initializes all extensions (SQLAlchemy, JWT, Cache, Mail, CORS)
    - Registers all route blueprints
    - Creates the admin user on first run
    - Serves the Vue.js frontend
"""
import os
from datetime import timedelta
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_mail import Mail
from werkzeug.security import generate_password_hash

from backend.config import Config
from backend.models import db, User

# ---------------------------------------------------------------------------
#  Initialize extensions (created here, attached to app in create_app)
# ---------------------------------------------------------------------------
jwt = JWTManager()
cache = Cache()
mail = Mail()


def create_app():
    """
    Application factory function.
    Creates and configures the Flask app, initializes all extensions,
    and registers all route blueprints.
    """
    app = Flask(
        __name__,
        # Tell Flask where to find templates and static files
        # The frontend folder contains our Vue.js app
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend'),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'src'),
        static_url_path='/src'
    )

    # Load configuration from config.py
    app.config.from_object(Config)

    # Set JWT expiry as timedelta
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)

    # --- Initialize Extensions ---
    db.init_app(app)           # Database (SQLAlchemy)
    jwt.init_app(app)          # JWT authentication
    cache.init_app(app)        # Redis caching
    mail.init_app(app)         # Email sending
    CORS(app)                  # Allow cross-origin requests (for Vue.js dev)

    # --- Register Route Blueprints ---
    from backend.routes.auth import auth_bp
    from backend.routes.admin import admin_bp, init_admin_cache
    from backend.routes.company import company_bp, init_company_cache
    from backend.routes.student import student_bp, init_student_cache

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(student_bp)

    # Pass cache instance to route modules that need it
    init_admin_cache(cache)
    init_company_cache(cache)
    init_student_cache(cache)

    # --- Create upload and export directories ---
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

    # --- Create database tables and seed admin user ---
    with app.app_context():
        db.create_all()  # Create all tables if they don't exist
        _create_admin_user(app)

    # --- Serve Frontend ---
    @app.route('/')
    def serve_frontend():
        """Serve the main Vue.js frontend page."""
        return send_from_directory(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend'),
            'index.html'
        )

    @app.route('/components/<path:filename>')
    def serve_components(filename):
        """Serve Vue component files (.vue files)."""
        return send_from_directory(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'src', 'components'),
            filename,
            mimetype='application/javascript'
        )

    return app


def _create_admin_user(app):
    """
    Create the admin user if it doesn't already exist.
    This ensures admin is always available without manual setup.
    Called once during app initialization.
    """
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            username=app.config['ADMIN_USERNAME'],
            password_hash=generate_password_hash(app.config['ADMIN_PASSWORD']),
            email=app.config['ADMIN_EMAIL'],
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print(' * Admin user created: username=admin, password=admin123')
    else:
        print(' * Admin user already exists')
