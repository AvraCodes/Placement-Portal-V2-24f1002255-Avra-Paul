"""
Authentication Routes for the Placement Portal Application.

Handles:
    - POST /api/auth/login    -> Login and get JWT token
    - POST /api/auth/register -> Register a new student or company
    - GET  /api/auth/me       -> Get current logged-in user's info
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models import db, User, CompanyProfile, StudentProfile

# Create a Blueprint for auth routes
# All routes in this file will be prefixed with /api/auth
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login endpoint.
    Expects JSON: { "username": "...", "password": "..." }
    Returns a JWT token if credentials are valid.
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    # Find the user by username
    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid username or password'}), 401

    if not user.is_active:
        return jsonify({'error': 'Your account has been deactivated. Contact admin.'}), 403

    # Create JWT token with user id as identity (must be string)
    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        'token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register endpoint for students and companies.
    Admin cannot register -- admin is created programmatically.

    For student registration, expects JSON:
    {
        "username": "...",
        "password": "...",
        "email": "...",
        "role": "student",
        "full_name": "...",
        "branch": "...",
        "cgpa": 8.5,
        "year": 2025
    }

    For company registration, expects JSON:
    {
        "username": "...",
        "password": "...",
        "email": "...",
        "role": "company",
        "company_name": "...",
        "hr_contact": "...",
        "website": "...",
        "description": "..."
    }
    """
    data = request.get_json()

    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()
    role = data.get('role', '').strip()

    # Validate required fields
    if not username or not password or not email or not role:
        return jsonify({'error': 'Username, password, email, and role are required'}), 400

    # Only student and company can register
    if role not in ['student', 'company']:
        return jsonify({'error': 'Role must be either "student" or "company"'}), 400

    # Check if username already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 409

    # Create the user
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        email=email,
        role=role
    )
    db.session.add(user)
    db.session.flush()  # Flush to get the user.id before creating profile

    # Create role-specific profile
    if role == 'student':
        full_name = data.get('full_name', username)
        student_profile = StudentProfile(
            user_id=user.id,
            full_name=full_name,
            branch=data.get('branch', ''),
            cgpa=data.get('cgpa'),
            year=data.get('year')
        )
        db.session.add(student_profile)
    elif role == 'company':
        company_name = data.get('company_name', '')
        if not company_name:
            return jsonify({'error': 'Company name is required'}), 400
        company_profile = CompanyProfile(
            user_id=user.id,
            company_name=company_name,
            hr_contact=data.get('hr_contact', ''),
            website=data.get('website', ''),
            description=data.get('description', ''),
            approval_status='pending'  # Companies start as pending until admin approves
        )
        db.session.add(company_profile)

    db.session.commit()

    return jsonify({
        'message': 'Registration successful',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get the currently logged-in user's information.
    Requires a valid JWT token in the Authorization header.
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Build response with role-specific profile data
    response = user.to_dict()

    if user.role == 'company' and user.company_profile:
        response['company_profile'] = user.company_profile.to_dict()
    elif user.role == 'student' and user.student_profile:
        response['student_profile'] = user.student_profile.to_dict()

    return jsonify(response), 200
