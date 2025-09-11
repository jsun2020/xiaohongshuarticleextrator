"""
获取小红书笔记API - Vercel Serverless函数 (Class-based Handler)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler
from _utils import require_auth
from _database import db
from _xhs_crawler import get_xiaohongshu_note
import json
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    
    def send_json_response(self, data, status_code=200):
        """统一发送JSON响应的辅助函数"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(204) # No Content
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()

    def do_POST(self):
        """处理获取小红书笔记的POST请求"""
        # 初始化数据库
        db.init_database()
        
        try:
            # 1. 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}
            
            # 2. 解析Cookie进行认证
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
            
            # 3. 检查用户认证
            user_id = require_auth(req_data)
            if not user_id:
                self.send_json_response({'success': False, 'error': '请先登录'}, 401)
                return
            
            url = data.get('url', '').strip()
            if not url:
                self.send_json_response({'success': False, 'error': '请提供小红书链接'}, 400)
                return
            
            # 4. 调用爬虫获取笔记信息
            result = get_xiaohongshu_note(url)
            
            if result.get('success'):
                note_data = result['data']
                
                # 5. 保存到数据库
                print(f"[API] Attempting to save note: {note_data.get('note_id')} for user_id: {user_id}")
                save_success = db.save_note(note_data, user_id)
                print(f"[API] Save result: {save_success}")
                
                if save_success:
                    self.send_json_response({
                        'success': True,
                        'message': '笔记获取并保存成功',
                        'data': note_data,
                        'saved_to_db': True
                    })
                else:
                    # 即使保存失败（例如，因为已存在），采集本身是成功的
                    self.send_json_response({
                        'success': True,
                        'message': '笔记获取成功，但保存失败（可能已存在）',
                        'data': note_data,
                        'saved_to_db': False
                    })
            else:
                self.send_json_response({
                    'success': False,
                    'error': result.get('error', '获取笔记失败')
                }, 400)
                
        except Exception as e:
            print(f"Error in note.py handler: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': f'处理请求失败: {str(e)}'
            }, 500)