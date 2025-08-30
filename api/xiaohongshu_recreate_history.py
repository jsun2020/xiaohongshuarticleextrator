"""
二创历史列表API - Vercel Serverless函数
Handles: GET /api/xiaohongshu/recreate/history
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response, require_auth
from _database import db
import json
from urllib.parse import urlparse, parse_qs

def handler(request):
    """Vercel serverless function handler"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cookie'
            }
        }
    
    if request.method == 'GET':
        """处理二创历史请求"""
        # 初始化数据库
        db.init_database()
        print(f"[CRITICAL DEBUG] Recreate history - database path: {db.db_path}")
        print(f"[CRITICAL DEBUG] Recreate history - database exists: {os.path.exists(db.db_path)}")
        print(f"[CRITICAL DEBUG] Recreate history - current working dir: {os.getcwd()}")
        print(f"[CRITICAL DEBUG] Recreate history - temp dir: {os.environ.get('TMPDIR', 'not set')}")
        print(f"[DB DEBUG] Recreate history using database: {db.db_path}")
        
        try:
            # 解析查询参数
            query_params = {}
            if hasattr(request, 'url'):
                parsed_url = urlparse(request.url)
                query_params = parse_qs(parsed_url.query)
            elif hasattr(request, 'query'):
                query_params = request.query or {}
            
            # 解析Cookie进行认证
            cookies = {}
            cookie_header = request.headers.get('cookie', '') or request.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
            
            req_data = {
                'method': 'GET',
                'query': query_params,
                'cookies': cookies,
                'headers': dict(request.headers)
            }
            
            # 检查用户认证
            print(f"[AUTH DEBUG] Cookies in request: {list(cookies.keys())}")
            print(f"[AUTH DEBUG] Headers: {list(request.headers.keys())}")
            
            user_id = require_auth(req_data)
            print(f"[AUTH DEBUG] User ID from auth: {user_id}")
            
            if not user_id:
                return {
                    'statusCode': 401,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'success': False, 'error': '请先登录'})
                }
            
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
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cookie'
                    },
                    'body': json.dumps(response_data, ensure_ascii=False)
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Error in recreate history API: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'获取二创历史失败: {str(e)}'
                })
            }
    
    return {
        'statusCode': 405,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': 'Method not allowed'})
    }