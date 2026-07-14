import os
from datetime import date
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models import db, User, StudentProfile, PlacementDrive, Application
from backend.utils import role_required, check_eligibility

# Define Blueprint for student-scoped requests prefixed with /api/student
student_bp = Blueprint('student', __name__, url_prefix='/api/student')
_cache = None


def init_student_cache(c):
    """
    Register the Flask-Caching backend store globally for student queries.
    """
    global _cache
    _cache = c


@student_bp.route('/profile', methods=['GET'])
@jwt_required()
@role_required('student')
def get_profile():
    """
    GET /api/student/profile
    Retrieves the logged-in student's profile settings.
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.student_profile
    if not p:
        return jsonify({'error': 'Profile not found'}), 404
    result = p.to_dict()
    result['email'] = user.email
    result['username'] = user.username
    return jsonify(result), 200


@student_bp.route('/profile', methods=['PUT'])
@jwt_required()
@role_required('student')
def update_profile():
    """
    PUT /api/student/profile
    Updates personal info parameters on the student's profile (name, branch, phone, cgpa).
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.student_profile
    if not p:
        return jsonify({'error': 'Profile not found'}), 404
    data = request.get_json()
    for field in ('full_name', 'branch', 'phone'):
        if field in data:
            setattr(p, field, data[field])
    if 'cgpa' in data:
        p.cgpa = float(data['cgpa']) if data['cgpa'] else None
    if 'year' in data:
        p.year = int(data['year']) if data['year'] else None
    if 'email' in data:
        user.email = data['email']
    db.session.commit()
    return jsonify({'message': 'Profile updated', 'profile': p.to_dict()}), 200


@student_bp.route('/profile/resume', methods=['POST'])
@jwt_required()
@role_required('student')
def upload_resume():
    """
    POST /api/student/profile/resume
    Uploads a PDF/DOC resume file for the logged-in student.
    Files are saved with the student's user ID to avoid duplicate collisions.
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.student_profile
    if not p:
        return jsonify({'error': 'Profile not found'}), 404
    if 'resume' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    f = request.files['resume']
    if not f.filename:
        return jsonify({'error': 'No file selected'}), 400
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
    if ext not in ('pdf', 'doc', 'docx'):
        return jsonify({'error': 'Only PDF, DOC, DOCX allowed'}), 400
    folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(folder, exist_ok=True)
    filename = f'resume_{user.id}.{ext}'
    f.save(os.path.join(folder, filename))
    p.resume_path = filename
    db.session.commit()
    return jsonify({'message': 'Resume uploaded', 'filename': filename}), 200


@student_bp.route('/resume/<int:student_id>', methods=['GET'])
@jwt_required()
def get_resume(student_id):
    """
    GET /api/student/resume/<student_id>
    Streams back a student's resume attachment.
    """
    p = db.session.get(StudentProfile, student_id)
    if not p or not p.resume_path:
        return jsonify({'error': 'Resume not found'}), 404
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], p.resume_path)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found on server'}), 404
    return send_file(filepath, as_attachment=True)


@student_bp.route('/drives', methods=['GET'])
@jwt_required()
@role_required('student')
def list_drives():
    """
    GET /api/student/drives
    Lists all placement drives that are approved by admin.
    Returns drives with specific eligibility fields (is_eligible, eligibility_reason) custom computed for this student.
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.student_profile

    search = request.args.get('search', '').strip()
    query = PlacementDrive.query.filter_by(status='approved')
    if search:
        query = query.filter(
            db.or_(
                PlacementDrive.drive_name.ilike(f'%{search}%'),
                PlacementDrive.job_title.ilike(f'%{search}%'),
                PlacementDrive.location.ilike(f'%{search}%')
            )
        )

    drives = query.all()
    result = []
    for d in drives:
        dd = d.to_dict()
        if p:
            is_elig, reason = check_eligibility(p, d)
            dd['is_eligible'] = is_elig
            dd['eligibility_reason'] = reason
            existing = Application.query.filter_by(student_id=p.id, drive_id=d.id).first()
            dd['already_applied'] = existing is not None
            dd['application_status'] = existing.status if existing else None
        else:
            dd['is_eligible'] = False
            dd['eligibility_reason'] = 'Complete your profile first'
            dd['already_applied'] = False
            dd['application_status'] = None
        result.append(dd)
    return jsonify(result), 200


@student_bp.route('/drives/<int:did>/apply', methods=['POST'])
@jwt_required()
@role_required('student')
def apply(did):
    """
    POST /api/student/drives/<did>/apply
    Applies for a specific job drive.
    Performs validation tests (cgpa, branch, deadline, duplicate application checks).
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.student_profile
    if not p:
        return jsonify({'error': 'Complete your profile before applying'}), 400

    drive = db.session.get(PlacementDrive, did)
    if not drive:
        return jsonify({'error': 'Drive not found'}), 404
    if drive.status != 'approved':
        return jsonify({'error': 'Drive is not open for applications'}), 400
    if drive.application_deadline and drive.application_deadline < date.today():
        return jsonify({'error': 'Application deadline has passed'}), 400

    is_elig, reason = check_eligibility(p, drive)
    if not is_elig:
        return jsonify({'error': reason}), 400

    if Application.query.filter_by(student_id=p.id, drive_id=did).first():
        return jsonify({'error': 'Already applied to this drive'}), 409

    app = Application(student_id=p.id, drive_id=did, status='applied')
    db.session.add(app)
    db.session.commit()
    if _cache:
        _cache.delete('admin_dash')
    return jsonify({'message': 'Application submitted', 'application': app.to_dict()}), 201


@student_bp.route('/applications', methods=['GET'])
@jwt_required()
@role_required('student')
def list_applications():
    """
    GET /api/student/applications
    Lists all job applications submitted by this student.
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.student_profile
    if not p:
        return jsonify([]), 200
    apps = Application.query.filter_by(student_id=p.id).all()
    return jsonify([a.to_dict() for a in apps]), 200


@student_bp.route('/applications/history', methods=['GET'])
@jwt_required()
@role_required('student')
def history():
    """
    GET /api/student/applications/history
    Returns student profile settings along with their complete application log.
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.student_profile
    if not p:
        return jsonify({'student': None, 'applications': []}), 200
    apps = Application.query.filter_by(student_id=p.id).all()
    result = p.to_dict()
    result['email'] = user.email
    return jsonify({'student': result, 'applications': [a.to_dict() for a in apps]}), 200


@student_bp.route('/applications/export', methods=['POST'])
@jwt_required()
@role_required('student')
def export():
    """
    POST /api/student/applications/export
    Triggers an asynchronous celery job to format the application log as a CSV file and email it to the student.
    """
    user = db.session.get(User, int(get_jwt_identity()))
    p = user.student_profile
    if not p:
        return jsonify({'error': 'Profile not found'}), 404
    from backend.tasks import export_applications_csv
    task = export_applications_csv.delay(p.id, user.email)
    return jsonify({'message': 'Export started. You will be emailed when ready.', 'task_id': task.id}), 202
