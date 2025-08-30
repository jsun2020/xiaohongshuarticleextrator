"""
用户登出API - Vercel Serverless函数
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
    
    def do_POST(self):
        """处理登出请求"""
        try:
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
            
        except Exception as e:
            self.send_json_response({'success': False, 'error': f'登出失败: {str(e)}'}, 500)

    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))