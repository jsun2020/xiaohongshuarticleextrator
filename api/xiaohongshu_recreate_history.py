"""
二创历史列表API - Vercel Serverless函数
Handles: GET /api/xiaohongshu/recreate/history
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
        """处理二创历史请求"""
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
            
            # 获取二创历史
            conn = db.get_connection()
            cursor = conn.cursor()
            
            try:
                # Get recreate history without requiring note join (to handle invalid note_ids)
                if db.use_postgres:
                    cursor.execute('''
                        SELECT id, user_id, note_id, original_title, original_content, 
                               recreated_title, recreated_content, created_at
                        FROM recreate_history
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    ''', (user_id, per_page, offset))
                else:
                    cursor.execute('''
                        SELECT id, user_id, note_id, original_title, original_content, 
                               recreated_title, recreated_content, created_at
                        FROM recreate_history
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    ''', (user_id, per_page, offset))
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                history_list = []
                for row in rows:
                    try:
                        history = dict(zip(columns, row))
                        history_list.append({
                            'id': history.get('id'),
                            'note_id': history.get('note_id'),
                            'note_title': history.get('original_title', ''),  # Use original_title as note title
                            'original_url': '',  # Not available without note join
                            'original_title': history.get('original_title', ''),
                            'original_content': history.get('original_content', ''),
                            'recreated_title': history.get('recreated_title', ''),
                            'recreated_content': history.get('recreated_content', ''),
                            'created_at': str(history.get('created_at', ''))
                        })
                    except Exception as format_error:
                        print(f"Error formatting history: {format_error}")
                        continue
                
                self.send_json_response({
                    'success': True,
                    'data': history_list,
                    'pagination': {
                        'limit': limit,
                        'offset': offset,
                        'page': page,
                        'per_page': per_page,
                        'total': len(history_list)
                    }
                }, 200)
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Error in recreate history API: {e}")
            self.send_error_response({
                'success': False,
                'error': f'获取二创历史失败: {str(e)}'
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