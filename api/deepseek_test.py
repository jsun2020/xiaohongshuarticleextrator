"""
DeepSeek连接测试API - Vercel Serverless函数
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
        """测试DeepSeek API连接"""
        try:
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
                self.send_json_response({
                    'success': False, 
                    'error': '请先登录'
                }, 401)
                return
            
            # 初始化数据库
            db.init_database()
            
            # 获取用户配置
            user_config = db.get_user_config(user_id)
            
            print(f"[DeepSeek Test] Testing connection for user {user_id}")
            print(f"[DeepSeek Test] User config keys: {list(user_config.keys())}")
            
            # 调用DeepSeek API测试连接
            result = deepseek_api.test_connection(user_config)
            
            print(f"[DeepSeek Test] Test result: {result}")
            
            if result['success']:
                self.send_json_response({
                    'success': True,
                    'message': result['message']
                }, 200)
            else:
                self.send_json_response({
                    'success': False,
                    'error': result['error']
                }, 200)  # 使用200状态码，让前端处理业务错误
                
        except Exception as e:
            print(f"[DeepSeek Test] Error: {str(e)}")
            self.send_json_response({
                'success': False,
                'error': f'连接测试失败: {str(e)}'
            }, 500)
    
    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))