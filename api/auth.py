"""
统一认证API - Vercel Serverless函数
处理登录、注册、登出请求
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
import re
from urllib.parse import urlparse, parse_qs

# 认证工具函数
def validate_username(username):
    """验证用户名格式"""
    if not username or len(username) < 3 or len(username) > 20:
        return False, "用户名长度必须在3-20个字符之间"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    
    return True, ""

def validate_password(password):
    """验证密码强度"""
    if not password or len(password) < 6:
        return False, "密码至少需要6个字符"
    
    if len(password) > 50:
        return False, "密码不能超过50个字符"
    
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_letter and has_digit):
        return False, "密码必须包含至少一个字母和一个数字"
    
    return True, ""

def validate_email(email):
    """验证邮箱格式"""
    if not email:
        return True, ""  # 邮箱是可选的
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "邮箱格式不正确"
    
    return True, ""

def hash_password(password):
    """密码哈希"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

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
        """根据路径参数处理不同的认证请求"""
        try:
            # 获取查询参数来确定操作类型
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # 从查询参数获取action，如果没有则从路径获取
            action = query_params.get('action', [None])[0]
            if not action:
                # 从路径中提取action，例如 /api/auth?action=login
                path_parts = parsed_url.path.strip('/').split('/')
                if 'login' in self.path:
                    action = 'login'
                elif 'register' in self.path:
                    action = 'register'
                elif 'logout' in self.path:
                    action = 'logout'
                elif 'status' in self.path:
                    action = 'status'
            
            # 初始化数据库
            db.init_database()
            
            if action == 'login':
                self.handle_login()
            elif action == 'register':
                self.handle_register()
            elif action == 'logout':
                self.handle_logout()
            elif action == 'status':
                self.handle_status()
            else:
                self.send_json_response({'success': False, 'error': 'Invalid action'}, 400)
                
        except Exception as e:
            self.send_json_response({'success': False, 'error': f'请求处理失败: {str(e)}'}, 500)
    
    def do_GET(self):
        """处理GET请求（主要用于status检查）"""
        try:
            if 'status' in self.path:
                db.init_database()
                self.handle_status()
            else:
                self.send_json_response({'success': False, 'error': 'Method not allowed'}, 405)
        except Exception as e:
            self.send_json_response({'success': False, 'error': f'请求处理失败: {str(e)}'}, 500)
    
    def handle_login(self):
        """处理登录请求"""
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
    
    def handle_register(self):
        """处理注册请求"""
        # 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        nickname = data.get('nickname', '').strip()
        
        # 验证输入
        valid, msg = validate_username(username)
        if not valid:
            self.send_json_response({'success': False, 'error': msg}, 400)
            return
        
        valid, msg = validate_password(password)
        if not valid:
            self.send_json_response({'success': False, 'error': msg}, 400)
            return
        
        valid, msg = validate_email(email)
        if not valid:
            self.send_json_response({'success': False, 'error': msg}, 400)
            return
        
        # 检查用户名是否已存在
        existing_user = db.get_user_by_username(username)
        if existing_user:
            self.send_json_response({'success': False, 'error': '用户名已存在'}, 400)
            return
        
        # 创建用户
        password_hash = hash_password(password)
        user_id = db.create_user(username, password_hash, email, nickname)
        
        if user_id:
            # 设置默认配置
            db.set_user_config(user_id, 'deepseek_base_url', 'https://api.deepseek.com')
            db.set_user_config(user_id, 'deepseek_model', 'deepseek-chat')
            db.set_user_config(user_id, 'deepseek_temperature', '0.7')
            db.set_user_config(user_id, 'deepseek_max_tokens', '1000')
            
            self.send_json_response({
                'success': True,
                'message': '用户注册成功',
                'user': {
                    'id': user_id,
                    'username': username,
                    'nickname': nickname or username
                }
            }, 201)
        else:
            self.send_json_response({'success': False, 'error': '用户创建失败'}, 500)
    
    def handle_logout(self):
        """处理登出请求"""
        # 清除所有认证相关的cookies
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        
        # Clear all auth cookies by setting them to expire immediately
        cookies_to_clear = ['session_id', 'session_token', 'user_id', 'logged_in']
        for cookie_name in cookies_to_clear:
            self.send_header('Set-Cookie', f'{cookie_name}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT')
        
        self.end_headers()
        
        response_data = {
            'success': True,
            'message': '登出成功'
        }
        
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
    
    def handle_status(self):
        """处理状态检查请求"""
        try:
            # 从cookies中获取session信息
            cookies = {}
            if 'Cookie' in self.headers:
                cookie_header = self.headers['Cookie']
                for cookie in cookie_header.split(';'):
                    if '=' in cookie:
                        key, value = cookie.strip().split('=', 1)
                        cookies[key] = value
            
            session_id = cookies.get('session_id')
            user_id = cookies.get('user_id')
            logged_in = cookies.get('logged_in')
            
            if session_id and user_id and logged_in == 'true':
                # 验证用户是否存在
                user = db.get_user_by_id(int(user_id))
                if user:
                    self.send_json_response({
                        'success': True,
                        'logged_in': True,
                        'user': {
                            'id': user['id'],
                            'username': user['username'],
                            'nickname': user['nickname'] or user['username'],
                            'email': user['email']
                        }
                    }, 200)
                    return
            
            self.send_json_response({
                'success': True,
                'logged_in': False
            }, 200)
            
        except Exception as e:
            self.send_json_response({
                'success': True,
                'logged_in': False
            }, 200)
    
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