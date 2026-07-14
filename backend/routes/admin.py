from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.models import db, CompanyProfile, StudentProfile, PlacementDrive, Application
from backend.utils import role_required

# Define Blueprint for admin-scoped requests prefixed with /api/admin
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
_cache = None


def init_admin_cache(c):
    """
    Register the Flask-Caching backend store globally for admin queries.
    """
    global _cache
    _cache = c


def _clear(key):
    """
    Invalidate a specific cache key when records are modified.
    """
    if _cache:
        _cache.delete(key)


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required('admin')
def dashboard():
    """
    GET /api/admin/dashboard
    Returns summary statistics for the dashboard view.
    Utilizes Redis cache storage with a 60-second invalidation timeout.
    """
    if _cache:
        hit = _cache.get('admin_dash')
        if hit:
            return jsonify(hit), 200

    # Query statistics from DB
    stats = {
        'total_students': StudentProfile.query.count(),
        'total_companies': CompanyProfile.query.count(),
        'total_drives': PlacementDrive.query.count(),
        'pending_companies': CompanyProfile.query.filter_by(approval_status='pending').count(),
        'pending_drives': PlacementDrive.query.filter_by(status='pending').count(),
        'total_applications': Application.query.count(),
        'selected_students': Application.query.filter_by(status='selected').count(),
        'approved_companies': CompanyProfile.query.filter_by(approval_status='approved').count(),
        'approved_drives': PlacementDrive.query.filter_by(status='approved').count(),
    }
    if _cache:
        _cache.set('admin_dash', stats, timeout=60)
    return jsonify(stats), 200


# ---- Company Actions ----

@admin_bp.route('/companies', methods=['GET'])
@jwt_required()
@role_required('admin')
def list_companies():
    """
    GET /api/admin/companies
    Lists all registered corporate profiles.
    """
    companies = CompanyProfile.query.all()
    return jsonify([c.to_dict() for c in companies]), 200


@admin_bp.route('/companies/<int:cid>/approve', methods=['PUT'])
@jwt_required()
@role_required('admin')
def approve_company(cid):
    """
    PUT /api/admin/companies/<cid>/approve
    Approves a pending company profile registration.
    Clears dashboard statistics cache to reflect changes.
    """
    c = db.session.get(CompanyProfile, cid)
    if not c:
        return jsonify({'error': 'Company not found'}), 404
    c.approval_status = 'approved'
    db.session.commit()
    _clear('admin_dash')
    return jsonify({'message': 'Company approved', 'company': c.to_dict()}), 200


@admin_bp.route('/companies/<int:cid>/reject', methods=['PUT'])
@jwt_required()
@role_required('admin')
def reject_company(cid):
    """
    PUT /api/admin/companies/<cid>/reject
    Rejects a pending company profile registration.
    Clears dashboard statistics cache.
    """
    c = db.session.get(CompanyProfile, cid)
    if not c:
        return jsonify({'error': 'Company not found'}), 404
    c.approval_status = 'rejected'
    db.session.commit()
    _clear('admin_dash')
    return jsonify({'message': 'Company rejected', 'company': c.to_dict()}), 200


@admin_bp.route('/companies/<int:cid>/blacklist', methods=['PUT'])
@jwt_required()
@role_required('admin')
def toggle_company(cid):
    """
    PUT /api/admin/companies/<cid>/blacklist
    Toggles the active state of a company account. Blacklists or activates the login.
    """
    c = db.session.get(CompanyProfile, cid)
    if not c:
        return jsonify({'error': 'Company not found'}), 404
    c.user.is_active = not c.user.is_active
    db.session.commit()
    _clear('admin_dash')
    action = 'activated' if c.user.is_active else 'blacklisted'
    return jsonify({'message': f'Company {action}', 'company': c.to_dict()}), 200


# ---- Student Actions ----

@admin_bp.route('/students', methods=['GET'])
@jwt_required()
@role_required('admin')
def list_students():
    """
    GET /api/admin/students
    Lists all registered student profiles.
    """
    students = StudentProfile.query.all()
    return jsonify([s.to_dict() for s in students]), 200


