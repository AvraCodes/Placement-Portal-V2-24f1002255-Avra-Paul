"""
Company Routes for the Placement Portal Application.

Handles:
    - GET/PUT  /api/company/profile                  -> View/update company profile
    - GET      /api/company/drives                   -> List company's drives
    - POST     /api/company/drives                   -> Create a new drive
    - GET      /api/company/drives/<id>/applications -> View applications for a drive
    - PUT      /api/company/applications/<id>/status -> Update application status
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models import db, User, CompanyProfile, PlacementDrive, Application, StudentProfile
from backend.utils import role_required

# Create company blueprint
company_bp = Blueprint('company', __name__, url_prefix='/api/company')

# Cache instance - set from app.py
cache = None


def init_company_cache(cache_instance):
    """Called from app.py to pass the cache instance."""
    global cache
    cache = cache_instance


@company_bp.route('/profile', methods=['GET'])
@jwt_required()
@role_required('company')
def get_profile():
    """Get the logged-in company's profile."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    profile = user.company_profile

    if not profile:
        return jsonify({'error': 'Company profile not found'}), 404

    return jsonify(profile.to_dict()), 200


@company_bp.route('/profile', methods=['PUT'])
@jwt_required()
@role_required('company')
def update_profile():
    """
    Update company profile details.
    Expects JSON with any of: company_name, hr_contact, website, description
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    profile = user.company_profile

    if not profile:
        return jsonify({'error': 'Company profile not found'}), 404

    data = request.get_json()

    # Update only the fields that are provided
    if 'company_name' in data:
        profile.company_name = data['company_name']
    if 'hr_contact' in data:
        profile.hr_contact = data['hr_contact']
    if 'website' in data:
        profile.website = data['website']
    if 'description' in data:
        profile.description = data['description']

    db.session.commit()
    return jsonify({'message': 'Profile updated', 'profile': profile.to_dict()}), 200


@company_bp.route('/drives', methods=['GET'])
@jwt_required()
@role_required('company')
def list_drives():
    """List all placement drives created by this company."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    profile = user.company_profile

    if not profile:
        return jsonify({'error': 'Company profile not found'}), 404

    drives = PlacementDrive.query.filter_by(company_id=profile.id).all()
    return jsonify([d.to_dict() for d in drives]), 200


@company_bp.route('/drives', methods=['POST'])
@jwt_required()
@role_required('company')
def create_drive():
    """
    Create a new placement drive.
    Company must be approved by admin before creating drives.

    Expects JSON:
    {
        "drive_name": "...",
        "job_title": "...",
        "job_description": "...",
        "eligibility_branch": "CS,ECE",
        "eligibility_cgpa": 7.0,
        "eligibility_year": 2025,
        "salary": 600000,
        "location": "Chennai",
        "application_deadline": "2025-12-31"
    }
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    profile = user.company_profile

    if not profile:
        return jsonify({'error': 'Company profile not found'}), 404

    # Check if company is approved
    if profile.approval_status != 'approved':
        return jsonify({'error': 'Company must be approved by admin before creating drives'}), 403

    data = request.get_json()

    # Validate required fields
    if not data.get('drive_name') or not data.get('job_title'):
        return jsonify({'error': 'Drive name and job title are required'}), 400

    # Parse the application deadline date
    deadline = None
    if data.get('application_deadline'):
        try:
            deadline = datetime.strptime(data['application_deadline'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Create the drive with 'pending' status (needs admin approval)
    drive = PlacementDrive(
        company_id=profile.id,
        drive_name=data['drive_name'],
        job_title=data['job_title'],
        job_description=data.get('job_description', ''),
        eligibility_branch=data.get('eligibility_branch', ''),
        eligibility_cgpa=data.get('eligibility_cgpa', 0.0),
        eligibility_year=data.get('eligibility_year'),
        salary=data.get('salary'),
        location=data.get('location', ''),
        application_deadline=deadline,
        status='pending'  # Drive starts as pending
    )
    db.session.add(drive)
    db.session.commit()

    # Clear caches
    if cache:
        cache.delete('admin_dashboard')

    return jsonify({'message': 'Drive created (pending admin approval)', 'drive': drive.to_dict()}), 201


@company_bp.route('/drives/<int:drive_id>/applications', methods=['GET'])
@jwt_required()
@role_required('company')
def view_applications(drive_id):
    """View all student applications for a specific drive owned by this company."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    profile = user.company_profile

    if not profile:
        return jsonify({'error': 'Company profile not found'}), 404

    # Verify the drive belongs to this company
    drive = db.session.get(PlacementDrive, drive_id)
    if not drive or drive.company_id != profile.id:
        return jsonify({'error': 'Drive not found or access denied'}), 404

    applications = Application.query.filter_by(drive_id=drive_id).all()
    return jsonify({
        'drive': drive.to_dict(),
        'applications': [a.to_dict() for a in applications]
    }), 200


@company_bp.route('/applications/<int:app_id>/status', methods=['PUT'])
@jwt_required()
@role_required('company')
def update_application_status(app_id):
    """
    Update the status of a student's application.
    Expects JSON: { "status": "shortlisted|selected|rejected", "interview_type": "...", "remarks": "..." }
    """
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    profile = user.company_profile

    if not profile:
        return jsonify({'error': 'Company profile not found'}), 404

    application = db.session.get(Application, app_id)
    if not application:
        return jsonify({'error': 'Application not found'}), 404

    # Verify the application's drive belongs to this company
    if application.drive.company_id != profile.id:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    new_status = data.get('status', '').strip()

    # Validate the new status
    valid_statuses = ['applied', 'shortlisted', 'selected', 'rejected']
    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    application.status = new_status

    # Optionally update interview type and remarks
    if 'interview_type' in data:
        application.interview_type = data['interview_type']
    if 'remarks' in data:
        application.remarks = data['remarks']

    db.session.commit()

    return jsonify({'message': 'Application status updated', 'application': application.to_dict()}), 200
