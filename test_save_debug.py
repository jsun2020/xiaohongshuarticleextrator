#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug script to test user creation and note saving independently
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))
from auth_utils import hash_password

def test_user_and_save():
    # Create a test database
    db = XiaohongshuDatabase("test_debug.db")
    
    # Create a test user
    username = "testuser_debug"
    password_hash = hash_password("testpass123")
    email = "test@example.com"
    nickname = "Test User"
    
    print("=== Creating Test User ===")
    user_id = db.create_user(username, password_hash, email, nickname)
    print(f"Created user_id: {user_id}, type: {type(user_id)}")
    
    if not user_id:
        print("❌ Failed to create user")
        return
    
    # Verify user exists
    user = db.get_user_by_username(username)
    print(f"Retrieved user: {user}")
    print(f"User ID from database: {user['id']}, type: {type(user['id'])}")
    
    # Test note data (simplified)
    test_note_data = {
        'note_id': 'test_note_123',
        'title': 'Test Note Title',
        'content': 'Test note content',
        'type': 'normal',
        'publish_time': '2024-01-01 12:00:00',
        'location': 'Test Location',
        'original_url': 'https://test.com/note/123',
        'author': {
            'user_id': 'xiaohongshu_author_123',
            'nickname': 'XHS Author',
            'avatar': 'https://test.com/avatar.jpg'
        },
        'stats': {
            'likes': 100,
            'collects': 50,
            'comments': 20,
            'shares': 5
        },
        'tags': ['测试', '标签'],
        'images': ['https://test.com/image1.jpg'],
        'videos': []
    }
    
    print("\n=== Testing Note Save ===")
    save_result = db.save_note(test_note_data, user_id)
    print(f"Save result: {save_result}")
    
    # Verify note was saved
    print("\n=== Verifying Note ===")
    notes = db.get_notes_list(user_id, limit=10)
    print(f"Found {len(notes)} notes for user {user_id}")
    for note in notes:
        print(f"  - {note['note_id']}: {note['title']}")

if __name__ == "__main__":
    test_user_and_save()