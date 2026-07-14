"""
Celery Background Task Scheduler and Executors:
  1. send_daily_reminders    - Scheduled to run daily at 8:00 AM (reminds students about deadlines).
  2. send_monthly_report     - Scheduled to run on the 1st of every month at 9:00 AM (sends placement report to admin).
  3. export_applications_csv  - Async task triggered on-demand by students to export application history to CSV.
"""
import csv
import os
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab

# Initialize the Celery application.
# Redis is used as the message broker (to pass tasks) and backend (to store results).
# Database index 1 of Redis (redis://localhost:6379/1) keeps task data separate from caching.
celery_app = Celery(
    'ppa',
    broker='redis://localhost:6379/1',
    backend='redis://localhost:6379/1'
)

# Configure Celery Beat: the scheduler that dispatches periodic tasks.
celery_app.conf.update(
    timezone='Asia/Kolkata',  # Uses local timezone to schedule daily/monthly jobs
    enable_utc=False,
    beat_schedule={
        # Task 1: Daily Reminder at 8:00 AM
        'daily-reminders': {
            'task': 'backend.tasks.send_daily_reminders',
            'schedule': crontab(hour=8, minute=0),
        },
        # Task 2: Monthly Activity Report on the 1st of every month at 9:00 AM
        'monthly-report': {
            'task': 'backend.tasks.send_monthly_report',
            'schedule': crontab(day_of_month=1, hour=9, minute=0),
        },
    }
)


def _get_app():
    """
    Helper function to instantiate the Flask app context.
    Since Celery runs in a separate worker process outside of the HTTP lifecycle,
    we must instantiate the Flask application to access configuration and extensions.
    """
    from backend.app import create_app
    return create_app()


# ---------------------------------------------------------------------------
# Task 1: Daily Reminders (Scheduled)
# ---------------------------------------------------------------------------
@celery_app.task(name='backend.tasks.send_daily_reminders')
def send_daily_reminders():
    """
    Finds approved drives whose application deadlines are within the next 48 hours
    and emails active students a summary list to encourage them to apply.
    """
    app = _get_app()
    with app.app_context():  # Push Flask application context to query database
        from backend.models import PlacementDrive, StudentProfile, User
        from flask_mail import Mail, Message

        mail = Mail(app)
        today = datetime.now().date()
        upcoming = today + timedelta(days=2)  # Deadline threshold: 2 days

        # Query all approved drives with deadlines in range [today, today + 2 days]
        drives = PlacementDrive.query.filter(
            PlacementDrive.status == 'approved',
            PlacementDrive.application_deadline >= today,
            PlacementDrive.application_deadline <= upcoming
        ).all()

        if not drives:
            return 'No upcoming deadlines'

        # Fetch all active student profiles
        students = StudentProfile.query.join(User).filter(User.is_active == True).all()
        sent = 0
        
        # Email each student the upcoming drive list
        for student in students:
            items = ''.join(
                f'<li><strong>{d.drive_name}</strong> — {d.job_title} at {d.company.company_name}'
                f' (Deadline: {d.application_deadline})</li>'
                for d in drives
            )
            if student.user.email:
                try:
                    msg = Message(
                        subject='Placement Portal — Upcoming Deadlines Reminder',
                        recipients=[student.user.email],
                        html=f'''
                        <h2>Hello {student.full_name},</h2>
                        <p>The following placement drives have deadlines within 2 days:</p>
                        <ul>{items}</ul>
                        <p>Log in to apply before it's too late!</p>
                        <p>— Placement Portal Team</p>
                        '''
                    )
                    mail.send(msg)
                    sent += 1
                except Exception as e:
                    print(f'Reminder failed for {student.user.email}: {e}')
        return f'Sent {sent} reminder(s)'


