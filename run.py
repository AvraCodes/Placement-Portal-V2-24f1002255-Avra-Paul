"""
Entry point to run the Placement Portal Application.
Run this file: python run.py
"""
from backend.app import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Run the Flask development server
    # debug=True enables auto-reload on code changes and shows detailed errors
    print('=' * 50)
    print('  Placement Portal Application')
    print('  Open http://localhost:5001 in your browser')
    print('=' * 50)
    app.run(debug=True, port=5001)
