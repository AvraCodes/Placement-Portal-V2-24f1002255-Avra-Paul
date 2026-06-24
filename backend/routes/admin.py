"""
Admin Routes for the Placement Portal Application.

Handles all admin-only operations:
    - Dashboard stats
    - Company approval/rejection/blacklisting
    - Student blacklisting
    - Drive approval/rejection
    - View all applications
    - Search students and companies
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_caching import Cache
from backend.models import db, User, CompanyProfile, StudentProfile, PlacementDrive, Application
from backend.utils import role_required

# Create admin blueprint - all routes prefixed with /api/admin
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Cache instance will be set in app.py after initialization
cache = None


def init_admin_cache(cache_instance):
    """Called from app.py to pass the cache instance to this module."""
    global cache
    cache = cache_instance


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required('admin')
def dashboard():
    """
    Admin dashboard - returns summary statistics.
    Cached for 60 seconds to improve performance.
    """
    # Try to get cached data first
    if cache:
        cached = cache.get('admin_dashboard')
        if cached:
            return jsonify(cached), 200

    stats = {
        'total_students': StudentProfile.query.count(),
        'total_companies': CompanyProfile.query.count(),
        'total_drives': PlacementDrive.query.count(),
        'pending_companies': CompanyProfile.query.filter_by(approval_status='pending').count(),
        'pending_drives': PlacementDrive.query.filter_by(status='pending').count(),
        'total_applications': Application.query.count(),
        'selected_students': Application.query.filter_by(status='selected').count()
    }

    # Cache the result
    if cache:
        cache.set('admin_dashboard', stats, timeout=60)

    return jsonify(stats), 200


@admin_bp.route('/companies', methods=['GET'])
@jwt_required()
@role_required('admin')
def list_companies():
    """List all registered companies with their approval status."""
    companies = CompanyProfile.query.all()
    return jsonify([c.to_dict() for c in companies]), 200


@admin_bp.route('/companies/<int:company_id>/approve', methods=['PUT'])
@jwt_required()
@role_required('admin')
def approve_company(company_id):
    """Approve a company registration. Only approved companies can create drives."""
    company = db.session.get(CompanyProfile, company_id)
    if not company:
        return jsonify({'error': 'Company not found'}), 404

    company.approval_status = 'approved'
    db.session.commit()

    # Clear dashboard cache since stats changed
    if cache:
        cache.delete('admin_dashboard')

    return jsonify({'message': 'Company approved', 'company': company.to_dict()}), 200


@admin_bp.route('/companies/<int:company_id>/reject', methods=['PUT'])
@jwt_required()
@role_required('admin')
def reject_company(company_id):
    """Reject a company registration."""
    company = db.session.get(CompanyProfile, company_id)
    if not company:
        return jsonify({'error': 'Company not found'}), 404

    company.approval_status = 'rejected'
    db.session.commit()

    if cache:
        cache.delete('admin_dashboard')

    return jsonify({'message': 'Company rejected', 'company': company.to_dict()}), 200


@admin_bp.route('/companies/<int:company_id>/blacklist', methods=['PUT'])
@jwt_required()
@role_required('admin')
def blacklist_company(company_id):
    """
    Blacklist (deactivate) a company.
    This sets is_active=False on the User, preventing login.
    Also cancels all pending drives from this company.
    """
    company = db.session.get(CompanyProfile, company_id)
    if not company:
        return jsonify({'error': 'Company not found'}), 404

    # Deactivate the user account
    company.user.is_active = not company.user.is_active  # Toggle active status
    db.session.commit()

    if cache:
        cache.delete('admin_dashboard')

    status = 'activated' if company.user.is_active else 'blacklisted'
    return jsonify({'message': f'Company {status}', 'company': company.to_dict()}), 200


@admin_bp.route('/students', methods=['GET'])
@jwt_required()
@role_required('admin')
def list_students():
    """List all registered students."""
    students = StudentProfile.query.all()
    return jsonify([s.to_dict() for s in students]), 200


@admin_bp.route('/students/<int:student_id>/blacklist', methods=['PUT'])
@jwt_required()
@role_required('admin')
def blacklist_student(student_id):
    """Blacklist (deactivate) a student. Toggles active status."""
    student = db.session.get(StudentProfile, student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    student.user.is_active = not student.user.is_active  # Toggle
    db.session.commit()

    if cache:
        cache.delete('admin_dashboard')

    status = 'activated' if student.user.is_active else 'blacklisted'
    return jsonify({'message': f'Student {status}', 'student': student.to_dict()}), 200


@admin_bp.route('/drives', methods=['GET'])
@jwt_required()
@role_required('admin')
def list_drives():
    """List all placement drives with their status."""
    drives = PlacementDrive.query.all()
    return jsonify([d.to_dict() for d in drives]), 200


@admin_bp.route('/drives/<int:drive_id>/approve', methods=['PUT'])
@jwt_required()
@role_required('admin')
def approve_drive(drive_id):
    """Approve a placement drive. Only approved drives are visible to students."""
    drive = db.session.get(PlacementDrive, drive_id)
    if not drive:
        return jsonify({'error': 'Drive not found'}), 404

    drive.status = 'approved'
    db.session.commit()

    if cache:
        cache.delete('admin_dashboard')
        cache.delete('approved_drives')  # Clear student-facing cache

    return jsonify({'message': 'Drive approved', 'drive': drive.to_dict()}), 200


@admin_bp.route('/drives/<int:drive_id>/reject', methods=['PUT'])
@jwt_required()
@role_required('admin')
def reject_drive(drive_id):
    """Reject a placement drive."""
    drive = db.session.get(PlacementDrive, drive_id)
    if not drive:
        return jsonify({'error': 'Drive not found'}), 404

    drive.status = 'rejected'
    db.session.commit()

    if cache:
        cache.delete('admin_dashboard')
        cache.delete('approved_drives')

    return jsonify({'message': 'Drive rejected', 'drive': drive.to_dict()}), 200


@admin_bp.route('/applications', methods=['GET'])
@jwt_required()
@role_required('admin')
def list_applications():
    """List all student applications across all drives."""
    applications = Application.query.all()
    return jsonify([a.to_dict() for a in applications]), 200


@admin_bp.route('/search', methods=['GET'])
@jwt_required()
@role_required('admin')
def search():
    """
    Search students and companies by name.
    Query parameter: ?q=search_term&type=students|companies|all
    """
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')

    if not query:
        return jsonify({'error': 'Search query is required'}), 400

    results = {'students': [], 'companies': []}

    # Search students by name
    if search_type in ['students', 'all']:
        students = StudentProfile.query.filter(
            StudentProfile.full_name.ilike(f'%{query}%')
        ).all()
        results['students'] = [s.to_dict() for s in students]

    # Search companies by name
    if search_type in ['companies', 'all']:
        companies = CompanyProfile.query.filter(
            CompanyProfile.company_name.ilike(f'%{query}%')
        ).all()
        results['companies'] = [c.to_dict() for c in companies]

    return jsonify(results), 200
