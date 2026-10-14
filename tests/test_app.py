"""
Unit and Integration Tests for Government Job Guide – AI Career Assistant.
Tests cover authentication, route protection, input validation,
API chat handling, eligibility evaluation, and saved guidance CRUD.
"""

import os
import pytest
import tempfile
from werkzeug.security import generate_password_hash, check_password_hash

# Set test environment
os.environ['SECRET_KEY'] = 'test_secret_key_12345'
os.environ['FLASK_ENV'] = 'testing'

import app as flask_app_module
import database
import ai_service


@pytest.fixture
def client(monkeypatch):
    """Create a temporary test database and Flask test client."""
    db_fd, temp_db_path = tempfile.mkstemp()
    monkeypatch.setattr(database, 'DATABASE_PATH', temp_db_path)

    # Initialize tables
    database.init_db()

    flask_app = flask_app_module.app
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False

    with flask_app.test_client() as client:
        yield client

    os.close(db_fd)
    try:
        os.unlink(temp_db_path)
    except OSError:
        pass


def test_public_pages_render(client):
    """Test that all public pages return HTTP 200."""
    routes = ['/', '/jobs', '/eligibility', '/preparation', '/chat', '/login', '/register']
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, f"Failed on route {route}"
        assert b"GovtJob" in response.data or b"Government" in response.data


