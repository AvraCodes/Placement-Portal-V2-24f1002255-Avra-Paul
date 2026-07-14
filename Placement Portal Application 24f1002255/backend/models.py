from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Instantiate SQLAlchemy. This will be bound to the Flask app inside app.py.
db = SQLAlchemy()


class User(db.Model):
    """
    Unified User model containing basic authentication fields for all user types.
    The 'role' column decides whether they are an 'admin', 'company', or 'student'.
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # Stores encrypted password hash
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'company', or 'student'
    is_active = db.Column(db.Boolean, default=True)  # True = Active, False = Blacklisted / Deactivated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 1-to-1 relationships linking authentication User to specific role profiles.
    # uselist=False guarantees that one User has at most one CompanyProfile or StudentProfile.
    company_profile = db.relationship('CompanyProfile', backref='user', uselist=False)
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False)

    def to_dict(self):
        """Converts user credentials metadata into a JSON-friendly python dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CompanyProfile(db.Model):
    """
    Stores metadata specific to companies.
    Linked to a User model via foreign key user_id.
    """
    __tablename__ = 'company_profile'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    company_name = db.Column(db.String(200), nullable=False)
    hr_contact = db.Column(db.String(100))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    industry = db.Column(db.String(100))
    # Approval status is updated by the Admin (Institute) role.
    approval_status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'

    # One company profile can create many placement drives.
    drives = db.relationship('PlacementDrive', backref='company', lazy=True)

    def to_dict(self):
        """Converts company profile into a dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'company_name': self.company_name,
            'hr_contact': self.hr_contact,
            'website': self.website,
            'description': self.description,
            'industry': self.industry,
            'approval_status': self.approval_status,
            'is_active': self.user.is_active if self.user else True,
            'username': self.user.username if self.user else None,
            'email': self.user.email if self.user else None
        }


class StudentProfile(db.Model):
    """
    Stores metadata specific to students.
    Linked to a User model via foreign key user_id.
    """
    __tablename__ = 'student_profile'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(200), nullable=False)
    branch = db.Column(db.String(100))  # e.g., CS, ECE
    cgpa = db.Column(db.Float)          # Floating point score
    year = db.Column(db.Integer)        # Graduation Year
    phone = db.Column(db.String(20))
    resume_path = db.Column(db.String(300))  # Filename of uploaded resume

    # One student can apply to many placement drives.
    applications = db.relationship('Application', backref='student', lazy=True)

    def to_dict(self):
        """Converts student profile into a dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'branch': self.branch,
            'cgpa': self.cgpa,
            'year': self.year,
            'phone': self.phone,
            'resume_path': self.resume_path,
            'is_active': self.user.is_active if self.user else True,
            'username': self.user.username if self.user else None,
            'email': self.user.email if self.user else None
        }


class PlacementDrive(db.Model):
    """
    Represents a recruitment event (drive) created by a company.
    Must be approved by the Admin before students can view or apply.
    """
    __tablename__ = 'placement_drive'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    drive_name = db.Column(db.String(200), nullable=False)
    job_title = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text)
    eligibility_branch = db.Column(db.String(300))  # Comma-separated list: e.g. 'CS,ECE'
    eligibility_cgpa = db.Column(db.Float, default=0.0)
    eligibility_year = db.Column(db.Integer)
    salary = db.Column(db.Float)
    location = db.Column(db.String(200))
    application_deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'closed', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # One placement drive can receive multiple student applications.
    applications = db.relationship('Application', backref='drive', lazy=True)

    def to_dict(self):
        """Converts drive details to a dictionary representation."""
        return {
            'id': self.id,
            'company_id': self.company_id,
            'company_name': self.company.company_name if self.company else None,
            'drive_name': self.drive_name,
            'job_title': self.job_title,
            'job_description': self.job_description,
            'eligibility_branch': self.eligibility_branch,
            'eligibility_cgpa': self.eligibility_cgpa,
            'eligibility_year': self.eligibility_year,
            'salary': self.salary,
            'location': self.location,
            'application_deadline': self.application_deadline.isoformat() if self.application_deadline else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'application_count': len(self.applications)
        }


class Application(db.Model):
    """
    Represents a student's application to a placement drive.
    Includes state columns like status, interview type, and company remarks.
    """
    __tablename__ = 'application'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='applied')  # 'applied', 'shortlisted', 'selected', 'rejected'
    interview_type = db.Column(db.String(50))  # e.g., 'in-person', 'online'
    remarks = db.Column(db.Text)               # Notes/Feedback from the company

    # UNIQUE CONSTRAINT: Ensures a student can apply to a specific placement drive only once.
    __table_args__ = (db.UniqueConstraint('student_id', 'drive_id', name='uq_student_drive'),)

    def to_dict(self):
        """Converts application status log to a dictionary representation."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'drive_id': self.drive_id,
            'student_name': self.student.full_name if self.student else None,
            'student_branch': self.student.branch if self.student else None,
            'student_cgpa': self.student.cgpa if self.student else None,
            'student_email': self.student.user.email if self.student and self.student.user else None,
            'drive_name': self.drive.drive_name if self.drive else None,
            'job_title': self.drive.job_title if self.drive else None,
            'company_name': self.drive.company.company_name if self.drive and self.drive.company else None,
            'application_date': self.application_date.isoformat() if self.application_date else None,
            'status': self.status,
            'interview_type': self.interview_type,
            'remarks': self.remarks
        }

