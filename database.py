import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class XiaohongshuDatabase:
    """小红书笔记数据库管理类"""
    
    def __init__(self, db_path: str = "xiaohongshu_notes.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库和表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建笔记主表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    type TEXT,
                    publish_time TEXT,
                    location TEXT,
                    original_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            
            # 创建二创历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recreate_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_note_id TEXT,
                    original_title TEXT,
                    original_content TEXT,
                    new_title TEXT,
                    new_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (original_note_id) REFERENCES notes (note_id)
                )
            ''')
            
            conn.commit()
            print("✅ 数据库表初始化完成")
    
    def save_note(self, note_data: Dict) -> bool:
        """保存笔记数据到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查笔记是否已存在
                cursor.execute("SELECT id FROM notes WHERE note_id = ?", (note_data['note_id'],))
                if cursor.fetchone():
                    print(f"笔记 {note_data['note_id']} 已存在，跳过保存")
                    return False
                
                # 保存作者信息
                author_data = note_data.get('author', {})
                user_id = author_data.get('user_id', '')
                nickname = author_data.get('nickname', '未知用户')
                avatar = author_data.get('avatar', '')
                
                if not user_id:
                    user_id = f"unknown_{note_data['note_id']}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO authors (user_id, nickname, avatar, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, nickname, avatar))
                
                # 获取作者ID
                cursor.execute("SELECT id FROM authors WHERE user_id = ?", (user_id,))
                author_id = cursor.fetchone()[0]
                
                # 保存笔记主信息
                cursor.execute('''
                    INSERT INTO notes (note_id, title, content, type, publish_time, location, original_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    note_data.get('note_id', ''),
                    note_data.get('title', ''),
                    note_data.get('content', ''),
                    note_data.get('type', ''),
                    note_data.get('publish_time', ''),
                    note_data.get('location', ''),
                    note_data.get('original_url', '')
                ))
                
                # 保存笔记作者关系
                cursor.execute('''
                    INSERT INTO note_authors (note_id, author_id)
                    VALUES (?, ?)
                ''', (note_data['note_id'], author_id))
                
                # 保存互动数据
                stats = note_data['stats']
                
                def safe_int(value):
                    """安全转换为整数"""
                    if value is None or value == '':
                        return 0
                    try:
                        return int(str(value).replace(',', '').replace(' ', ''))
                    except (ValueError, TypeError):
                        return 0
                
                cursor.execute('''
                    INSERT INTO note_stats (note_id, likes, collects, comments, shares)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    note_data['note_id'], 
                    safe_int(stats.get('likes', 0)),
                    safe_int(stats.get('collects', 0)),
                    safe_int(stats.get('comments', 0)),
                    safe_int(stats.get('shares', 0))
                ))
                
                # 保存标签
                tags = note_data.get('tags', [])
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
                
                # 保存图片
                images = note_data.get('images', [])
                if images and isinstance(images, list):
                    for i, image_url in enumerate(images):
                        if image_url and image_url.strip():  # 确保URL不为空
                            cursor.execute('''
                                INSERT INTO note_images (note_id, image_url, image_order)
                                VALUES (?, ?, ?)
                            ''', (note_data['note_id'], image_url.strip(), i))
                
                # 保存视频
                videos = note_data.get('videos', [])
                if videos and isinstance(videos, list):
                    for i, video_url in enumerate(videos):
                        if video_url and video_url.strip():  # 确保URL不为空
                            cursor.execute('''
                                INSERT INTO note_videos (note_id, video_url, video_order)
                                VALUES (?, ?, ?)
                            ''', (note_data['note_id'], video_url.strip(), i))
                
                conn.commit()
                print(f"✅ 笔记 {note_data['note_id']} 保存成功")
                return True
                
        except Exception as e:
            print(f"❌ 保存笔记失败: {str(e)}")
            print(f"📝 失败的笔记数据: {note_data}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_notes_list(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """获取笔记列表"""
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
                    ORDER BY n.created_at DESC
                    LIMIT ? OFFSET ?
                '''
                
                cursor.execute(query, (limit, offset))
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
    
    def get_notes_count(self) -> int:
        """获取笔记总数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM notes")
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"❌ 获取笔记总数失败: {str(e)}")
            return 0
    
    def delete_note(self, note_id: str) -> bool:
        """删除笔记"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 删除相关数据
                cursor.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
                cursor.execute("DELETE FROM note_images WHERE note_id = ?", (note_id,))
                cursor.execute("DELETE FROM note_videos WHERE note_id = ?", (note_id,))
                cursor.execute("DELETE FROM note_stats WHERE note_id = ?", (note_id,))
                cursor.execute("DELETE FROM note_authors WHERE note_id = ?", (note_id,))
                cursor.execute("DELETE FROM notes WHERE note_id = ?", (note_id,))
                
                conn.commit()
                print(f"✅ 笔记 {note_id} 删除成功")
                return True
                
        except Exception as e:
            print(f"❌ 删除笔记失败: {str(e)}")
            return False
    
    def save_recreate_history(self, history_data: Dict) -> bool:
        """保存二创历史记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO recreate_history 
                    (original_note_id, original_title, original_content, new_title, new_content)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    history_data['original_note_id'],
                    history_data['original_title'],
                    history_data['original_content'],
                    history_data['new_title'],
                    history_data['new_content']
                ))
                
                conn.commit()
                print(f"✅ 二创历史记录保存成功")
                return True
                
        except Exception as e:
            print(f"❌ 保存二创历史失败: {str(e)}")
            return False
    
    def get_recreate_history(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """获取二创历史列表"""
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
                    LEFT JOIN notes n ON rh.original_note_id = n.note_id
                    LEFT JOIN note_authors na ON n.note_id = na.note_id
                    LEFT JOIN authors a ON na.author_id = a.id
                    ORDER BY rh.created_at DESC
                    LIMIT ? OFFSET ?
                '''
                
                cursor.execute(query, (limit, offset))
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
    
    def get_recreate_history_count(self) -> int:
        """获取二创历史总数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM recreate_history")
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"❌ 获取二创历史总数失败: {str(e)}")
            return 0
    
    def delete_recreate_history(self, history_id: int) -> bool:
        """删除二创历史记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM recreate_history WHERE id = ?", (history_id,))
                conn.commit()
                print(f"✅ 二创历史记录 {history_id} 删除成功")
                return True
                
        except Exception as e:
            print(f"❌ 删除二创历史失败: {str(e)}")
            return False

# 全局数据库实例
db = XiaohongshuDatabase()

if __name__ == "__main__":
    # 测试数据库初始化
    print("🔧 测试数据库初始化...")
    test_db = XiaohongshuDatabase("test.db")
    print("✅ 数据库测试完成")
