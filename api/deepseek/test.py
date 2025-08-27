"""
测试DeepSeek连接API - Vercel Serverless函数
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _utils import parse_request, create_response, require_auth
from _database import db
from _deepseek_api import deepseek_api
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """处理DeepSeek连接测试请求"""
        # 初始化数据库
        db.init_database()
        
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            # 解析Cookie进行认证
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
            
            req_data = {
                'method': 'POST',
                'body': data,
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            # 检查用户认证
            user_id = require_auth(req_data)
            if not user_id:
                self.send_error_response({'success': False, 'error': '请先登录'}, 401)
                return
            
            # 获取用户配置
            user_config = db.get_user_config(user_id)
            print(f"[DEBUG] User {user_id} config: {list(user_config.keys()) if user_config else 'None'}")
            
            # 检查API Key
            api_key = user_config.get('deepseek_api_key', '')
            print(f"[DEBUG] API Key present: {'Yes' if api_key else 'No'}")
            if api_key:
                print(f"[DEBUG] API Key starts with: {api_key[:10]}...")
            
            # 测试连接
            result = deepseek_api.test_connection(user_config)
            
            if result['success']:
                self.send_json_response(result, 200)
            else:
                self.send_json_response(result, 400)
                
        except Exception as e:
            print(f"Error in deepseek test: {e}")
            self.send_error_response({
                'success': False,
                'error': f'测试连接失败: {str(e)}'
            }, 500)
    
    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, data, status_code):
        """发送错误响应"""
        self.send_json_response(data, status_code)
    
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()