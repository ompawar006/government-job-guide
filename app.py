"""
Government Job Guide – AI Career Assistant
Main Flask Application

Provides full-stack routes for:
- Landing page, Authentication (Register, Login, Logout)
- Dashboard, AI Chat Assistant, Job Categories, Eligibility Tool, Preparation Resources
- Saved Guidance, Profile and Settings
- JSON APIs for Chat, Eligibility Assessment, Saved Items, and User Management
"""

import os
import re
import logging
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, session,
    flash, jsonify, make_response
)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

import database
import ai_service

# Load environment configuration
load_dotenv()

app = Flask(__name__)
CORS(app)

# Flask Session Security Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_dev_secret_key_gov_job_guide_2026')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7  # 7 days

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger('app')

# Initialize database tables on app load
with app.app_context():
    database.init_db()


# --- Authentication Helpers & Decorators ---

def get_current_user():
    """Retrieve logged-in user record from session, or None."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return database.get_user_by_id(user_id)


@app.context_processor
def inject_user():
    """Inject current_user into all Jinja templates automatically."""
    user = get_current_user()
    return dict(current_user=user)


def login_required(f):
    """Decorator to protect routes requiring authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Check if this is an API call
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required. Please sign in.'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


EMAIL_REGEX = re.compile(r'^[\w\.-]+@([\w-]+\.)+[\w-]{2,8}$')


def validate_email(email: str) -> bool:
    """Validate email syntax."""
    return bool(EMAIL_REGEX.match(email.strip())) if email else False


# --- Frontend Page Routes ---

