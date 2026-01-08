import sqlite3
import os
import bcrypt
from datetime import datetime
import json

DB_FILE = os.getenv("DB_PATH", "data/studio.db")

def get_db_connection():
    if not os.path.exists("data"):
        os.makedirs("data")
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # 1. Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Models Table (Roster)
    c.execute('''
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            face_base64 TEXT,
            body_base64 TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 3. Assets Table (Closet / Locations)
    c.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT NOT NULL, -- 'closet' or 'location'
            name TEXT NOT NULL,
            image_base64 TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 4. Gallery Table (Both Apparel and Accessories)
    c.execute('''
        CREATE TABLE IF NOT EXISTS gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT NOT NULL, -- 'apparel' or 'accessory'
            prompt TEXT,
            image_base64 TEXT NOT NULL,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # MIGRATION: Add password_hint column if it doesn't exist
    try:
        c.execute('ALTER TABLE users ADD COLUMN password_hint TEXT')
    except sqlite3.OperationalError:
        # Column likely already exists
        pass
        
    conn.commit()
    conn.close()

# --- AUTH ---
def create_user(username, password, hint=""):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # Hash password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        c.execute('INSERT INTO users (username, password_hash, password_hint) VALUES (?, ?, ?)', (username, hashed, hint))
        conn.commit()
        conn.close()
        return True, "User created successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    except Exception as e:
        return False, str(e)

def get_user_hint(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT password_hint FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    return row['password_hint'] if row else None

def get_all_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, password_hint, created_at FROM users ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def login_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return user['id']
    return None

# --- MODELS ---
def add_model(user_id, name, face_b64, body_b64):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO models (user_id, name, face_base64, body_base64) VALUES (?, ?, ?, ?)', 
              (user_id, name, face_b64, body_b64))
    conn.commit()
    conn.close()

def get_models(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM models WHERE user_id = ? ORDER BY id DESC', (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows] # Convert to list of dicts

def delete_model(model_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM models WHERE id = ?', (model_id,))
    conn.commit()
    conn.close()

# --- ASSETS (Closet/Locations) ---
def add_asset(user_id, category, name, image_b64):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO assets (user_id, category, name, image_base64) VALUES (?, ?, ?, ?)', 
              (user_id, category, name, image_b64))
    conn.commit()
    conn.close()

def get_assets(user_id, category):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM assets WHERE user_id = ? AND category = ? ORDER BY id DESC', (user_id, category))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_asset(asset_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM assets WHERE id = ?', (asset_id,))
    conn.commit()
    conn.close()

# --- GALLERY ---
def add_gallery_item(user_id, category, prompt, image_b64):
    timestamp = datetime.now().isoformat()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO gallery (user_id, category, prompt, image_base64, timestamp) VALUES (?, ?, ?, ?, ?)', 
              (user_id, category, prompt, image_b64, timestamp))
    conn.commit()
    conn.close()

def get_gallery(user_id, category):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM gallery WHERE user_id = ? AND category = ? ORDER BY id DESC', (user_id, category))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_gallery_item(item_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM gallery WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()

def clear_gallery(user_id, category):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM gallery WHERE user_id = ? AND category = ?', (user_id, category))
    conn.commit()
    conn.close()

# Initial Init
if __name__ == "__main__":
    init_db()
    print("Database initialized.")
