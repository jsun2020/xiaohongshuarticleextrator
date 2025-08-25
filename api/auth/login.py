"""
用户登录API - Vercel Serverless函数
"""
import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from _utils import parse_request, create_response
    from _database import db
except ImportError as e:
    print(f"Import error: {e}")
    # 尝试相对导入
    import importlib.util
    
    utils_path = os.path.join(parent_dir, '_utils.py')
    db_path = os.path.join(parent_dir, '_database.py')
    
    spec = importlib.util.spec_from_file_location("_utils", utils_path)
    _utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_utils)
    
    spec = importlib.util.spec_from_file_location("_database", db_path)
    _database = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_database)
    
    parse_request = _utils.parse_request
    create_response = _utils.create_response
    db = _database.db
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

from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """处理POST请求"""
        # 初始化数据库
        db.init_database()
        
        try:
            # 读取请求体
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                self.send_error_response({'success': False, 'error': '用户名和密码不能为空'}, 400)
                return
            
            # 查找用户
            user = db.get_user_by_username(username)
            if not user:
                self.send_error_response({'success': False, 'error': '用户名或密码错误'}, 401)
                return
            
            # 验证密码
            if not verify_password(password, user['password_hash']):
                self.send_error_response({'success': False, 'error': '用户名或密码错误'}, 401)
                return
            
            # 生成会话ID
            session_id = secrets.token_hex(32)
            
            # 发送成功响应
            self.send_success_response({
                'success': True,
                'message': '登录成功',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'nickname': user['nickname'] or user['username'],
                    'email': user['email']
                }
            }, session_id, user['id'])
            
        except Exception as e:
            self.send_error_response({'success': False, 'error': f'登录失败: {str(e)}'}, 500)
    
    def send_success_response(self, data, session_id, user_id):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
        # 设置Cookie
        self.send_header('Set-Cookie', f'session_id={session_id}; HttpOnly; Secure; SameSite=Lax; Max-Age={86400 * 7}')
        self.send_header('Set-Cookie', f'user_id={user_id}; HttpOnly; Secure; SameSite=Lax; Max-Age={86400 * 7}')
        self.send_header('Set-Cookie', f'logged_in=true; Secure; SameSite=Lax; Max-Age={86400 * 7}')
        
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, data, status_code):
        """发送错误响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()