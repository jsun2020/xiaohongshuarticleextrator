"""
检查登录状态API - Vercel Serverless函数
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response, require_auth
from _database import db
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_GET(self):
        """检查登录状态"""
        try:
            # 解析Cookie
            cookies = {}
            cookie_header = self.headers.get('Cookie', '') or self.headers.get('cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
            
            # 检查认证
            req_data = {
                'method': 'GET',
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            user_id = require_auth(req_data)
            
            if not user_id:
                self.send_json_response({
                    'logged_in': False,
                    'user': None
                }, 200)
                return
            
            # 初始化数据库并获取完整用户信息
            db.init_database()
            user_data = db.get_user_by_id(user_id)
            
            if not user_data:
                # User ID is valid but user no longer exists in DB
                self.send_json_response({
                    'logged_in': False,
                    'user': None
                }, 200)
                return
            
            # 返回完整用户信息
            self.send_json_response({
                'logged_in': True,
                'user': {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'nickname': user_data['nickname'] or user_data['username'],
                    'email': user_data['email'] or ''
                }
            }, 200)
            
        except Exception as e:
            self.send_json_response({
                'logged_in': False,
                'user': None,
                'error': str(e)
            }, 200)
    
    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))