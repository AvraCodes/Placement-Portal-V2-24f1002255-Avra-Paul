from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models import db, User, CompanyProfile, StudentProfile

# Define the Authentication Blueprint.
# All routes registered on this blueprint will be prefixed with '/api/auth'.
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user and return a JWT access token.
    Accepts JSON body: { "username": "...", "password": "..." }
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    # Validate input fields.
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    # Query the user by username.
    user = User.query.filter_by(username=username).first()
    # Check if user exists and the hashed password matches the input.
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Prevent blacklisted users from logging in.
    if not user.is_active:
        return jsonify({'error': 'Account deactivated. Contact admin.'}), 403

    # Generate a JWT token containing the user ID as its identity.
    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'user': user.to_dict()}), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registers a new student or company profile.
    Saves a base User credentials row and creates the corresponding role-based profile.
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()
    role = data.get('role', '').strip()

    # Validate presence of mandatory fields.
    if not all([username, password, email, role]):
        return jsonify({'error': 'All fields are required'}), 400

    # Enforce allowed roles for self-registration.
    if role not in ('student', 'company'):
        return jsonify({'error': 'Role must be student or company'}), 400

    # Prevent registration of duplicate usernames.
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 409

    # Create the base user authentication entry.
    user = User(
        username=username,
        # Hash the password securely using pbkdf2 algorithm via werkzeug.
        password_hash=generate_password_hash(password),
        email=email,
        role=role
    )
    db.session.add(user)
    db.session.flush()  # Flushes changes to database to generate user.id before profile insertion.

    # Insert role-specific profile based on selection.
    if role == 'student':
        profile = StudentProfile(
            user_id=user.id,
            full_name=data.get('full_name', username),
            branch=data.get('branch', ''),
            cgpa=data.get('cgpa'),
            year=data.get('year'),
            phone=data.get('phone', '')
        )
        db.session.add(profile)
    else:
        company_name = data.get('company_name', '').strip()
        if not company_name:
            return jsonify({'error': 'Company name required'}), 400
        profile = CompanyProfile(
            user_id=user.id,
            company_name=company_name,
            hr_contact=data.get('hr_contact', ''),
            website=data.get('website', ''),
            description=data.get('description', ''),
            industry=data.get('industry', ''),
            approval_status='pending'  # Companies must be approved by the admin before creating drives.
        )
        db.session.add(profile)

    db.session.commit()
    return jsonify({'message': 'Registration successful', 'user': user.to_dict()}), 201


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """
    Returns the currently logged-in user profile details.
    Decodes the JWT token from the Authorization header.
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    resp = user.to_dict()
    # Attach role-specific profile details if they exist.
    if user.role == 'company' and user.company_profile:
        resp['company_profile'] = user.company_profile.to_dict()
    elif user.role == 'student' and user.student_profile:
        resp['student_profile'] = user.student_profile.to_dict()
    return jsonify(resp), 200