def test_protected_routes_redirect(client):
    """Test that protected pages redirect unauthenticated users to /login."""
    protected_routes = ['/dashboard', '/saved', '/profile']
    for route in protected_routes:
        response = client.get(route, follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']


def test_registration_and_duplicate_prevention(client):
    """Test user registration flow and rejection of duplicate emails."""
    # 1. Valid registration
    res = client.post('/register', data={
        'name': 'Aarav Patel',
        'email': 'aarav@example.com',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=False)
    assert res.status_code == 302
    assert '/dashboard' in res.headers['Location']

    # Log out to test unauthenticated attempts
    client.get('/logout')

    # 2. Duplicate registration attempt
    res_dup = client.post('/register', data={
        'name': 'Aarav Patel 2',
        'email': 'aarav@example.com',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)
    assert b"already exists" in res_dup.data

    # 3. Password mismatch attempt
    res_mismatch = client.post('/register', data={
        'name': 'Other User',
        'email': 'other@example.com',
        'password': 'Password123',
        'confirm_password': 'DifferentPassword'
    }, follow_redirects=True)
    assert b"Passwords do not match" in res_mismatch.data

    # 4. Short password attempt
    res_short = client.post('/register', data={
        'name': 'Other User',
        'email': 'other2@example.com',
        'password': '123',
        'confirm_password': '123'
    }, follow_redirects=True)
    assert b"at least 6 characters" in res_short.data


def test_login_and_logout(client):
    """Test valid and invalid login, and logout session clearance."""
    # Create test user
    pwd_hash = generate_password_hash('SecretPass123')
    database.create_user('Priya Sharma', 'priya@example.com', pwd_hash)

    # Invalid password
    res_fail = client.post('/login', data={
        'email': 'priya@example.com',
        'password': 'WrongPassword'
    }, follow_redirects=True)
    assert b"Invalid email or password" in res_fail.data

    # Valid login
    res_ok = client.post('/login', data={
        'email': 'priya@example.com',
        'password': 'SecretPass123'
    }, follow_redirects=False)
    assert res_ok.status_code == 302
    assert '/dashboard' in res_ok.headers['Location']

    # Access dashboard after login
    res_dash = client.get('/dashboard')
    assert res_dash.status_code == 200
    assert b"Priya Sharma" in res_dash.data

    # Logout
    res_logout = client.get('/logout', follow_redirects=True)
    assert b"logged out successfully" in res_logout.data

    # Verify dashboard now blocked
    res_blocked = client.get('/dashboard', follow_redirects=False)
    assert res_blocked.status_code == 302


def test_chat_api_validation(client):
    """Test /api/chat input validation rules."""
    # 1. Non-JSON request
    res_non_json = client.post('/api/chat', data="plain text")
    assert res_non_json.status_code == 400

    # 2. Missing message
    res_no_msg = client.post('/api/chat', json={})
    assert res_no_msg.status_code == 400
    assert "Message field is required" in res_no_msg.get_json()['error']

    # 3. Empty whitespace message
    res_empty_msg = client.post('/api/chat', json={'message': '   '})
    assert res_empty_msg.status_code == 400
    assert "cannot be empty" in res_empty_msg.get_json()['error']

    # 4. Oversized message (>2500 chars)
    res_long_msg = client.post('/api/chat', json={'message': 'A' * 3000})
    assert res_long_msg.status_code == 400
    assert "maximum allowed length" in res_long_msg.get_json()['error']

    # 5. Valid message returns reply
    res_valid = client.post('/api/chat', json={
        'message': 'Jobs after 12th',
        'history': []
    })
    assert res_valid.status_code == 200
    data = res_valid.get_json()
    assert 'reply' in data
    assert len(data['reply']) > 50


def test_eligibility_api(client):
    """Test /api/eligibility returns structured career guidance."""
    # Missing qualification
    res_fail = client.post('/api/eligibility', json={})
    assert res_fail.status_code == 400

    # Valid criteria
    res_ok = client.post('/api/eligibility', json={
        'qualification': 'B.Tech / B.E. (Engineering)',
        'study_status': 'Completed / Degree Awarded',
        'branch': 'Computer Science & Engineering',
        'age': 22,
        'state': 'Maharashtra',
        'department': 'Technical PSUs & R&D',
        'career_preference': 'Purely Technical / Engineering Roles'
    })
    assert res_ok.status_code == 200
    data = res_ok.get_json()
    assert 'report' in data
    assert len(data['report']) > 100


def test_saved_guidance_crud_and_isolation(client):
    """Test saving, retrieving, and deleting guidance with user isolation."""
    # Create two users
    pwd_hash = generate_password_hash('Password123')
    user1_id = database.create_user('User One', 'user1@example.com', pwd_hash)
    user2_id = database.create_user('User Two', 'user2@example.com', pwd_hash)

    # 1. Unauthenticated API access blocked
    res_unauth = client.get('/api/saved')
    assert res_unauth.status_code == 401

    # 2. Login as User 1
    client.post('/login', data={'email': 'user1@example.com', 'password': 'Password123'})

    # 3. Save guidance for User 1
    res_save = client.post('/api/saved', json={
        'title': 'SSC Preparation Roadmap',
        'category': 'SSC',
        'content': 'Comprehensive guide for SSC CGL Tier 1 and 2.'
    })
    assert res_save.status_code == 200
    save_data = res_save.get_json()
    item_id = save_data['id']

    # 4. Retrieve saved items for User 1
    res_items = client.get('/api/saved')
    assert res_items.status_code == 200
    items = res_items.get_json()['items']
    assert len(items) == 1
    assert items[0]['title'] == 'SSC Preparation Roadmap'

    # 5. Switch to User 2
    client.get('/logout')
    client.post('/login', data={'email': 'user2@example.com', 'password': 'Password123'})

    # User 2 sees 0 items
    res_u2_items = client.get('/api/saved')
    assert len(res_u2_items.get_json()['items']) == 0

    # User 2 cannot delete User 1's item
    res_del_hack = client.delete(f'/api/saved/{item_id}')
    assert res_del_hack.status_code == 404

    # 6. Switch back to User 1 and delete
    client.get('/logout')
    client.post('/login', data={'email': 'user1@example.com', 'password': 'Password123'})

    res_del_ok = client.delete(f'/api/saved/{item_id}')
    assert res_del_ok.status_code == 200
    assert res_del_ok.get_json()['success'] is True

    # Verify deleted
    res_after = client.get('/api/saved')
    assert len(res_after.get_json()['items']) == 0


def test_profile_update_and_password_change(client):
    """Test user profile preferences update and password changing."""
    pwd_hash = generate_password_hash('OldPassword123')
    user_id = database.create_user('Rahul Varma', 'rahul@example.com', pwd_hash)

    # Login as Rahul
    client.post('/login', data={'email': 'rahul@example.com', 'password': 'OldPassword123'})

    # Update profile preferences
    res_prof = client.post('/api/profile', json={
        'name': 'Rahul K. Varma',
        'qualification': 'B.Tech / B.E. (Engineering)',
        'branch': 'Civil Engineering',
        'age': 23,
        'state': 'Uttar Pradesh',
        'preferred_dept': 'Central Administrative (SSC/UPSC)'
    })
    assert res_prof.status_code == 200
    assert res_prof.get_json()['success'] is True

    # Check updated name in DB
    updated_user = database.get_user_by_id(user_id)
    assert updated_user['name'] == 'Rahul K. Varma'

    # Check profile DB row
    prof = database.get_user_profile(user_id)
    assert prof['branch'] == 'Civil Engineering'
    assert prof['age'] == 23

    # Attempt password change with wrong old password
    res_pw_fail = client.post('/api/change-password', json={
        'current_password': 'WrongPassword',
        'new_password': 'NewPassword123',
        'confirm_password': 'NewPassword123'
    })
    assert res_pw_fail.status_code == 400
    assert "Current password is incorrect" in res_pw_fail.get_json()['error']

    # Change password successfully
    res_pw_ok = client.post('/api/change-password', json={
        'current_password': 'OldPassword123',
        'new_password': 'NewPassword123',
        'confirm_password': 'NewPassword123'
    })
    assert res_pw_ok.status_code == 200
    assert res_pw_ok.get_json()['success'] is True

    # Logout and verify login with new password
    client.get('/logout')
    res_new_login = client.post('/login', data={
        'email': 'rahul@example.com',
        'password': 'NewPassword123'
    }, follow_redirects=False)
    assert res_new_login.status_code == 302
    assert '/dashboard' in res_new_login.headers['Location']