@app.route('/')
def index():
    """Landing Page."""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User Registration."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        if not name or len(name) < 2:
            flash('Full Name must be at least 2 characters long.', 'danger')
            return render_template('register.html', name=name, email=email)

        if not validate_email(email):
            flash('Please provide a valid email address.', 'danger')
            return render_template('register.html', name=name, email=email)

        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html', name=name, email=email)

        if password != confirm_password:
            flash('Passwords do not match. Please re-enter.', 'danger')
            return render_template('register.html', name=name, email=email)

        # Check for existing email
        existing_user = database.get_user_by_email(email)
        if existing_user:
            flash('An account with this email address already exists. Please log in.', 'danger')
            return render_template('register.html', name=name, email=email)

        # Securely hash password and create account
        password_hash = generate_password_hash(password)
        try:
            user_id = database.create_user(name, email, password_hash)
            session['user_id'] = user_id
            session['user_name'] = name
            session['user_email'] = email
            flash(f'Account created successfully! Welcome, {name}.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('register.html', name=name, email=email)

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User Login."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Please enter both your email and password.', 'danger')
            return render_template('login.html', email=email)

        user = database.get_user_by_email(email)
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid email or password. Please check your credentials.', 'danger')
            return render_template('login.html', email=email)

        # Authentication successful
        session.permanent = remember
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Sign out the current user."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Personalized user dashboard."""
    user = get_current_user()
    recent_saved = database.get_saved_guidance(user['id'])[:3]
    profile = database.get_user_profile(user['id'])
    return render_template('dashboard.html', user=user, recent_saved=recent_saved, profile=profile)


@app.route('/chat')
def chat():
    """AI Chat Page."""
    user = get_current_user()
    return render_template('chat.html', user=user)


@app.route('/jobs')
def jobs():
    """Government Job Categories Page."""
    return render_template('jobs.html')


@app.route('/eligibility')
def eligibility():
    """Eligibility Guidance Tool Page."""
    user = get_current_user()
    profile = database.get_user_profile(user['id']) if user else None
    return render_template('eligibility.html', user=user, profile=profile)


@app.route('/preparation')
def preparation():
    """Preparation Resources Page."""
    return render_template('preparation.html')


@app.route('/saved')
@login_required
def saved():
    """Saved Guidance Page."""
    user = get_current_user()
    items = database.get_saved_guidance(user['id'])
    return render_template('saved.html', user=user, items=items)


@app.route('/profile')
@login_required
def profile():
    """User Profile and Career Settings Page."""
    user = get_current_user()
    user_profile = database.get_user_profile(user['id'])
    return render_template('profile.html', user=user, profile=user_profile)


# --- RESTful JSON APIs ---

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    Main Chat API Endpoint.
    Accepts JSON: {"message": "...", "history": [...]}
    Returns JSON: {"reply": "..."}
    """
    if not request.is_json:
        return jsonify({'error': 'Invalid Content-Type, application/json expected.'}), 400

    data = request.get_json(silent=True)
    is_valid, err_msg, cleaned_msg, cleaned_history = ai_service.validate_chat_input(data)

    if not is_valid:
        return jsonify({'error': err_msg}), 400

    try:
        reply = ai_service.call_gemini_api(cleaned_msg, cleaned_history)
        return jsonify({'reply': reply})
    except RuntimeError as re_err:
        err_text = str(re_err)
        # Determine appropriate status code
        status_code = 500
        if '429' in err_text or 'quota' in err_text.lower():
            status_code = 429
        elif '401' in err_text or '403' in err_text or 'unauthorized' in err_text.lower():
            status_code = 401
        elif '404' in err_text or 'not found' in err_text.lower():
            status_code = 404
        elif 'timed out' in err_text.lower():
            status_code = 504

        return jsonify({'error': err_text}), status_code
    except Exception as e:
        logger.error(f"Unexpected error in /api/chat: {e}")
        return jsonify({'error': 'An unexpected server error occurred. Please try again shortly.'}), 500


@app.route('/api/eligibility', methods=['POST'])
def api_eligibility():
    """
    Eligibility Guidance Tool API.
    Accepts candidate criteria JSON and returns tailored recommendations.
    """
    if not request.is_json:
        return jsonify({'error': 'Invalid Content-Type, application/json expected.'}), 400

    criteria = request.get_json(silent=True) or {}
    qualification = str(criteria.get('qualification', '')).strip()

    if not qualification:
        return jsonify({'error': 'Qualification is required.'}), 400

    try:
        report = ai_service.generate_eligibility_report(criteria)
        return jsonify({'report': report})
    except RuntimeError as re_err:
        return jsonify({'error': str(re_err)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in /api/eligibility: {e}")
        return jsonify({'error': 'Failed to generate eligibility report. Please try again.'}), 500


@app.route('/api/saved', methods=['GET', 'POST'])
@login_required
def api_saved_guidance():
    """Fetch or Save guidance items for the current user."""
    user = get_current_user()

    if request.method == 'GET':
        items = database.get_saved_guidance(user['id'])
        items_list = [dict(item) for item in items]
        return jsonify({'items': items_list})

    # POST - Save new item
    data = request.get_json(silent=True) or {}
    title = str(data.get('title', 'Career Guidance')).strip()
    category = str(data.get('category', 'General')).strip()
    content = str(data.get('content', '')).strip()

    if not content:
        return jsonify({'error': 'Content cannot be empty.'}), 400

    try:
        item_id = database.save_guidance(user['id'], title, category, content)
        return jsonify({'success': True, 'id': item_id, 'message': 'Guidance saved successfully.'})
    except Exception as e:
        logger.error(f"Error saving guidance: {e}")
        return jsonify({'error': 'Failed to save guidance.'}), 500


@app.route('/api/saved/<int:item_id>', methods=['DELETE'])
@login_required
def api_delete_saved(item_id):
    """Delete a saved guidance item."""
    user = get_current_user()
    try:
        success = database.delete_saved_guidance(user['id'], item_id)
        if success:
            return jsonify({'success': True, 'message': 'Item removed successfully.'})
        return jsonify({'error': 'Item not found or unauthorized.'}), 404
    except Exception as e:
        logger.error(f"Error deleting saved guidance {item_id}: {e}")
        return jsonify({'error': 'Failed to delete item.'}), 500


@app.route('/api/profile', methods=['POST'])
@login_required
def api_update_profile():
    """Update profile preferences and display name."""
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    name = str(data.get('name', '')).strip()
    if name and len(name) >= 2:
        database.update_user_name(user['id'], name)
        session['user_name'] = name

    profile_data = {
        'qualification': data.get('qualification', ''),
        'study_status': data.get('study_status', ''),
        'branch': data.get('branch', ''),
        'age': data.get('age', 0),
        'state': data.get('state', ''),
        'preferred_dept': data.get('preferred_dept', ''),
        'career_preference': data.get('career_preference', '')
    }

    try:
        database.update_user_profile(user['id'], profile_data)
        return jsonify({'success': True, 'message': 'Profile updated successfully.'})
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return jsonify({'error': 'Failed to update profile.'}), 500


@app.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Change user password."""
    user = database.get_user_by_id(session['user_id'])
    # Need user with password_hash
    with database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE id = ?;', (user['id'],))
        row = cursor.fetchone()
        password_hash = row['password_hash'] if row else None

    data = request.get_json(silent=True) or {}
    current_pwd = data.get('current_password', '')
    new_pwd = data.get('new_password', '')
    confirm_pwd = data.get('confirm_password', '')

    if not current_pwd or not new_pwd:
        return jsonify({'error': 'All password fields are required.'}), 400

    if not password_hash or not check_password_hash(password_hash, current_pwd):
        return jsonify({'error': 'Current password is incorrect.'}), 400

    if len(new_pwd) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long.'}), 400

    if new_pwd != confirm_pwd:
        return jsonify({'error': 'New passwords do not match.'}), 400

    new_hash = generate_password_hash(new_pwd)
    database.update_user_password(user['id'], new_hash)
    return jsonify({'success': True, 'message': 'Password changed successfully.'})


@app.route('/api/auth-status', methods=['GET'])
def api_auth_status():
    """Return current session status."""
    user = get_current_user()
    if user:
        return jsonify({
            'logged_in': True,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email']
            }
        })
    return jsonify({'logged_in': False, 'user': None})


# --- Error Handlers ---

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error_notice="The requested page was not found."), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('index.html', error_notice="An internal server error occurred."), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    logger.info(f"Starting Government Job Guide on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
