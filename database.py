import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class XiaohongshuDatabase:
    """小红书笔记数据库管理类 - Serverless兼容版本"""
    
    def __init__(self, db_path: str = None):
        # 在Serverless环境中，使用临时目录
        if db_path is None:
            import tempfile
            temp_dir = tempfile.gettempdir()
            self.db_path = os.path.join(temp_dir, "xiaohongshu_notes.db")
        else:
            self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库和表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    nickname TEXT,
                    avatar TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建用户配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    config_key TEXT NOT NULL,
                    config_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, config_key)
                )
            ''')
            
            # 创建笔记主表（添加用户关联）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    note_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    type TEXT,
                    publish_time TEXT,
                    location TEXT,
                    original_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(user_id, note_id)
                )
            ''')
            
            # 创建作者表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS authors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    nickname TEXT NOT NULL,
                    avatar TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建互动数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS note_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id TEXT NOT NULL,
                    likes INTEGER DEFAULT 0,
                    collects INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (note_id) REFERENCES notes (note_id)
                )
            ''')
            
            # 创建标签表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建笔记标签关系表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS note_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id TEXT NOT NULL,
                    tag_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (note_id) REFERENCES notes (note_id),
                    FOREIGN KEY (tag_id) REFERENCES tags (id),
                    UNIQUE(note_id, tag_id)
                )
            ''')
            
            # 创建图片表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS note_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id TEXT NOT NULL,
                    image_url TEXT NOT NULL,
                    image_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (note_id) REFERENCES notes (note_id)
                )
            ''')
            
            # 创建视频表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS note_videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id TEXT NOT NULL,
                    video_url TEXT NOT NULL,
                    video_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (note_id) REFERENCES notes (note_id)
                )
            ''')
            
            # 创建笔记作者关系表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS note_authors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id TEXT NOT NULL,
                    author_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (note_id) REFERENCES notes (note_id),
                    FOREIGN KEY (author_id) REFERENCES authors (id),
                    UNIQUE(note_id, author_id)
                )
            ''')
            
            # 创建二创历史表（添加用户关联）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recreate_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    original_note_id TEXT,
                    original_title TEXT,
                    original_content TEXT,
                    new_title TEXT,
                    new_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (original_note_id) REFERENCES notes (note_id)
                )
            ''')
            
            # 创建视觉故事历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS visual_story_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    history_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    cover_card_data TEXT,
                    content_cards_data TEXT,
                    html_content TEXT,
                    model_used TEXT DEFAULT 'gemini-2.5-flash-image',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (history_id) REFERENCES recreate_history (id)
                )
            ''')
            
            # 创建用户使用统计表
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
            print("数据库表初始化完成")
    
    def create_user(self, username: str, password_hash: str, email: str = None, nickname: str = None) -> Optional[int]:
        """创建新用户"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, nickname)
                    VALUES (?, ?, ?, ?)
                ''', (username, password_hash, email, nickname or username))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                # 验证用户是否成功创建
                cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
                created_user = cursor.fetchone()
                if created_user:
                    print(f"用户 {username} 创建成功，ID: {user_id} (数据库: {self.db_path})")
                    return user_id
                else:
                    print(f"用户创建验证失败: {username}")
                    return None
                
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                print(f"用户名 {username} 已存在")
            elif 'email' in str(e):
                print(f"邮箱 {email} 已存在")
            else:
                print(f"创建用户失败: {str(e)}")
            return None
        except Exception as e:
            print(f"创建用户失败: {str(e)}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, username, email, password_hash, nickname, avatar, is_active, created_at
                    FROM users WHERE username = ? AND is_active = 1
                ''', (username,))
                
                user = cursor.fetchone()
                if user:
                    print(f"用户登录验证: {username} (ID: {user['id']}, 数据库: {self.db_path})")
                    return dict(user)
                else:
                    print(f"用户未找到或已停用: {username} (数据库: {self.db_path})")
                    return None
                
        except Exception as e:
            print(f"获取用户信息失败: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据用户ID获取用户信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, username, email, nickname, avatar, is_active, created_at
                    FROM users WHERE id = ? AND is_active = 1
                ''', (user_id,))
                
                user = cursor.fetchone()
                return dict(user) if user else None
                
        except Exception as e:
            print(f"❌ 获取用户信息失败: {str(e)}")
            return None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """更新用户信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建更新字段
                update_fields = []
                values = []
                
                for field in ['email', 'nickname', 'avatar', 'password_hash']:
                    if field in kwargs:
                        update_fields.append(f"{field} = ?")
                        values.append(kwargs[field])
                
                if not update_fields:
                    return True
                
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                values.append(user_id)
                
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, values)
                
                conn.commit()
                print(f"✅ 用户 {user_id} 信息更新成功")
                return True
                
        except Exception as e:
            print(f"❌ 更新用户信息失败: {str(e)}")
            return False
    
    def get_user_config(self, user_id: int, config_key: str = None) -> Dict:
        """获取用户配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if config_key:
                    cursor.execute('''
                        SELECT config_value FROM user_configs 
                        WHERE user_id = ? AND config_key = ?
                    ''', (user_id, config_key))
                    result = cursor.fetchone()
                    return result['config_value'] if result else None
                else:
                    cursor.execute('''
                        SELECT config_key, config_value FROM user_configs 
                        WHERE user_id = ?
                    ''', (user_id,))
                    results = cursor.fetchall()
                    return {row['config_key']: row['config_value'] for row in results}
                
        except Exception as e:
            print(f"❌ 获取用户配置失败: {str(e)}")
            return {} if not config_key else None
    
    def set_user_config(self, user_id: int, config_key: str, config_value: str) -> bool:
        """设置用户配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO user_configs 
                    (user_id, config_key, config_value, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, config_key, config_value))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 设置用户配置失败: {str(e)}")
            return False
    
    def save_note(self, note_data: Dict, user_id: int) -> bool:
        """保存笔记数据到数据库"""
        if not user_id or not isinstance(user_id, int):
            print(f"Invalid user_id: {user_id} (type: {type(user_id)})")
            return False
            
        if not note_data or not note_data.get('note_id'):
            print(f"Invalid note_data: missing note_id")
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('PRAGMA foreign_keys = OFF')  # Disable FK constraints to avoid migration issues
                cursor = conn.cursor()
                
                # 1. 验证用户存在
                cursor.execute("SELECT id, username FROM users WHERE id = ? AND is_active = 1", (user_id,))
                user_record = cursor.fetchone()
                if not user_record:
                    print(f"User {user_id} not found or inactive in database: {self.db_path}")
                    return False
                
                print(f"User verified: ID={user_record[0]}, Username={user_record[1]}")
                
                # 2. 检查笔记是否已存在（同一用户下）
                cursor.execute("SELECT id FROM notes WHERE user_id = ? AND note_id = ?", (user_id, note_data['note_id']))
                if cursor.fetchone():
                    print(f"用户 {user_id} 的笔记 {note_data['note_id']} 已存在，跳过保存")
                    return False
                
                # 3. 保存作者信息
                try:
                    author_data = note_data.get('author', {})
                    author_user_id = author_data.get('user_id', '')
                    nickname = author_data.get('nickname', '未知用户')
                    avatar = author_data.get('avatar', '')
                    
                    if not author_user_id:
                        author_user_id = f"unknown_{note_data['note_id']}"
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO authors (user_id, nickname, avatar, updated_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (author_user_id, nickname, avatar))
                    
                    # 获取作者ID
                    cursor.execute("SELECT id FROM authors WHERE user_id = ?", (author_user_id,))
                    author_id = cursor.fetchone()[0]
                    print(f"Author saved: {nickname} (ID: {author_id})")
                    
                except Exception as e:
                    print(f"Failed to save author: {str(e)}")
                    raise
                
                # 4. 保存笔记主信息
                try:
                    cursor.execute('''
                        INSERT INTO notes (user_id, note_id, title, content, type, publish_time, location, original_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        note_data.get('note_id', ''),
                        note_data.get('title', ''),
                        note_data.get('content', ''),
                        note_data.get('type', ''),
                        note_data.get('publish_time', ''),
                        note_data.get('location', ''),
                        note_data.get('original_url', '')
                    ))
                    print(f"Note saved: {note_data.get('title', 'No title')}")
                    
                except Exception as e:
                    print(f"Failed to save note: {str(e)}")
                    raise
                
                # 5. 保存笔记作者关系 (允许重复，支持多用户隔离)
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO note_authors (note_id, author_id)
                        VALUES (?, ?)
                    ''', (note_data['note_id'], author_id))
                    print(f"Note-author relationship saved")
                except Exception as e:
                    print(f"Failed to save note-author relationship: {str(e)}")
                    raise
                
                # 6. 保存互动数据
                try:
                    stats = note_data.get('stats', {})
                    
                    def safe_int(value):
                        """安全转换为整数"""
                        if value is None or value == '':
                            return 0
                        try:
                            return int(str(value).replace(',', '').replace(' ', ''))
                        except (ValueError, TypeError):
                            return 0
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO note_stats (note_id, likes, collects, comments, shares)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        note_data['note_id'], 
                        safe_int(stats.get('likes', 0)),
                        safe_int(stats.get('collects', 0)),
                        safe_int(stats.get('comments', 0)),
                        safe_int(stats.get('shares', 0))
                    ))
                    print(f"Note stats saved")
                except Exception as e:
                    print(f"Failed to save note stats: {str(e)}")
                    raise
                
                # 7. 保存标签
                try:
                    tags = note_data.get('tags', [])
                    tags_saved = 0
                    if tags and isinstance(tags, list):
                        for tag_name in tags:
                            if tag_name and tag_name.strip():  # 确保标签不为空
                                # 插入或获取标签
                                cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name.strip(),))
                                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name.strip(),))
                                tag_result = cursor.fetchone()
                                if tag_result:
                                    tag_id = tag_result[0]
                                    # 保存笔记标签关系
                                    cursor.execute('''
                                        INSERT OR IGNORE INTO note_tags (note_id, tag_id)
                                        VALUES (?, ?)
                                    ''', (note_data['note_id'], tag_id))
                                    tags_saved += 1
                    print(f"Tags saved: {tags_saved}")
                except Exception as e:
                    print(f"Failed to save tags (non-critical): {str(e)}")
                
                # 8. 保存图片
                try:
                    images = note_data.get('images', [])
                    images_saved = 0
                    if images and isinstance(images, list):
                        for i, image_url in enumerate(images):
                            if image_url and image_url.strip():  # 确保URL不为空
                                cursor.execute('''
                                    INSERT OR IGNORE INTO note_images (note_id, image_url, image_order)
                                    VALUES (?, ?, ?)
                                ''', (note_data['note_id'], image_url.strip(), i))
                                images_saved += 1
                    print(f"Images saved: {images_saved}")
                except Exception as e:
                    print(f"Failed to save images (non-critical): {str(e)}")
                
                # 9. 保存视频
                try:
                    videos = note_data.get('videos', [])
                    videos_saved = 0
                    if videos and isinstance(videos, list):
                        for i, video_url in enumerate(videos):
                            if video_url and video_url.strip():  # 确保URL不为空
                                cursor.execute('''
                                    INSERT OR IGNORE INTO note_videos (note_id, video_url, video_order)
                                    VALUES (?, ?, ?)
                                ''', (note_data['note_id'], video_url.strip(), i))
                                videos_saved += 1
                    print(f"Videos saved: {videos_saved}")
                except Exception as e:
                    print(f"Failed to save videos (non-critical): {str(e)}")
                
                # 10. 提交事务
                try:
                    conn.commit()
                    print(f"笔记 {note_data['note_id']} 保存成功 (用户: {user_id})")
                except Exception as e:
                    print(f"Failed to commit transaction: {str(e)}")
                    raise
                return True
                
        except Exception as e:
            print(f"保存笔记失败: {str(e)}")
            print(f"失败的笔记数据: {note_data}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_notes_list(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """获取用户的笔记列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = '''
                    SELECT 
                        n.note_id,
                        n.title,
                        n.content,
                        n.type,
                        n.publish_time,
                        n.location,
                        n.created_at,
                        a.nickname as author_nickname,
                        a.user_id as author_user_id,
                        a.avatar as author_avatar,
                        ns.likes,
                        ns.collects,
                        ns.comments,
                        ns.shares
                    FROM notes n
                    LEFT JOIN note_authors na ON n.note_id = na.note_id
                    LEFT JOIN authors a ON na.author_id = a.id
                    LEFT JOIN note_stats ns ON n.note_id = ns.note_id
                    WHERE n.user_id = ?
                    ORDER BY n.created_at DESC
                    LIMIT ? OFFSET ?
                '''
                
                cursor.execute(query, (user_id, limit, offset))
                notes = cursor.fetchall()
                
                result = []
                for note in notes:
                    note_dict = dict(note)
                    note_id = note_dict['note_id']
                    
                    # 获取标签
                    cursor.execute('''
                        SELECT t.name FROM tags t
                        JOIN note_tags nt ON t.id = nt.tag_id
                        WHERE nt.note_id = ?
                    ''', (note_id,))
                    tags = [row[0] for row in cursor.fetchall()]
                    
                    # 获取图片
                    cursor.execute('''
                        SELECT image_url FROM note_images
                        WHERE note_id = ?
                        ORDER BY image_order
                    ''', (note_id,))
                    images = [row[0] for row in cursor.fetchall()]
                    
                    # 获取视频
                    cursor.execute('''
                        SELECT video_url FROM note_videos
                        WHERE note_id = ?
                        ORDER BY video_order
                    ''', (note_id,))
                    videos = [row[0] for row in cursor.fetchall()]
                    
                    # 组装数据
                    formatted_note = {
                        'note_id': note_dict['note_id'],
                        'title': note_dict['title'],
                        'content': note_dict['content'],
                        'type': note_dict['type'],
                        'author': {
                            'nickname': note_dict['author_nickname'],
                            'user_id': note_dict['author_user_id'],
                            'avatar': note_dict['author_avatar']
                        },
                        'stats': {
                            'likes': note_dict['likes'] or 0,
                            'collects': note_dict['collects'] or 0,
                            'comments': note_dict['comments'] or 0,
                            'shares': note_dict['shares'] or 0
                        },
                        'publish_time': note_dict['publish_time'],
                        'location': note_dict['location'],
                        'tags': tags,
                        'images': images,
                        'videos': videos,
                        'created_at': note_dict['created_at']
                    }
                    result.append(formatted_note)
                
                return result
                
        except Exception as e:
            print(f"❌ 获取笔记列表失败: {str(e)}")
            return []
    
    def get_notes_count(self, user_id: int = None) -> int:
        """获取笔记总数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if user_id:
                    cursor.execute("SELECT COUNT(*) FROM notes WHERE user_id = ?", (user_id,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM notes")
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"❌ 获取笔记总数失败: {str(e)}")
            return 0
    
    def delete_note(self, user_id: int, note_id: str) -> bool:
        """删除用户的笔记"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 验证笔记属于该用户
                cursor.execute("SELECT id FROM notes WHERE user_id = ? AND note_id = ?", (user_id, note_id))
                if not cursor.fetchone():
                    print(f"❌ 笔记 {note_id} 不存在或不属于用户 {user_id}")
                    return False
                
                # 删除相关数据
                cursor.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
                cursor.execute("DELETE FROM note_images WHERE note_id = ?", (note_id,))
                cursor.execute("DELETE FROM note_videos WHERE note_id = ?", (note_id,))
                cursor.execute("DELETE FROM note_stats WHERE note_id = ?", (note_id,))
                cursor.execute("DELETE FROM note_authors WHERE note_id = ?", (note_id,))
                cursor.execute("DELETE FROM notes WHERE user_id = ? AND note_id = ?", (user_id, note_id))
                
                conn.commit()
                print(f"✅ 用户 {user_id} 的笔记 {note_id} 删除成功")
                return True
                
        except Exception as e:
            print(f"❌ 删除笔记失败: {str(e)}")
            return False
    
    def save_recreate_history(self, user_id: int, history_data: Dict) -> bool:
        """保存用户的二创历史记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO recreate_history 
                    (user_id, original_note_id, original_title, original_content, new_title, new_content)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    history_data['original_note_id'],
                    history_data['original_title'],
                    history_data['original_content'],
                    history_data['new_title'],
                    history_data['new_content']
                ))
                
                conn.commit()
                print(f"✅ 用户 {user_id} 的二创历史记录保存成功")
                return True
                
        except Exception as e:
            print(f"❌ 保存二创历史失败: {str(e)}")
            return False
    
    def get_recreate_history(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """获取用户的二创历史列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = '''
                    SELECT 
                        rh.id,
                        rh.original_note_id,
                        rh.original_title,
                        rh.original_content,
                        rh.new_title,
                        rh.new_content,
                        rh.created_at,
                        n.title as note_title,
                        a.nickname as author_nickname
                    FROM recreate_history rh
                    LEFT JOIN notes n ON rh.original_note_id = n.note_id AND n.user_id = rh.user_id
                    LEFT JOIN note_authors na ON n.note_id = na.note_id
                    LEFT JOIN authors a ON na.author_id = a.id
                    WHERE rh.user_id = ?
                    ORDER BY rh.created_at DESC
                    LIMIT ? OFFSET ?
                '''
                
                cursor.execute(query, (user_id, limit, offset))
                history_records = cursor.fetchall()
                
                result = []
                for record in history_records:
                    history_dict = {
                        'id': record['id'],
                        'original_note_id': record['original_note_id'],
                        'original_title': record['original_title'],
                        'original_content': record['original_content'],
                        'new_title': record['new_title'],
                        'new_content': record['new_content'],
                        'created_at': record['created_at'],
                        'note_title': record['note_title'],
                        'author_nickname': record['author_nickname']
                    }
                    result.append(history_dict)
                
                return result
                
        except Exception as e:
            print(f"❌ 获取二创历史失败: {str(e)}")
            return []
    
    def get_recreate_history_count(self, user_id: int) -> int:
        """获取用户的二创历史总数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM recreate_history WHERE user_id = ?", (user_id,))
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"❌ 获取二创历史总数失败: {str(e)}")
            return 0
    
    def delete_recreate_history(self, user_id: int, history_id: int) -> bool:
        """删除用户的二创历史记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM recreate_history WHERE user_id = ? AND id = ?", (user_id, history_id))
                if cursor.rowcount > 0:
                    conn.commit()
                    print(f"✅ 用户 {user_id} 的二创历史记录 {history_id} 删除成功")
                    return True
                else:
                    print(f"❌ 二创历史记录 {history_id} 不存在或不属于用户 {user_id}")
                    return False
                
        except Exception as e:
            print(f"❌ 删除二创历史失败: {str(e)}")
            return False
    
    def save_visual_story_history(self, user_id: int, history_data: Dict) -> bool:
        """保存用户的视觉故事历史记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO visual_story_history 
                    (user_id, history_id, title, content, cover_card_data, content_cards_data, 
                     html_content, model_used, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    history_data['history_id'],
                    history_data['title'],
                    history_data['content'],
                    history_data['cover_card_data'],
                    history_data['content_cards_data'],
                    history_data['html_content'],
                    history_data['model_used'],
                    history_data['created_at']
                ))
                
                conn.commit()
                print(f"✅ 用户 {user_id} 的视觉故事历史记录保存成功")
                return True
                
        except Exception as e:
            print(f"❌ 保存视觉故事历史失败: {str(e)}")
            return False
    
    def get_visual_story_history(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """获取用户的视觉故事历史列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = '''
                    SELECT 
                        vs.id,
                        vs.history_id,
                        vs.title,
                        vs.content,
                        vs.model_used,
                        vs.created_at,
                        rh.new_title as source_title
                    FROM visual_story_history vs
                    LEFT JOIN recreate_history rh ON vs.history_id = rh.id AND rh.user_id = vs.user_id
                    WHERE vs.user_id = ?
                    ORDER BY vs.created_at DESC
                    LIMIT ? OFFSET ?
                '''
                
                cursor.execute(query, (user_id, limit, offset))
                history_records = cursor.fetchall()
                
                result = []
                for record in history_records:
                    history_dict = {
                        'id': record['id'],
                        'history_id': record['history_id'],
                        'title': record['title'],
                        'content': record['content'][:200] + '...' if len(record['content']) > 200 else record['content'],
                        'model_used': record['model_used'],
                        'created_at': record['created_at'],
                        'source_title': record['source_title']
                    }
                    result.append(history_dict)
                
                return result
                
        except Exception as e:
            print(f"❌ 获取视觉故事历史失败: {str(e)}")
            return []
    
    def get_visual_story_history_count(self, user_id: int) -> int:
        """获取用户的视觉故事历史总数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM visual_story_history WHERE user_id = ?", (user_id,))
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"❌ 获取视觉故事历史总数失败: {str(e)}")
            return 0
    
    def delete_visual_story_history(self, user_id: int, story_id: int) -> bool:
        """删除用户的视觉故事历史记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM visual_story_history WHERE user_id = ? AND id = ?", (user_id, story_id))
                if cursor.rowcount > 0:
                    conn.commit()
                    print(f"✅ 用户 {user_id} 的视觉故事历史记录 {story_id} 删除成功")
                    return True
                else:
                    print(f"❌ 视觉故事历史记录 {story_id} 不存在或不属于用户 {user_id}")
                    return False
                
        except Exception as e:
            print(f"❌ 删除视觉故事历史失败: {str(e)}")
            return False
    
    def get_user_usage_count(self, user_id: int, usage_type: str) -> int:
        """获取用户使用次数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT usage_count FROM user_usage WHERE user_id = ? AND usage_type = ?", (user_id, usage_type))
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            print(f"❌ 获取用户使用次数失败: {str(e)}")
            return 0
    
    def verify_database_state(self) -> Dict:
        """验证数据库状态和统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取用户统计
                cursor.execute("SELECT COUNT(*) as total_users FROM users")
                total_users = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) as active_users FROM users WHERE is_active = 1")
                active_users = cursor.fetchone()[0]
                
                # 获取笔记统计
                cursor.execute("SELECT COUNT(*) as total_notes FROM notes")
                total_notes = cursor.fetchone()[0]
                
                # 获取最近创建的用户
                cursor.execute('''
                    SELECT id, username, created_at FROM users 
                    ORDER BY created_at DESC LIMIT 5
                ''')
                recent_users = cursor.fetchall()
                
                state = {
                    'database_path': self.db_path,
                    'total_users': total_users,
                    'active_users': active_users,
                    'total_notes': total_notes,
                    'recent_users': recent_users
                }
                
                print(f"📊 数据库状态:")
                print(f"   路径: {self.db_path}")
                print(f"   总用户数: {total_users}")
                print(f"   活跃用户数: {active_users}")
                print(f"   总笔记数: {total_notes}")
                print(f"   最近用户: {[f'{u[1]}(ID:{u[0]})' for u in recent_users]}")
                
                return state
                
        except Exception as e:
            print(f"❌ 数据库状态验证失败: {str(e)}")
            return {}
    
    def increment_user_usage(self, user_id: int, usage_type: str) -> bool:
        """增加用户使用次数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 使用INSERT OR REPLACE来处理计数器递增
                cursor.execute('''
                    INSERT OR REPLACE INTO user_usage (user_id, usage_type, usage_count, last_used)
                    VALUES (?, ?, COALESCE((SELECT usage_count FROM user_usage WHERE user_id = ? AND usage_type = ?), 0) + 1, CURRENT_TIMESTAMP)
                ''', (user_id, usage_type, user_id, usage_type))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 增加用户使用次数失败: {str(e)}")
            return False

# 全局数据库实例 - 使用项目目录中的数据库文件
db = XiaohongshuDatabase("xiaohongshu_notes.db")

if __name__ == "__main__":
    # 测试数据库初始化
    print("🔧 测试数据库初始化...")
    test_db = XiaohongshuDatabase("test.db")
    print("✅ 数据库测试完成")
