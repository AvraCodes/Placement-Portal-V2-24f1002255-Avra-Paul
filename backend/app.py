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

# Instantiate global Flask extensions.
jwt = JWTManager()
cache = Cache()
mail = Mail()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND = os.path.join(ROOT, 'frontend')


def create_app():
    """
    Flask Application Factory.
    Initializes configuration, extensions, registers blueprints, 
    creates DB tables, seeds default admin, and sets up static routing.
    """
    app = Flask(
        __name__,
        template_folder=FRONTEND,
        static_folder=os.path.join(FRONTEND, 'src'),
        static_url_path='/src'
    )
    app.config.from_object(Config)
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)

    # Bind extensions to the application instance.
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    CORS(app)

    # Import and register route Blueprints.
    from backend.routes.auth import auth_bp
    from backend.routes.admin import admin_bp, init_admin_cache
    from backend.routes.company import company_bp, init_company_cache
    from backend.routes.student import student_bp, init_student_cache

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(student_bp)

    # Bind cache instances.
    init_admin_cache(cache)
    init_company_cache(cache)
    init_student_cache(cache)

    # Create directories for uploads and exports.
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.EXPORT_FOLDER, exist_ok=True)

    with app.app_context():
        # Create SQLite database tables if they do not exist.
        db.create_all()
        _seed_admin(app)

    @app.route('/')
    def index():
        """Serve the frontend entry page."""
        return send_from_directory(FRONTEND, 'index.html')

    @app.route('/<filename>.html')
    def serve_html(filename):
        """Serve any HTML file in the frontend folder (e.g. debug.html)."""
        return send_from_directory(FRONTEND, filename + '.html')

    @app.route('/src/<path:filename>')
    def serve_src(filename):
        """
        Generic Static Routing.
        Serves any file recursively under frontend/src/ (views, components, services, utils, app.js)
        so that standard browser ES module imports work perfectly.
        """
        return send_from_directory(
            os.path.join(FRONTEND, 'src'),
            filename
        )

    return app


def _seed_admin(app):
    """Programmatic seeding of default Admin user on app startup."""
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username=app.config['ADMIN_USERNAME'],
            password_hash=generate_password_hash(app.config['ADMIN_PASSWORD']),
            email=app.config['ADMIN_EMAIL'],
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print(' * Admin seeded: admin / admin123')
    else:
        print(' * Admin already exists')
