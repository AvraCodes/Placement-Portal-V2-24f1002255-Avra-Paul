# Placement Portal Application (PPA) - V2

PPA V2 is a responsive, web-based system designed to coordinate and manage campus placement drives involving institutes, recruiting companies, and students. Currently, institutes rely on spreadsheets or manual emails, which PPA replaces with role-based dashboard control.

## Technology Stack
- **Backend API**: Flask & Flask-SQLAlchemy (SQLite database)
- **Frontend UI**: Vue.js 3 (CDN), Vue Router 4 (CDN), and Bootstrap 5
- **Caching**: Flask-Caching backed by Redis
- **Background Jobs**: Celery worker & beat scheduler backed by Redis

## Key Features
- **Admin**: Approve recruiting companies and placement drives, search student databases, toggle blacklists, and trigger reminder/report batches.
- **Companies**: Create job openings, review candidate details and resume summaries, shortlist, and schedule technical interviews.
- **Students**: Filter approved drives, verify eligibility (CGPA/branch constraints), apply to jobs, and export personal application histories to CSV.

## Getting Started

1. **Install Python requirements**:
   ```bash
   venv/bin/pip install -r requirements.txt
   ```

2. **Initialize and Seed Database**:
   ```bash
   venv/bin/flask --app app init-db
   ```

3. **Start services**:
   - Celery Worker: `venv/bin/python -m celery -A celery_app.celery worker --loglevel=info`
   - Celery Beat: `venv/bin/python -m celery -A celery_app.celery beat --loglevel=info`
   - Flask Web server: `venv/bin/python app.py`

4. **Navigate Browser**:
   Open `http://localhost:5001/` in your browser.