@admin_bp.route('/students/<int:sid>/blacklist', methods=['PUT'])
@jwt_required()
@role_required('admin')
def toggle_student(sid):
    """
    PUT /api/admin/students/<sid>/blacklist
    Toggles the active state of a student account. Blacklists or activates the login.
    """
    s = db.session.get(StudentProfile, sid)
    if not s:
        return jsonify({'error': 'Student not found'}), 404
    s.user.is_active = not s.user.is_active
    db.session.commit()
    _clear('admin_dash')
    action = 'activated' if s.user.is_active else 'blacklisted'
    return jsonify({'message': f'Student {action}', 'student': s.to_dict()}), 200


# ---- Placement Drives ----

@admin_bp.route('/drives', methods=['GET'])
@jwt_required()
@role_required('admin')
def list_drives():
    """
    GET /api/admin/drives
    Lists all placement drives created by companies.
    """
    drives = PlacementDrive.query.all()
    return jsonify([d.to_dict() for d in drives]), 200


@admin_bp.route('/drives/<int:did>/approve', methods=['PUT'])
@jwt_required()
@role_required('admin')
def approve_drive(did):
    """
    PUT /api/admin/drives/<did>/approve
    Approves a pending placement drive created by a company.
    """
    d = db.session.get(PlacementDrive, did)
    if not d:
        return jsonify({'error': 'Drive not found'}), 404
    d.status = 'approved'
    db.session.commit()
    _clear('admin_dash')
    _clear('approved_drives')
    return jsonify({'message': 'Drive approved', 'drive': d.to_dict()}), 200


@admin_bp.route('/drives/<int:did>/reject', methods=['PUT'])
@jwt_required()
@role_required('admin')
def reject_drive(did):
    """
    PUT /api/admin/drives/<did>/reject
    Rejects a pending placement drive.
    """
    d = db.session.get(PlacementDrive, did)
    if not d:
        return jsonify({'error': 'Drive not found'}), 404
    d.status = 'rejected'
    db.session.commit()
    _clear('admin_dash')
    _clear('approved_drives')
    return jsonify({'message': 'Drive rejected', 'drive': d.to_dict()}), 200


@admin_bp.route('/drives/<int:did>/close', methods=['PUT'])
@jwt_required()
@role_required('admin')
def close_drive(did):
    """
    PUT /api/admin/drives/<did>/close
    Closes an active placement drive to student registrations.
    """
    d = db.session.get(PlacementDrive, did)
    if not d:
        return jsonify({'error': 'Drive not found'}), 404
    d.status = 'closed'
    db.session.commit()
    _clear('admin_dash')
    _clear('approved_drives')
    return jsonify({'message': 'Drive closed', 'drive': d.to_dict()}), 200


# ---- Student Applications ----

@admin_bp.route('/applications', methods=['GET'])
@jwt_required()
@role_required('admin')
def list_applications():
    """
    GET /api/admin/applications
    Lists all job applications across all companies and students.
    """
    apps = Application.query.all()
    return jsonify([a.to_dict() for a in apps]), 200


# ---- Search Queries ----

@admin_bp.route('/search', methods=['GET'])
@jwt_required()
@role_required('admin')
def search():
    """
    GET /api/admin/search
    Queries databases of students and companies using standard case-insensitive wildcard patterns.
    """
    q = request.args.get('q', '').strip()
    stype = request.args.get('type', 'all')
    if not q:
        return jsonify({'error': 'Query required'}), 400

    result = {'students': [], 'companies': []}
    if stype in ('students', 'all'):
        students = StudentProfile.query.filter(
            StudentProfile.full_name.ilike(f'%{q}%')
        ).all()
        result['students'] = [s.to_dict() for s in students]
    if stype in ('companies', 'all'):
        companies = CompanyProfile.query.filter(
            CompanyProfile.company_name.ilike(f'%{q}%')
        ).all()
        result['companies'] = [c.to_dict() for c in companies]
    return jsonify(result), 200
