"""
Database Models for the Placement Portal Application.

This file defines all the database tables using SQLAlchemy ORM.
Tables:
    - User: Unified user model for admin, company, and student roles
    - CompanyProfile: Company details (linked to User)
    - StudentProfile: Student details (linked to User)
    - PlacementDrive: Recruitment drives created by companies
    - Application: Student applications to placement drives
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Create the SQLAlchemy database instance
# This will be initialized with the Flask app in app.py
db = SQLAlchemy()


class User(db.Model):
    """
    Unified User model for all roles (admin, company, student).
    Every person who logs in has a row in this table.
    The 'role' column determines what they can do.
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # Stores hashed password
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'company', or 'student'
    is_active = db.Column(db.Boolean, default=True)  # False = blacklisted/deactivated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships: a user can have one company profile OR one student profile
    company_profile = db.relationship('CompanyProfile', backref='user', uselist=False)
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False)

    def to_dict(self):
        """Convert user object to a dictionary for JSON responses."""
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
    Stores company-specific details.
    Linked to a User with role='company' via user_id.
    A company must be approved by admin before creating drives.
    """
    __tablename__ = 'company_profile'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    company_name = db.Column(db.String(200), nullable=False)
    hr_contact = db.Column(db.String(100))  # HR phone or email
    website = db.Column(db.String(200))
    description = db.Column(db.Text)  # About the company
    approval_status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'

    # Relationship: a company can have many placement drives
    drives = db.relationship('PlacementDrive', backref='company', lazy=True)

    def to_dict(self):
        """Convert company profile to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'company_name': self.company_name,
            'hr_contact': self.hr_contact,
            'website': self.website,
            'description': self.description,
            'approval_status': self.approval_status,
            'is_active': self.user.is_active if self.user else True
        }


class StudentProfile(db.Model):
    """
    Stores student-specific details.
    Linked to a User with role='student' via user_id.
    """
    __tablename__ = 'student_profile'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(200), nullable=False)
    branch = db.Column(db.String(100))  # e.g., 'Computer Science', 'Electrical'
    cgpa = db.Column(db.Float)  # e.g., 8.5
    year = db.Column(db.Integer)  # Graduation year, e.g., 2025
    resume_path = db.Column(db.String(300))  # File path to uploaded resume

    # Relationship: a student can have many applications
    applications = db.relationship('Application', backref='student', lazy=True)

    def to_dict(self):
        """Convert student profile to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'branch': self.branch,
            'cgpa': self.cgpa,
            'year': self.year,
            'resume_path': self.resume_path,
            'is_active': self.user.is_active if self.user else True
        }


class PlacementDrive(db.Model):
    """
    Represents a recruitment drive created by a company.
    Must be approved by admin before students can see and apply.
    """
    __tablename__ = 'placement_drive'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    drive_name = db.Column(db.String(200), nullable=False)
    job_title = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text)
    eligibility_branch = db.Column(db.String(300))  # Comma-separated, e.g., 'CS,ECE,EE'
    eligibility_cgpa = db.Column(db.Float, default=0.0)  # Minimum CGPA required
    eligibility_year = db.Column(db.Integer)  # Target graduation year
    salary = db.Column(db.Float)  # Package offered (in currency units)
    location = db.Column(db.String(200))  # Job location
    application_deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'closed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: a drive can have many applications
    applications = db.relationship('Application', backref='drive', lazy=True)

    def to_dict(self):
        """Convert drive to dictionary."""
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
    Tracks the status from 'applied' through to 'selected' or 'rejected'.
    A student can only apply once to each drive (enforced by unique constraint).
    """
    __tablename__ = 'application'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='applied')  # 'applied', 'shortlisted', 'selected', 'rejected'
    interview_type = db.Column(db.String(50))  # 'in-person', 'online', or null
    remarks = db.Column(db.Text)  # Notes from the company

    # Unique constraint: one student can apply to a drive only once
    __table_args__ = (db.UniqueConstraint('student_id', 'drive_id', name='unique_student_drive'),)

    def to_dict(self):
        """Convert application to dictionary."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'drive_id': self.drive_id,
            'student_name': self.student.full_name if self.student else None,
            'student_branch': self.student.branch if self.student else None,
            'student_cgpa': self.student.cgpa if self.student else None,
            'drive_name': self.drive.drive_name if self.drive else None,
            'job_title': self.drive.job_title if self.drive else None,
            'company_name': self.drive.company.company_name if self.drive and self.drive.company else None,
            'application_date': self.application_date.isoformat() if self.application_date else None,
            'status': self.status,
            'interview_type': self.interview_type,
            'remarks': self.remarks
        }
