from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from backend.models import db, User


def role_required(required_role):
    """Decorator to enforce role-based access on a route."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = int(get_jwt_identity())
            user = db.session.get(User, user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            if not user.is_active:
                return jsonify({'error': 'Account deactivated'}), 403
            if user.role != required_role:
                return jsonify({'error': f'Access denied. Requires {required_role} role'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def check_eligibility(student_profile, drive):
    """
    Returns (is_eligible: bool, reason: str).
    Checks CGPA, graduation year, and branch.
    """
    if drive.eligibility_cgpa and student_profile.cgpa is not None:
        if student_profile.cgpa < drive.eligibility_cgpa:
            return False, f'CGPA too low (required: {drive.eligibility_cgpa}, yours: {student_profile.cgpa})'

    if drive.eligibility_year and student_profile.year:
        if student_profile.year != drive.eligibility_year:
            return False, f'Graduation year mismatch (required: {drive.eligibility_year})'

    if drive.eligibility_branch and student_profile.branch:
        allowed = [b.strip().upper() for b in drive.eligibility_branch.split(',')]
        if student_profile.branch.strip().upper() not in allowed:
            return False, f'Branch not eligible (allowed: {drive.eligibility_branch})'

    return True, 'Eligible'
