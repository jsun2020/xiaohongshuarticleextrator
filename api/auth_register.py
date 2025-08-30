"""
用户注册API - Vercel Serverless函数
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

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_POST(self):
        """处理注册请求"""
        try:
            # 初始化数据库
            db.init_database()
            
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
                
        except Exception as e:
            self.send_json_response({'success': False, 'error': f'注册失败: {str(e)}'}, 500)

    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))