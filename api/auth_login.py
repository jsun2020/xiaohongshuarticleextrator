"""
用户登录API - Vercel Serverless函数
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response
from _database import db
from http.server import BaseHTTPRequestHandler
import json
import hashlib
import secrets

def verify_password(password, stored_hash):
    """验证密码"""
    try:
        salt, hash_value = stored_hash.split(':')
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash == hash_value
    except:
        return False

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_POST(self):
        """处理登录请求"""
        try:
            # 初始化数据库
            db.init_database()
            
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                self.send_json_response({'success': False, 'error': '用户名和密码不能为空'}, 400)
                return
            
            # 查找用户
            user = db.get_user_by_username(username)
            if not user:
                self.send_json_response({'success': False, 'error': '用户名或密码错误'}, 401)
                return
            
            # 验证密码
            if not verify_password(password, user['password_hash']):
                self.send_json_response({'success': False, 'error': '用户名或密码错误'}, 401)
                return
            
            # 生成会话ID和JWT token
            session_id = secrets.token_hex(32)
            
            # 导入JWT相关函数
            try:
                from _utils import create_session_token
                token = create_session_token(user['id'])
            except ImportError:
                # 如果导入失败，使用session_id作为token
                token = session_id
            
            # 发送成功响应
            self.send_success_response({
                'success': True,
                'message': '登录成功',
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'nickname': user['nickname'] or user['username'],
                    'email': user['email']
                }
            }, session_id, user['id'], token)
            
        except Exception as e:
            self.send_json_response({'success': False, 'error': f'登录失败: {str(e)}'}, 500)
    
    def send_success_response(self, data, session_id, user_id, token):
        """发送成功响应"""
        # 设置Cookie - 在生产环境中使用Secure标志
        secure_flag = '; Secure'
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        
        # Set multiple cookies by calling send_header multiple times with different values
        cookies = [
            f'session_id={session_id}; Path=/; HttpOnly{secure_flag}; SameSite=Lax; Max-Age={86400 * 7}',
            f'session_token={token}; Path=/; HttpOnly{secure_flag}; SameSite=Lax; Max-Age={86400 * 7}',
            f'user_id={user_id}; Path=/; HttpOnly{secure_flag}; SameSite=Lax; Max-Age={86400 * 7}',
            f'logged_in=true; Path=/{secure_flag}; SameSite=Lax; Max-Age={86400 * 7}'
        ]
        
        # Add each cookie as a separate header
        for cookie in cookies:
            self.send_header('Set-Cookie', cookie)
            
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))