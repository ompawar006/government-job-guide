"""
Database module for Government Job Guide – AI Career Assistant.
Uses SQLite for persistent storage of users, profiles, and saved AI guidance.
"""

import os
import sqlite3
from datetime import datetime

DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'database.db')


def ensure_db_dir():
    """Ensure the instance directory exists."""
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR, exist_ok=True)


def get_db():
    """Get a database connection with row factory configured."""
    ensure_db_dir()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initialize database tables if they do not already exist."""
    ensure_db_dir()
    with get_db() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Saved AI Guidance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_guidance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        ''')

        # User Profile & Preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                qualification TEXT DEFAULT '',
                study_status TEXT DEFAULT '',
                branch TEXT DEFAULT '',
                age INTEGER DEFAULT 0,
                state TEXT DEFAULT '',
                preferred_dept TEXT DEFAULT '',
                career_preference TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        ''')

        conn.commit()


# --- User Management Operations ---

def create_user(name: str, email: str, password_hash: str):
    """Create a new user and initialize an empty profile."""
    email_clean = email.strip().lower()
    name_clean = name.strip()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?);',
            (name_clean, email_clean, password_hash)
        )
        user_id = cursor.lastrowid

        # Initialize profile row
        cursor.execute(
            'INSERT INTO user_profiles (user_id) VALUES (?);',
            (user_id,)
        )
        conn.commit()
        return user_id


def get_user_by_email(email: str):
    """Retrieve user record by email address."""
    email_clean = email.strip().lower()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?;', (email_clean,))
        return cursor.fetchone()


def get_user_by_id(user_id: int):
    """Retrieve user record by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, created_at FROM users WHERE id = ?;', (user_id,))
        return cursor.fetchone()


def update_user_name(user_id: int, name: str):
    """Update user's display name."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET name = ? WHERE id = ?;', (name.strip(), user_id))
        conn.commit()
        return cursor.rowcount > 0


def update_user_password(user_id: int, new_password_hash: str):
    """Update user's password hash."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?;', (new_password_hash, user_id))
        conn.commit()
        return cursor.rowcount > 0


# --- User Profile Operations ---

def get_user_profile(user_id: int):
    """Get the profile preferences for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?;', (user_id,))
        row = cursor.fetchone()
        if not row:
            # Create default if missing
            cursor.execute('INSERT OR IGNORE INTO user_profiles (user_id) VALUES (?);', (user_id,))
            conn.commit()
            cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?;', (user_id,))
            row = cursor.fetchone()
        return row


def update_user_profile(user_id: int, profile: dict):
    """Update user profile preferences."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_profiles (user_id, qualification, study_status, branch, age, state, preferred_dept, career_preference, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                qualification = excluded.qualification,
                study_status = excluded.study_status,
                branch = excluded.branch,
                age = excluded.age,
                state = excluded.state,
                preferred_dept = excluded.preferred_dept,
                career_preference = excluded.career_preference,
                updated_at = CURRENT_TIMESTAMP;
        ''', (
            user_id,
            profile.get('qualification', ''),
            profile.get('study_status', ''),
            profile.get('branch', ''),
            int(profile.get('age', 0) or 0),
            profile.get('state', ''),
            profile.get('preferred_dept', ''),
            profile.get('career_preference', '')
        ))
        conn.commit()
        return True


# --- Saved Guidance Operations ---

def save_guidance(user_id: int, title: str, category: str, content: str):
    """Save an AI career guidance recommendation for a user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO saved_guidance (user_id, title, category, content)
            VALUES (?, ?, ?, ?);
        ''', (user_id, title.strip() or 'Career Guidance', category.strip() or 'General', content.strip()))
        conn.commit()
        return cursor.lastrowid


def get_saved_guidance(user_id: int):
    """Retrieve all saved guidance for a user, ordered newest first."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, category, content, created_at
            FROM saved_guidance
            WHERE user_id = ?
            ORDER BY created_at DESC;
        ''', (user_id,))
        return cursor.fetchall()


def get_saved_guidance_item(user_id: int, item_id: int):
    """Retrieve a specific saved guidance item, ensuring user owns it."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, category, content, created_at
            FROM saved_guidance
            WHERE id = ? AND user_id = ?;
        ''', (item_id, user_id))
        return cursor.fetchone()


def delete_saved_guidance(user_id: int, item_id: int):
    """Delete a saved guidance item owned by the user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM saved_guidance WHERE id = ? AND user_id = ?;', (item_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
