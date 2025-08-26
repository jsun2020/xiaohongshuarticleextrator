"""
获取小红书笔记API - Vercel Serverless函数
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _utils import parse_request, create_response, require_auth
from _database import db
from _xhs_crawler import get_xiaohongshu_note
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """处理获取小红书笔记请求"""
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
            
            # 解析Cookie和Authorization header进行认证
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
            print(f"[DEBUG] Authentication result: user_id={user_id}")
            print(f"[DEBUG] Headers: {dict(self.headers)}")
            print(f"[DEBUG] Cookies: {cookies}")
            
            if not user_id:
                self.send_error_response({
                    'success': False, 
                    'error': '请先登录',
                    'debug': {
                        'headers': dict(self.headers),
                        'cookies': cookies,
                        'auth_result': user_id
                    }
                }, 401)
                return
            
            url = data.get('url', '').strip()
            if not url:
                self.send_error_response({'success': False, 'error': '请提供小红书链接'}, 400)
                return
            
            # 调用爬虫获取笔记信息
            result = get_xiaohongshu_note(url)
            
            if result.get('success'):
                note_data = result['data']
                
                # 保存到数据库
                save_success = db.save_note(note_data, user_id)
                
                if save_success:
                    self.send_json_response({
                        'success': True,
                        'message': '笔记获取并保存成功',
                        'data': note_data,
                        'saved_to_db': True
                    }, 200)
                else:
                    self.send_json_response({
                        'success': True,
                        'message': '笔记获取成功，但保存失败',
                        'data': note_data,
                        'saved_to_db': False
                    }, 200)
            else:
                self.send_error_response({
                    'success': False,
                    'error': result.get('error', '获取笔记失败')
                }, 400)
                
        except Exception as e:
            self.send_error_response({
                'success': False,
                'error': f'处理请求失败: {str(e)}'
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