"""
获取笔记列表API - Vercel Serverless函数
Handles: GET /api/xiaohongshu/notes
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
        """处理获取笔记列表请求"""
        # 初始化数据库
        db.init_database()
        
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
            user_id = require_auth(req_data)
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
            
            # 获取用户的笔记列表和总数
            notes = db.get_notes(user_id, page, per_page)
            total_count = db.get_notes_count(user_id)
            
            # 格式化笔记数据
            formatted_notes = []
            for note in notes:
                try:
                    # 处理images_data结构
                    images_data = note.get('images_data', {})
                    if isinstance(images_data, dict):
                        # 如果是对象，提取images数组
                        images = images_data.get('images', [])
                        videos = images_data.get('videos', [])
                    elif isinstance(images_data, list):
                        # 如果已经是数组，直接使用
                        images = images_data
                        videos = []
                    else:
                        images = []
                        videos = []
                    
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
                        'images': images,
                        'videos': videos,
                        'tags': [],  # 添加空的tags字段，避免前端错误
                        'created_at': str(note.get('created_at', ''))
                    }
                    formatted_notes.append(formatted_note)
                except Exception as format_error:
                    print(f"Error formatting note: {format_error}")
                    continue
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
                    'Pragma': 'no-cache',
                    'Expires': '0',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cookie'
                },
                'body': json.dumps({
                    'success': True,
                    'data': formatted_notes,
                    'pagination': {
                        'limit': limit,
                        'offset': offset,
                        'page': page,
                        'per_page': per_page,
                        'total': total_count
                    }
                }, ensure_ascii=False)
            }
            
        except Exception as e:
            print(f"Error in notes API: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'获取笔记列表失败: {str(e)}'
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