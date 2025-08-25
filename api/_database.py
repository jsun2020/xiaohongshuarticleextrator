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
            # 开发环境使用SQLite
            self.db_path = 'xiaohongshu_notes.db'
    
    def get_connection(self):
        """获取数据库连接"""
        if self.use_postgres:
            import psycopg2
            return psycopg2.connect(**self.pg_config)
        else:
            return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
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
            author_json = json.dumps(note_data.get('author', {}), ensure_ascii=False)
            stats_json = json.dumps(note_data.get('stats', {}), ensure_ascii=False)
            images_json = json.dumps(note_data.get('images', []), ensure_ascii=False)
            
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
            return True
            
        except Exception as e:
            print(f"保存笔记失败: {e}")
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

# 全局数据库实例
db = DatabaseManager()