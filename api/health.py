"""
健康检查API - Vercel Serverless函数
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response, require_auth
from _database import db
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        # 初始化数据库
        db.init_database()
        
        try:
            # 解析Cookie进行认证
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
            
            req_data = {
                'method': 'GET',
                'query': {},
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            # 检查用户登录状态
            user_id = require_auth(req_data)
            logged_in = user_id is not None
            
            # 获取笔记总数
            total_notes = 0
            if user_id:
                try:
                    total_notes = db.get_notes_count(user_id)
                except:
                    total_notes = 0
            
            # 检查用户的DeepSeek配置
            deepseek_configured = False
            if user_id:
                try:
                    user_config = db.get_user_config(user_id)
                    deepseek_configured = bool(user_config.get('deepseek_api_key', '').strip())
                except:
                    deepseek_configured = False
            
            self.send_json_response({
                'success': True,
                'status': 'healthy',
                'database_status': 'connected',
                'total_notes': total_notes,
                'deepseek_configured': deepseek_configured,
                'logged_in': logged_in
            }, 200)
            
        except Exception as e:
            print(f"Health check error: {e}")
            self.send_json_response({
                'success': False,
                'status': 'error',
                'error': str(e)
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
    
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()