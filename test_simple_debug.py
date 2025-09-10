#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple debug script to test note saving
"""

import sqlite3
import os

def create_test_db():
    """Create a simple test database"""
    db_path = "test_simple.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create simple users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            nickname TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create simple notes table
    cursor.execute('''
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            note_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, note_id)
        )
    ''')
    
    conn.commit()
    return conn

def test_simple_save():
    print("=== Creating Test Database ===")
    conn = create_test_db()
    cursor = conn.cursor()
    
    # Create test user
    print("=== Creating Test User ===")
    cursor.execute("INSERT INTO users (username, password_hash, email, nickname) VALUES (?, ?, ?, ?)",
                   ("testuser", "testhash", "test@example.com", "Test User"))
    user_id = cursor.lastrowid
    print(f"Created user_id: {user_id}, type: {type(user_id)}")
    
    # Verify user exists
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    user_exists = cursor.fetchone()
    print(f"User exists check: {user_exists is not None}")
    
    # Test saving a note
    print("=== Testing Note Save ===")
    try:
        cursor.execute("INSERT INTO notes (user_id, note_id, title, content) VALUES (?, ?, ?, ?)",
                       (user_id, "test_note_123", "Test Title", "Test Content"))
        print("Note inserted successfully")
        conn.commit()
        print("Transaction committed successfully")
        
        # Verify note was saved
        cursor.execute("SELECT * FROM notes WHERE user_id = ?", (user_id,))
        notes = cursor.fetchall()
        print(f"Found {len(notes)} notes for user {user_id}")
        for note in notes:
            print(f"  Note: {note}")
            
    except Exception as e:
        print(f"Error saving note: {e}")
        import traceback
        traceback.print_exc()
    
    conn.close()

if __name__ == "__main__":
    test_simple_save()