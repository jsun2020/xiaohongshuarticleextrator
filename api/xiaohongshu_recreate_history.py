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
            print(f"[API DEBUG] Starting recreate history request")
            
            # 初始化数据库
            try:
                db.init_database()
                print(f"[API DEBUG] Database initialized successfully")
            except Exception as db_init_error:
                print(f"[API ERROR] Database initialization failed: {db_init_error}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': f'数据库初始化失败: {str(db_init_error)}'
                }).encode('utf-8'))
                return
            
            # 调试信息 - 区分数据库类型
            if hasattr(db, 'db_path'):
                print(f"[CRITICAL DEBUG] Recreate history - SQLite database path: {db.db_path}")
                print(f"[CRITICAL DEBUG] Recreate history - database exists: {os.path.exists(db.db_path)}")
            else:
                print(f"[CRITICAL DEBUG] Recreate history - Using PostgreSQL database")
                print(f"[CRITICAL DEBUG] Recreate history - Database URL configured: {bool(getattr(db, 'db_url', False))}")
                
            print(f"[CRITICAL DEBUG] Recreate history - current working dir: {os.getcwd()}")
            print(f"[CRITICAL DEBUG] Recreate history - temp dir: {os.environ.get('TMPDIR', 'not set')}")
            
            # 解析查询参数
            query_params = {}
            if self.path and '?' in self.path:
                query_string = self.path.split('?', 1)[1]
                query_params = parse_qs(query_string)
            
            print(f"[API DEBUG] Query params: {query_params}")
            
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
            
            try:
                user_id = require_auth(req_data)
                print(f"[AUTH DEBUG] User ID from auth: {user_id}")
            except Exception as auth_error:
                print(f"[AUTH ERROR] Authentication failed: {auth_error}")
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False, 
                    'error': '认证失败，请重新登录'
                }).encode('utf-8'))
                return
            
            if not user_id:
                print(f"[AUTH DEBUG] No user_id returned from auth")
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
            try:
                conn = db.get_connection()
                print(f"[DB DEBUG] Database connection obtained successfully")
            except Exception as conn_error:
                print(f"[DB ERROR] Failed to get database connection: {conn_error}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': f'数据库连接失败: {str(conn_error)}'
                }).encode('utf-8'))
                return
            
            try:
                cursor = conn.cursor()
                print(f"[DB DEBUG] Database cursor created")
                
                # Detect database type safely
                use_postgres = getattr(db, 'use_postgres', False)
                print(f"[DB DEBUG] Using PostgreSQL: {use_postgres}")
                
                # Get recreate history with COALESCE to handle NULL values
                if use_postgres:
                    query = '''
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
                    '''
                    params = (user_id, per_page, offset)
                else:
                    query = '''
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
                    '''
                    params = (user_id, per_page, offset)
                
                print(f"[DB DEBUG] Executing query with params: {params}")
                cursor.execute(query, params)
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                print(f"[DB DEBUG] Found {len(rows)} recreate history records for user {user_id}")
                
                # Get total count
                if use_postgres:
                    count_query = 'SELECT COUNT(*) FROM recreate_history WHERE user_id = %s'
                    count_params = (user_id,)
                else:
                    count_query = 'SELECT COUNT(*) FROM recreate_history WHERE user_id = ?'
                    count_params = (user_id,)
                
                print(f"[DB DEBUG] Executing count query with params: {count_params}")
                cursor.execute(count_query, count_params)
                
                total_count = cursor.fetchone()[0]
                print(f"[DB DEBUG] Total recreate history count: {total_count}")
                
                history_list = []
                for row in rows:
                    try:
                        history = dict(zip(columns, row))
                        # Ensure no NULL values with proper type conversions
                        formatted_history = {
                            'id': int(history.get('id') or 0),
                            'note_id': str(history.get('note_id') or ''),  # Ensure string type
                            'note_title': str(history.get('original_title') or ''),
                            'original_url': '',  # Not available without note join
                            'original_title': str(history.get('original_title') or ''),
                            'original_content': str(history.get('original_content') or ''),
                            'new_title': str(history.get('recreated_title') or ''),
                            'new_content': str(history.get('recreated_content') or ''),
                            'created_at': str(history.get('created_at') or '')
                        }
                        history_list.append(formatted_history)
                        print(f"[DB DEBUG] Formatted history record {history.get('id')}: {formatted_history['original_title'][:50]}...")
                    except Exception as format_error:
                        print(f"Error formatting history: {format_error}")
                        continue
                
                # Calculate correct total_pages based on actual database count
                total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
                
                response_data = {
                    'success': True,
                    'data': history_list,
                    'pagination': {
                        'limit': limit,
                        'offset': offset,
                        'page': page,
                        'per_page': per_page,
                        'total': total_count,
                        'total_pages': total_pages,
                        'has_more': offset + per_page < total_count
                    }
                }
                
                print(f"[API DEBUG] Returning {len(history_list)} history records")
                print(f"[API DEBUG] Total count from DB: {total_count}")
                print(f"[API DEBUG] Pagination: limit={limit}, offset={offset}, total_pages={total_pages}")
                if history_list:
                    print(f"[API DEBUG] First record keys: {list(history_list[0].keys())}")
                    print(f"[API DEBUG] First record data: {history_list[0]}")
                    print(f"[API DEBUG] Response structure: {response_data}")
                else:
                    print(f"[API DEBUG] Empty history_list - no records found for user {user_id}")
                    print(f"[API DEBUG] Response will be: {response_data}")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
                self.end_headers()
                
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                
            except Exception as db_error:
                print(f"[DB ERROR] Database operation failed: {db_error}")
                import traceback
                print(f"[DB ERROR] Traceback: {traceback.format_exc()}")
                
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': f'数据库查询失败: {str(db_error)}'
                }).encode('utf-8'))
                
            finally:
                try:
                    if 'conn' in locals():
                        conn.close()
                        print(f"[DB DEBUG] Database connection closed")
                except Exception as close_error:
                    print(f"[DB ERROR] Error closing connection: {close_error}")
                
        except Exception as e:
            print(f"[RECREATE HISTORY ERROR] Exception in recreate history API: {str(e)}")
            import traceback
            print(f"[RECREATE HISTORY ERROR] Traceback: {traceback.format_exc()}")
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'获取二创历史失败: {str(e)}'
            }).encode('utf-8'))