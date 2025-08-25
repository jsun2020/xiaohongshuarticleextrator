"""
检查登录状态API - Vercel Serverless函数
"""
import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from _utils import parse_request, create_response, require_auth
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
    require_auth = _utils.require_auth
    db = _database.db

from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """检查用户登录状态"""
        try:
            # 解析Cookie
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
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
            
            # 获取用户信息 (简化版本)
            self.send_json_response({
                'logged_in': True,
                'user': {
                    'id': user_id,
                    'username': cookies.get('username', ''),
                    'nickname': cookies.get('nickname', '')
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