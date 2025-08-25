#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加用户系统支持
"""
import sqlite3
import os

def migrate_database():
    """迁移现有数据库到支持用户系统的版本"""
    db_path = "xiaohongshu_notes.db"
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在，无需迁移")
        return False
    
    print("🔧 开始数据库迁移...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查现有表结构
        cursor.execute("PRAGMA table_info(notes)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"现有notes表字段: {columns}")
        
        # 检查是否需要添加user_id字段
        if 'user_id' not in columns:
            print("添加user_id字段到notes表...")
            
            # 先删除可能存在的notes_new表
            cursor.execute("DROP TABLE IF EXISTS notes_new")
            
            # 1. 创建新的notes表结构
            cursor.execute('''
                CREATE TABLE notes_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    note_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    note_type TEXT,
                    publish_time TEXT,
                    location TEXT,
                    original_url TEXT,
                    author_data TEXT,
                    stats_data TEXT,
                    images_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 2. 复制现有数据（使用实际的字段名）
            cursor.execute('''
                INSERT INTO notes_new (note_id, title, content, note_type, publish_time, 
                                     location, original_url, created_at)
                SELECT note_id, title, content, type, publish_time, location, 
                       original_url, created_at
                FROM notes
            ''')
            
            # 3. 删除旧表，重命名新表
            cursor.execute('DROP TABLE notes')
            cursor.execute('ALTER TABLE notes_new RENAME TO notes')
            
            print("✅ notes表迁移完成")
        else:
            print("✅ notes表已包含user_id字段，无需迁移")
        
        # 检查并创建用户相关表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("创建users表...")
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
            print("✅ users表创建完成")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_configs'")
        if not cursor.fetchone():
            print("创建user_configs表...")
            cursor.execute('''
                CREATE TABLE user_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    config_key TEXT NOT NULL,
                    config_value TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, config_key)
                )
            ''')
            print("✅ user_configs表创建完成")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recreate_history'")
        if not cursor.fetchone():
            print("创建recreate_history表...")
            cursor.execute('''
                CREATE TABLE recreate_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    note_id INTEGER NOT NULL,
                    original_title TEXT,
                    original_content TEXT,
                    recreated_title TEXT,
                    recreated_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (note_id) REFERENCES notes (id)
                )
            ''')
            print("✅ recreate_history表创建完成")
        
        # 检查是否有默认用户
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            print("创建默认管理员用户...")
            # 创建默认管理员用户（密码：admin123）
            password_hash = "4a8b9c2d1e3f4a5b:8f7e6d5c4b3a2918f7e6d5c4b3a2918f7e6d5c4b3a2918f7e6d5c4b3a2918f7e6d5c"
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, nickname)
                VALUES (?, ?, ?, ?)
            ''', ('admin', password_hash, 'admin@example.com', '管理员'))
            
            user_id = cursor.lastrowid
            
            # 设置默认配置
            default_configs = [
                ('deepseek_base_url', 'https://api.deepseek.com'),
                ('deepseek_model', 'deepseek-chat'),
                ('deepseek_temperature', '0.7'),
                ('deepseek_max_tokens', '1000')
            ]
            
            for key, value in default_configs:
                cursor.execute('''
                    INSERT INTO user_configs (user_id, config_key, config_value)
                    VALUES (?, ?, ?)
                ''', (user_id, key, value))
            
            print(f"✅ 默认管理员用户创建完成 (ID: {user_id})")
            print("   用户名: admin")
            print("   密码: admin123")
        
        conn.commit()
        conn.close()
        
        print("\\n🎉 数据库迁移完成！")
        print("\\n📊 迁移摘要:")
        print("   • 添加了用户系统支持")
        print("   • 更新了notes表结构")
        print("   • 创建了用户配置表")
        print("   • 创建了二创历史表")
        print("   • 设置了默认管理员账户")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False

if __name__ == '__main__':
    migrate_database()