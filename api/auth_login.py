from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from auth_utils import verify_password, create_session_token

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 获取请求体
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = json.dumps({
                    'success': False,
                    'error': '用户名和密码不能为空'
                })
                self.wfile.write(response.encode('utf-8'))
                return
            
            # 获取用户信息
            user = db.get_user_by_username(username)
            if not user:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = json.dumps({
                    'success': False,
                    'error': '用户名或密码错误'
                })
                self.wfile.write(response.encode('utf-8'))
                return
            
            # 验证密码
            if not verify_password(password, user['password_hash']):
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = json.dumps({
                    'success': False,
                    'error': '用户名或密码错误'
                })
                self.wfile.write(response.encode('utf-8'))
                return
            
            # 创建会话令牌
            token = create_session_token(user['id'])
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', f'session_token={token}; HttpOnly; Path=/; Max-Age=86400')
            self.end_headers()
            
            response = json.dumps({
                'success': True,
                'message': '登录成功',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'nickname': user['nickname'],
                    'email': user['email']
                },
                'token': token
            }, ensure_ascii=False)
            
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = json.dumps({
                'success': False,
                'error': f'登录失败: {str(e)}'
            }, ensure_ascii=False)
            self.wfile.write(response.encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()