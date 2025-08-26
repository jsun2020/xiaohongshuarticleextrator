"""
获取笔记列表API - Vercel Serverless函数
Handles: GET /api/xiaohongshu/notes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response, require_auth
from _database import db
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理获取笔记列表请求"""
        # 初始化数据库
        db.init_database()
        
        try:
            # 解析查询参数
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
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
                'query': query_params,
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            # 检查用户认证
            user_id = require_auth(req_data)
            if not user_id:
                self.send_error_response({'success': False, 'error': '请先登录'}, 401)
                return
            
            # 获取分页参数
            try:
                limit = int(query_params.get('limit', ['20'])[0])
                offset = int(query_params.get('offset', ['0'])[0])
                page = (offset // limit) + 1
                per_page = limit
            except (ValueError, IndexError):
                limit = 20
                offset = 0
                page = 1
                per_page = 20
            
            # 获取用户的笔记列表
            notes = db.get_notes(user_id, page, per_page)
            
            # 格式化笔记数据
            formatted_notes = []
            for note in notes:
                try:
                    formatted_note = {
                        'id': note.get('id'),
                        'note_id': note.get('note_id'),
                        'title': note.get('title', ''),
                        'content': note.get('content', ''),
                        'type': note.get('note_type', ''),
                        'publish_time': note.get('publish_time', ''),
                        'location': note.get('location', ''),
                        'original_url': note.get('original_url', ''),
                        'author': note.get('author_data', {}),
                        'stats': note.get('stats_data', {}),
                        'images': note.get('images_data', []),
                        'created_at': str(note.get('created_at', ''))
                    }
                    formatted_notes.append(formatted_note)
                except Exception as format_error:
                    print(f"Error formatting note: {format_error}")
                    continue
            
            self.send_json_response({
                'success': True,
                'data': formatted_notes,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'page': page,
                    'per_page': per_page,
                    'total': len(formatted_notes)
                }
            }, 200)
            
        except Exception as e:
            print(f"Error in notes API: {e}")
            self.send_error_response({
                'success': False,
                'error': f'获取笔记列表失败: {str(e)}'
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