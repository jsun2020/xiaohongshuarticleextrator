"""
二创历史列表API - Vercel Serverless函数
Handles: GET /api/xiaohongshu_recreate_history
"""
from http.server import BaseHTTPRequestHandler
import sys
import os
import json
import urllib.parse
from urllib.parse import urlparse, parse_qs

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response, require_auth
from _database import db

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_GET(self):
        """处理二创历史请求"""
        try:
            # 初始化数据库
            db.init_database()
            
            # 调试信息 - 区分数据库类型
            if hasattr(db, 'db_path'):
                print(f"[CRITICAL DEBUG] Recreate history - SQLite database path: {db.db_path}")
                print(f"[CRITICAL DEBUG] Recreate history - database exists: {os.path.exists(db.db_path)}")
            else:
                print(f"[CRITICAL DEBUG] Recreate history - Using PostgreSQL database")
                print(f"[CRITICAL DEBUG] Recreate history - Database URL configured: {bool(db.db_url)}")
                
            print(f"[CRITICAL DEBUG] Recreate history - current working dir: {os.getcwd()}")
            print(f"[CRITICAL DEBUG] Recreate history - temp dir: {os.environ.get('TMPDIR', 'not set')}")
            
            # 解析查询参数
            query_params = {}
            if self.path and '?' in self.path:
                query_string = self.path.split('?', 1)[1]
                query_params = parse_qs(query_string)
            
            # 解析Cookie进行认证
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = urllib.parse.unquote(value)
            
            req_data = {
                'method': 'GET',
                'query': query_params,
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            # 检查用户认证
            print(f"[AUTH DEBUG] Cookies in request: {list(cookies.keys())}")
            print(f"[AUTH DEBUG] Headers: {list(self.headers.keys())}")
            
            user_id = require_auth(req_data)
            print(f"[AUTH DEBUG] User ID from auth: {user_id}")
            
            if not user_id:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False, 
                    'error': '请先登录'
                }).encode('utf-8'))
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
                # Get recreate history with COALESCE to handle NULL values
                if db.use_postgres:
                    cursor.execute('''
                        SELECT id, user_id, 
                               COALESCE(note_id, '') as note_id,
                               COALESCE(original_title, '') as original_title, 
                               COALESCE(original_content, '') as original_content, 
                               COALESCE(recreated_title, '') as recreated_title, 
                               COALESCE(recreated_content, '') as recreated_content, 
                               created_at
                        FROM recreate_history
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    ''', (user_id, per_page, offset))
                else:
                    cursor.execute('''
                        SELECT id, user_id, 
                               COALESCE(note_id, '') as note_id,
                               COALESCE(original_title, '') as original_title, 
                               COALESCE(original_content, '') as original_content, 
                               COALESCE(recreated_title, '') as recreated_title, 
                               COALESCE(recreated_content, '') as recreated_content, 
                               created_at
                        FROM recreate_history
                        WHERE user_id = ?
                        ORDER BY created_at DESC
                        LIMIT ? OFFSET ?
                    ''', (user_id, per_page, offset))
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                # Get total count
                if db.use_postgres:
                    cursor.execute('SELECT COUNT(*) FROM recreate_history WHERE user_id = %s', (user_id,))
                else:
                    cursor.execute('SELECT COUNT(*) FROM recreate_history WHERE user_id = ?', (user_id,))
                
                total_count = cursor.fetchone()[0]
                
                history_list = []
                for row in rows:
                    try:
                        history = dict(zip(columns, row))
                        # Ensure no NULL values with double protection
                        history_list.append({
                            'id': history.get('id') or 0,
                            'note_id': str(history.get('note_id') or ''),
                            'note_title': history.get('original_title') or '',  # Use original_title as note title
                            'original_url': '',  # Not available without note join
                            'original_title': history.get('original_title') or '',
                            'original_content': history.get('original_content') or '',
                            'new_title': history.get('recreated_title') or '',
                            'new_content': history.get('recreated_content') or '',
                            'created_at': str(history.get('created_at') or '')
                        })
                    except Exception as format_error:
                        print(f"Error formatting history: {format_error}")
                        continue
                
                response_data = {
                    'success': True,
                    'data': history_list,
                    'pagination': {
                        'limit': limit,
                        'offset': offset,
                        'page': page,
                        'per_page': per_page,
                        'total': total_count
                    }
                }
                
                print(f"[API DEBUG] Returning {len(history_list)} history records")
                if history_list:
                    print(f"[API DEBUG] First record keys: {list(history_list[0].keys())}")
                    print(f"[API DEBUG] First record data: {history_list[0]}")
                    print(f"[API DEBUG] Response structure: {{'success': {response_data['success']}, 'data_length': {len(response_data['data'])}, 'pagination': {response_data['pagination']}}}")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
                self.end_headers()
                
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Error in recreate history API: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'获取二创历史失败: {str(e)}'
            }).encode('utf-8'))