"""
小红书笔记二创API - Vercel Serverless函数
"""
from http.server import BaseHTTPRequestHandler
import sys
import os
import json
import urllib.parse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response, require_auth
from _database import db
from _deepseek_api import deepseek_api

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_POST(self):
        """处理笔记二创请求"""
        try:
            # 初始化数据库
            db.init_database()
            print(f"[CRITICAL DEBUG] AI recreate - database path: {db.db_path}")
            print(f"[CRITICAL DEBUG] AI recreate - database exists: {os.path.exists(db.db_path)}")
            print(f"[CRITICAL DEBUG] AI recreate - current working dir: {os.getcwd()}")
            print(f"[CRITICAL DEBUG] AI recreate - temp dir: {os.environ.get('TMPDIR', 'not set')}")
            
            # 获取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                try:
                    data = json.loads(body.decode('utf-8'))
                except json.JSONDecodeError:
                    data = {}
            else:
                data = {}
            
            # 解析Cookie进行认证
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = urllib.parse.unquote(value)
            
            req_data = {
                'method': 'POST',
                'body': data,
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            # 检查用户认证
            user_id = require_auth(req_data)
            if not user_id:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False, 
                    'error': '请先登录'
                }).encode('utf-8'))
                return
            
            note_id = data.get('note_id')
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            
            if not title or not content:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': '标题和内容不能为空'
                }).encode('utf-8'))
                return
            
            # 获取用户配置
            user_config = db.get_user_config(user_id)
            
            # 调用DeepSeek API进行二创
            recreate_result = deepseek_api.recreate_note(title, content, user_config, user_id)
            
            if recreate_result['success']:
                recreated_data = recreate_result['data']
                
                # 保存二创历史
                if note_id:
                    print(f"[DB DEBUG] Saving recreate history for user {user_id}, note {note_id}")
                    try:
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        
                        if db.use_postgres:
                            cursor.execute('''
                                INSERT INTO recreate_history (user_id, note_id, original_title, 
                                                            original_content, recreated_title, recreated_content)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            ''', (user_id, note_id, title, content, 
                                  recreated_data['new_title'], recreated_data['new_content']))
                        else:
                            cursor.execute('''
                                INSERT INTO recreate_history (user_id, note_id, original_title, 
                                                            original_content, recreated_title, recreated_content)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (user_id, note_id, title, content, 
                                  recreated_data['new_title'], recreated_data['new_content']))
                        
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        print(f"保存二创历史失败: {e}")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
                self.end_headers()
                
                response_data = {
                    'success': True,
                    'message': '笔记二创成功',
                    'data': {
                        'original_title': title,
                        'original_content': content,
                        'new_title': recreated_data['new_title'],
                        'new_content': recreated_data['new_content']
                    }
                }
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': recreate_result.get('error', '二创失败')
                }).encode('utf-8'))
                
        except Exception as e:
            print(f"Error in recreate API: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'处理二创请求失败: {str(e)}'
            }).encode('utf-8'))