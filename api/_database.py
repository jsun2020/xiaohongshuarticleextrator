"""
Vercel兼容的数据库管理
支持PostgreSQL和SQLite
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any

class DatabaseManager:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.use_postgres = self.db_url and self.db_url.startswith('postgres')
        
        if self.use_postgres:
            import psycopg2
            from urllib.parse import urlparse
            
            # 解析PostgreSQL URL
            url = urlparse(self.db_url)
            self.pg_config = {
                'host': url.hostname,
                'port': url.port or 5432,
                'database': url.path[1:],
                'user': url.username,
                'password': url.password
            }
        else:
            # 开发环境使用SQLite - 强制使用固定的项目目录路径
            # Vercel每个函数都有独立的临时目录，所以需要使用固定路径
            project_root = r'C:\Users\sr9rfx\.claude\xiaohongshuarticleextrator'
            self.db_path = os.path.join(project_root, 'xiaohongshu_notes.db')
            print(f"[DB] Using fixed database path: {self.db_path}")
    
    def get_connection(self):
        """获取数据库连接"""
        if self.use_postgres:
            try:
                import psycopg2
                return psycopg2.connect(**self.pg_config)
            except ImportError:
                import psycopg2
                return psycopg2.connect(**self.pg_config)
            except Exception as e:
                print(f"PostgreSQL连接失败: {e}")
                raise
        else:
            return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """初始化数据库表"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
        
        try:
            if self.use_postgres:
                # PostgreSQL建表语句
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        email VARCHAR(100),
                        nickname VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_configs (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        config_key VARCHAR(100) NOT NULL,
                        config_value TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        UNIQUE(user_id, config_key)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notes (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        note_id VARCHAR(100) NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT,
                        note_type VARCHAR(50),
                        publish_time VARCHAR(100),
                        location VARCHAR(200),
                        original_url TEXT,
                        author_data TEXT,
                        stats_data TEXT,
                        images_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recreate_history (
                        id SERIAL PRIMARY KEY,
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
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_usage (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        usage_type VARCHAR(50) NOT NULL,
                        usage_count INTEGER DEFAULT 0,
                        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        UNIQUE(user_id, usage_type)
                    )
                ''')
            else:
                # SQLite建表语句
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        email TEXT,
                        nickname TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        config_key TEXT NOT NULL,
                        config_value TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        UNIQUE(user_id, config_key)
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
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
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recreate_history (
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
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        usage_type TEXT NOT NULL,
                        usage_count INTEGER DEFAULT 0,
                        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        UNIQUE(user_id, usage_type)
                    )
                ''')
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            return False
        finally:
            conn.close()
    
    def create_user(self, username: str, password_hash: str, email: str = None, nickname: str = None) -> Optional[int]:
        """创建用户"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, nickname)
                    VALUES (%s, %s, %s, %s) RETURNING id
                ''', (username, password_hash, email, nickname))
                user_id = cursor.fetchone()[0]
            else:
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, nickname)
                    VALUES (?, ?, ?, ?)
                ''', (username, password_hash, email, nickname))
                user_id = cursor.lastrowid
            
            conn.commit()
            return user_id
            
        except Exception as e:
            print(f"创建用户失败: {e}")
            return None
        finally:
            conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgres:
                cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            else:
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            print(f"获取用户失败: {e}")
            return None
        finally:
            conn.close()
    
    def save_note(self, note_data: Dict, user_id: int) -> bool:
        """保存笔记"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if note already exists
            if self.use_postgres:
                cursor.execute('SELECT id FROM notes WHERE note_id = %s', (note_data.get('note_id'),))
            else:
                cursor.execute('SELECT id FROM notes WHERE note_id = ?', (note_data.get('note_id'),))
            
            existing = cursor.fetchone()
            if existing:
                print(f"[SAVE] Note {note_data.get('note_id')} already exists in database")
                return False  # Note already exists
            
            # 处理JSON数据
            author_json = json.dumps(note_data.get('author', {}), ensure_ascii=False)
            stats_json = json.dumps(note_data.get('stats', {}), ensure_ascii=False)
            
            # 处理图片和视频数据
            images_data = note_data.get('images', [])
            videos_data = note_data.get('videos', [])
            # 合并图片和视频到images_data字段
            all_media = {
                'images': images_data,
                'videos': videos_data
            }
            images_json = json.dumps(all_media, ensure_ascii=False)
            
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO notes (user_id, note_id, title, content, note_type, 
                                     publish_time, location, original_url, author_data, 
                                     stats_data, images_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (user_id, note_data.get('note_id'), note_data.get('title'),
                      note_data.get('content'), note_data.get('type'),
                      note_data.get('publish_time'), note_data.get('location'),
                      note_data.get('original_url'), author_json, stats_json, images_json))
            else:
                cursor.execute('''
                    INSERT INTO notes (user_id, note_id, title, content, note_type, 
                                     publish_time, location, original_url, author_data, 
                                     stats_data, images_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, note_data.get('note_id'), note_data.get('title'),
                      note_data.get('content'), note_data.get('type'),
                      note_data.get('publish_time'), note_data.get('location'),
                      note_data.get('original_url'), author_json, stats_json, images_json))
            
            conn.commit()
            print(f"[SAVE] Committed to database for note_id: {note_data.get('note_id')}")
            
            # Force verify the insert worked
            if not self.use_postgres:
                cursor.execute("SELECT last_insert_rowid()")  
                new_id = cursor.fetchone()[0]
                print(f"[SAVE] New row ID: {new_id}")
                if not new_id:
                    print(f"[SAVE] ERROR: No row ID returned")
                    return False
            return True
            
        except Exception as e:
            print(f"[SAVE] ERROR: 保存笔记失败: {e}")
            conn.rollback()  # Explicit rollback on error
            return False
        finally:
            conn.close()
    
    def get_notes(self, user_id: int, page: int = 1, per_page: int = 10) -> List[Dict]:
        """获取用户笔记列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            offset = (page - 1) * per_page
            
            if self.use_postgres:
                cursor.execute('''
                    SELECT * FROM notes WHERE user_id = %s 
                    ORDER BY created_at DESC LIMIT %s OFFSET %s
                ''', (user_id, per_page, offset))
            else:
                cursor.execute('''
                    SELECT * FROM notes WHERE user_id = ? 
                    ORDER BY created_at DESC LIMIT ? OFFSET ?
                ''', (user_id, per_page, offset))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            notes = []
            for row in rows:
                note = dict(zip(columns, row))
                # 解析JSON字段
                try:
                    note['author_data'] = json.loads(note['author_data']) if note['author_data'] else {}
                    note['stats_data'] = json.loads(note['stats_data']) if note['stats_data'] else {}
                    note['images_data'] = json.loads(note['images_data']) if note['images_data'] else []
                except:
                    pass
                notes.append(note)
            
            return notes
            
        except Exception as e:
            print(f"获取笔记列表失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_notes_count(self, user_id: int) -> int:
        """获取用户笔记总数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgres:
                cursor.execute('SELECT COUNT(*) FROM notes WHERE user_id = %s', (user_id,))
            else:
                cursor.execute('SELECT COUNT(*) FROM notes WHERE user_id = ?', (user_id,))
            
            count = cursor.fetchone()[0]
            return count
            
        except Exception as e:
            print(f"获取笔记数量失败: {e}")
            return 0
        finally:
            conn.close()
    
    def get_user_config(self, user_id: int) -> Dict:
        """获取用户配置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgres:
                cursor.execute('SELECT config_key, config_value FROM user_configs WHERE user_id = %s', (user_id,))
            else:
                cursor.execute('SELECT config_key, config_value FROM user_configs WHERE user_id = ?', (user_id,))
            
            rows = cursor.fetchall()
            return {row[0]: row[1] for row in rows}
            
        except Exception as e:
            print(f"获取用户配置失败: {e}")
            return {}
        finally:
            conn.close()
    
    def set_user_config(self, user_id: int, key: str, value: str) -> bool:
        """设置用户配置"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO user_configs (user_id, config_key, config_value)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, config_key) 
                    DO UPDATE SET config_value = EXCLUDED.config_value
                ''', (user_id, key, value))
            else:
                cursor.execute('''
                    INSERT OR REPLACE INTO user_configs (user_id, config_key, config_value)
                    VALUES (?, ?, ?)
                ''', (user_id, key, value))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"设置用户配置失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_usage(self, user_id: int, usage_type: str) -> int:
        """获取用户使用次数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgres:
                cursor.execute('SELECT usage_count FROM user_usage WHERE user_id = %s AND usage_type = %s', (user_id, usage_type))
            else:
                cursor.execute('SELECT usage_count FROM user_usage WHERE user_id = ? AND usage_type = ?', (user_id, usage_type))
            
            row = cursor.fetchone()
            return row[0] if row else 0
            
        except Exception as e:
            print(f"获取用户使用次数失败: {e}")
            return 0
        finally:
            conn.close()
    
    def increment_user_usage(self, user_id: int, usage_type: str) -> bool:
        """增加用户使用次数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.use_postgres:
                cursor.execute('''
                    INSERT INTO user_usage (user_id, usage_type, usage_count, last_used)
                    VALUES (%s, %s, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id, usage_type)
                    DO UPDATE SET usage_count = user_usage.usage_count + 1, last_used = CURRENT_TIMESTAMP
                ''', (user_id, usage_type))
            else:
                cursor.execute('''
                    INSERT OR REPLACE INTO user_usage (user_id, usage_type, usage_count, last_used)
                    VALUES (?, ?, COALESCE((SELECT usage_count FROM user_usage WHERE user_id = ? AND usage_type = ?), 0) + 1, CURRENT_TIMESTAMP)
                ''', (user_id, usage_type, user_id, usage_type))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"增加用户使用次数失败: {e}")
            return False
        finally:
            conn.close()

# 全局数据库实例
db = DatabaseManager()