# ---------------------------------------------------------------------------
# Task 2: Monthly Activity Report (Scheduled)
# ---------------------------------------------------------------------------
@celery_app.task(name='backend.tasks.send_monthly_report')
def send_monthly_report():
    """
    Generates placement metrics for the previous month (drives conducted, applications
    received, selection totals) and emails an HTML-formatted report to the admin.
    """
    app = _get_app()
    with app.app_context():  # Push Flask application context
        from backend.models import PlacementDrive, Application, User
        from flask_mail import Mail, Message

        mail = Mail(app)
        today = datetime.now()
        first_this = today.replace(day=1)
        last_month_end = first_this - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        month_label = last_month_start.strftime('%B %Y')

        # Calculate metrics using date ranges
        drives_count = PlacementDrive.query.filter(
            PlacementDrive.created_at >= last_month_start,
            PlacementDrive.created_at <= last_month_end
        ).count()
        apps_count = Application.query.filter(
            Application.application_date >= last_month_start,
            Application.application_date <= last_month_end
        ).count()
        selected_count = Application.query.filter(
            Application.application_date >= last_month_start,
            Application.application_date <= last_month_end,
            Application.status == 'selected'
        ).count()

        # Build clean HTML table report
        html = f'''
        <html><body style="font-family:Arial,sans-serif;padding:24px;background:#f4f6f9;">
        <div style="max-width:560px;margin:auto;background:#fff;border-radius:8px;padding:32px;
                    box-shadow:0 2px 8px rgba(0,0,0,.1);">
          <h1 style="color:#0d6efd;border-bottom:2px solid #0d6efd;padding-bottom:8px;">
            Monthly Placement Report
          </h1>
          <p style="color:#6c757d;">Period: <strong>{month_label}</strong></p>
          <table style="width:100%;border-collapse:collapse;margin-top:16px;">
            <tr style="background:#e9ecef;">
              <td style="padding:12px;border:1px solid #dee2e6;font-weight:600;">Drives Conducted</td>
              <td style="padding:12px;border:1px solid #dee2e6;font-size:1.4rem;
                         font-weight:700;color:#0d6efd;">{drives_count}</td>
            </tr>
            <tr>
              <td style="padding:12px;border:1px solid #dee2e6;font-weight:600;">Total Applications</td>
              <td style="padding:12px;border:1px solid #dee2e6;font-size:1.4rem;
                         font-weight:700;color:#198754;">{apps_count}</td>
            </tr>
            <tr style="background:#e9ecef;">
              <td style="padding:12px;border:1px solid #dee2e6;font-weight:600;">Students Selected</td>
              <td style="padding:12px;border:1px solid #dee2e6;font-size:1.4rem;
                         font-weight:700;color:#dc3545;">{selected_count}</td>
            </tr>
          </table>
          <p style="margin-top:24px;color:#6c757d;font-size:.875rem;">
            Generated automatically on {today.strftime('%d %B %Y')}.
          </p>
        </div>
        </body></html>
        '''

        # Fetch admin user to email the report
        admin = User.query.filter_by(role='admin').first()
        if admin and admin.email:
            try:
                msg = Message(
                    subject=f'Placement Portal — Monthly Report ({month_label})',
                    recipients=[admin.email],
                    html=html
                )
                mail.send(msg)
                return f'Report sent to {admin.email}'
            except Exception as e:
                return f'Failed: {e}'
        return 'No admin email found'


# ---------------------------------------------------------------------------
# Task 3: Export Applications as CSV (User-Triggered Async Job)
# ---------------------------------------------------------------------------
@celery_app.task(name='backend.tasks.export_applications_csv')
def export_applications_csv(student_id, student_email):
    """
    Asynchronously queries a student's entire application logs, formats it as a CSV file,
    saves the file to the local exports folder, and emails it as an attachment to the student.
    """
    app = _get_app()
    with app.app_context():  # Push Flask application context
        from backend.models import Application, StudentProfile, db
        from flask_mail import Mail, Message

        mail = Mail(app)
        student = db.session.get(StudentProfile, student_id)
        apps = Application.query.filter_by(student_id=student_id).all()

        # Ensure directory for exports exists.
        export_folder = app.config['EXPORT_FOLDER']
        os.makedirs(export_folder, exist_ok=True)

        # Generate a unique timestamped filename.
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'applications_{student_id}_{ts}.csv'
        filepath = os.path.join(export_folder, filename)

        # Write data to the CSV file.
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write Header row.
            writer.writerow([
                'Application ID', 'Student ID', 'Company Name', 'Drive Title',
                'Application Status', 'Application Date', 'Interview Type', 'Remarks'
            ])
            # Write Student applications list.
            for a in apps:
                writer.writerow([
                    a.id,
                    student_id,
                    a.drive.company.company_name if a.drive and a.drive.company else '',
                    a.drive.job_title if a.drive else '',
                    a.status,
                    a.application_date.strftime('%Y-%m-%d') if a.application_date else '',
                    a.interview_type or '',
                    a.remarks or ''
                ])

        # Attach the newly generated CSV file and mail it to the student.
        if student_email:
            try:
                msg = Message(
                    subject='Placement Portal — Your Application Export',
                    recipients=[student_email],
                    html=f'''
                    <h2>Hello {student.full_name if student else "Student"},</h2>
                    <p>Your placement application history export is attached.</p>
                    <p>— Placement Portal Team</p>
                    '''
                )
                with open(filepath, 'r', encoding='utf-8') as f:
                    msg.attach(filename, 'text/csv', f.read())
                mail.send(msg)
            except Exception as e:
                print(f'Export email failed: {e}')

        return {'status': 'done', 'file': filename}

