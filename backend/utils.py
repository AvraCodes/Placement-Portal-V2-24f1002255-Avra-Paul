"""
Utility / Helper functions for the Placement Portal Application.

Contains:
    - Role-checking decorators for route protection
    - Email sending helper
    - Eligibility validation
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from backend.models import db, User


# ---------------------------------------------------------------------------
#  Role-checking decorators
#  These wrap around route functions to ensure only the right role can access.
# ---------------------------------------------------------------------------

def role_required(required_role):
    """
    Decorator that checks if the logged-in user has the required role.
    Usage:
        @role_required('admin')
        def admin_only_route():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # get_jwt_identity() returns the user id stored in the JWT token (as string)
            user_id = int(get_jwt_identity())
            user = db.session.get(User, user_id)

            if not user:
                return jsonify({'error': 'User not found'}), 404
            if not user.is_active:
                return jsonify({'error': 'Your account has been deactivated'}), 403
            if user.role != required_role:
                return jsonify({'error': 'Access denied. Requires ' + required_role + ' role'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def check_eligibility(student_profile, drive):
    """
    Check if a student is eligible for a placement drive.
    Returns (is_eligible, reason) tuple.

    Checks:
        1. Student's CGPA >= drive's minimum CGPA
        2. Student's graduation year matches drive's target year
        3. Student's branch is in the drive's eligible branches list
    """
    # Check CGPA requirement
    if drive.eligibility_cgpa and student_profile.cgpa:
        if student_profile.cgpa < drive.eligibility_cgpa:
            return False, 'CGPA too low. Minimum required: ' + str(drive.eligibility_cgpa)

    # Check graduation year
    if drive.eligibility_year and student_profile.year:
        if student_profile.year != drive.eligibility_year:
            return False, 'Graduation year does not match. Required: ' + str(drive.eligibility_year)

    # Check branch eligibility
    if drive.eligibility_branch and student_profile.branch:
        # eligibility_branch is comma-separated, e.g., "CS,ECE,EE"
        allowed_branches = [b.strip().upper() for b in drive.eligibility_branch.split(',')]
        if student_profile.branch.strip().upper() not in allowed_branches:
            return False, 'Your branch is not eligible for this drive'

    return True, 'Eligible'
