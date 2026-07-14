from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models import db, User, CompanyProfile, PlacementDrive, Application
from backend.utils import role_required

# Define Blueprint for company-scoped requests prefixed with /api/company
company_bp = Blueprint('company', __name__, url_prefix='/api/company')
_cache = None


def init_company_cache(c):
    """
    Register the Flask-Caching backend store globally for company queries.
    """
    global _cache
    _cache = c


@company_bp.route('/profile', methods=['GET'])
@jwt_required()
@role_required('company')
def get_profile():
    """
    GET /api/company/profile
    Fetches the profile info of the logged-in company user.
    """
    user = db.session.get(User, int(get_jwt_identity()))
    if not user.company_profile:
        return jsonify({'error': 'Profile not found'}), 404
    return jsonify(user.company_profile.to_dict()), 200


@company_bp.route('/profile', methods=['PUT'])
@jwt_required()
@role_required('company')
def update_profile():
    """
    PUT /api/company/profile
    Updates parameters on the company profile (e.g. HR contacts, descriptions, etc.).
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.company_profile
    if not p:
        return jsonify({'error': 'Profile not found'}), 404
    data = request.get_json()
    for field in ('company_name', 'hr_contact', 'website', 'description', 'industry'):
        if field in data:
            setattr(p, field, data[field])
    db.session.commit()
    return jsonify({'message': 'Profile updated', 'profile': p.to_dict()}), 200


@company_bp.route('/drives', methods=['GET'])
@jwt_required()
@role_required('company')
def list_drives():
    """
    GET /api/company/drives
    Lists all placement drives created by this company.
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.company_profile
    if not p:
        return jsonify([]), 200
    drives = PlacementDrive.query.filter_by(company_id=p.id).all()
    return jsonify([d.to_dict() for d in drives]), 200


@company_bp.route('/drives', methods=['POST'])
@jwt_required()
@role_required('company')
def create_drive():
    """
    POST /api/company/drives
    Creates a new placement drive (job posting).
    Awaiting admin approval before it becomes visible to students.
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.company_profile
    if not p:
        return jsonify({'error': 'Profile not found'}), 404
    if p.approval_status != 'approved':
        return jsonify({'error': 'Company must be approved by admin first'}), 403

    data = request.get_json()
    if not data.get('drive_name') or not data.get('job_title'):
        return jsonify({'error': 'Drive name and job title required'}), 400

    deadline = None
    if data.get('application_deadline'):
        try:
            deadline = datetime.strptime(data['application_deadline'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Date format must be YYYY-MM-DD'}), 400

    drive = PlacementDrive(
        company_id=p.id,
        drive_name=data['drive_name'],
        job_title=data['job_title'],
        job_description=data.get('job_description', ''),
        eligibility_branch=data.get('eligibility_branch', ''),
        eligibility_cgpa=float(data.get('eligibility_cgpa', 0)) if data.get('eligibility_cgpa') else 0.0,
        eligibility_year=data.get('eligibility_year'),
        salary=data.get('salary'),
        location=data.get('location', ''),
        application_deadline=deadline,
        status='pending'
    )
    db.session.add(drive)
    db.session.commit()
    if _cache:
        _cache.delete('admin_dash')
    return jsonify({'message': 'Drive created, pending admin approval', 'drive': drive.to_dict()}), 201


@company_bp.route('/drives/<int:did>/applications', methods=['GET'])
@jwt_required()
@role_required('company')
def view_applications(did):
    """
    GET /api/company/drives/<did>/applications
    Lists all student applicants for a specific placement drive.
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.company_profile
    if not p:
        return jsonify({'error': 'Profile not found'}), 404
    drive = db.session.get(PlacementDrive, did)
    if not drive or drive.company_id != p.id:
        return jsonify({'error': 'Drive not found or access denied'}), 404
    apps = Application.query.filter_by(drive_id=did).all()
    return jsonify({'drive': drive.to_dict(), 'applications': [a.to_dict() for a in apps]}), 200


@company_bp.route('/applications/<int:aid>/status', methods=['PUT'])
@jwt_required()
@role_required('company')
def update_status(aid):
    """
    PUT /api/company/applications/<aid>/status
    Updates applicant status (e.g. shortlists, selects, rejects) and schedules interview type/remarks.
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.company_profile
    if not p:
        return jsonify({'error': 'Profile not found'}), 404
    app = db.session.get(Application, aid)
    if not app or app.drive.company_id != p.id:
        return jsonify({'error': 'Application not found or access denied'}), 404

    data = request.get_json()
    new_status = data.get('status', '').strip()
    if new_status not in ('applied', 'shortlisted', 'selected', 'rejected'):
        return jsonify({'error': 'Invalid status'}), 400

    app.status = new_status
    if 'interview_type' in data:
        app.interview_type = data['interview_type']
    if 'remarks' in data:
        app.remarks = data['remarks']
    db.session.commit()
    return jsonify({'message': 'Status updated', 'application': app.to_dict()}), 200


@company_bp.route('/drives/<int:did>/close', methods=['PUT'])
@jwt_required()
@role_required('company')
def close_drive(did):
    """
    PUT /api/company/drives/<did>/close
    Closes an active placement drive to student registrations.
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.company_profile
    if not p:
        return jsonify({'error': 'Profile not found'}), 404
    drive = db.session.get(PlacementDrive, did)
    if not drive or drive.company_id != p.id:
        return jsonify({'error': 'Drive not found or access denied'}), 404
    drive.status = 'closed'
    db.session.commit()
    if _cache:
        _cache.delete('approved_drives')
    return jsonify({'message': 'Drive closed', 'drive': drive.to_dict()}), 200
