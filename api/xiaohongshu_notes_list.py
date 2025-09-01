"""
小红书笔记API - 合并版 - Vercel Serverless函数
Handles: 
- POST /api/xiaohongshu_notes_list - 采集笔记
- GET /api/xiaohongshu_notes_list - 获取笔记列表
- DELETE /api/xiaohongshu_notes_list/{note_id} - 删除笔记
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
from _xhs_crawler import get_xiaohongshu_note

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_POST(self):
        """处理获取小红书笔记请求"""
        try:
            # 初始化数据库
            db.init_database()
            
            # 获取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                try:
                    data = json.loads(body.decode('utf-8'))
                except json.JSONDecodeError:
                    data = {}
            else:
                data = {}
            
            # 解析Cookie进行认证
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = urllib.parse.unquote(value)
            
            req_data = {
                'method': 'POST',
                'body': data,
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            # 检查用户认证
            user_id = require_auth(req_data)
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
            
            url = data.get('url', '').strip()
            if not url:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False, 
                    'error': '请提供小红书链接'
                }).encode('utf-8'))
                return
            
            # 调用爬虫获取笔记信息
            result = get_xiaohongshu_note(url)
            
            if result.get('success'):
                note_data = result['data']
                
                # 保存到数据库
                print(f"[API] Attempting to save note: {note_data.get('note_id')}")
                save_success = db.save_note(note_data, user_id)
                print(f"[API] Save result: {save_success}")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
                self.end_headers()
                
                response_data = {
                    'success': True,
                    'message': '笔记获取并保存成功' if save_success else '笔记获取成功，但保存失败',
                    'data': note_data,
                    'saved_to_db': save_success
                }
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': result.get('error', '获取笔记失败')
                }).encode('utf-8'))
                
        except Exception as e:
            print(f"[API Error] Exception in xiaohongshu_note collection: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'处理请求失败: {str(e)}'
            }).encode('utf-8'))
    
    def do_GET(self):
        """处理获取笔记列表请求"""
        try:
            # 初始化数据库
            db.init_database()
            
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
            user_id = require_auth(req_data)
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
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
            self.end_headers()
            
            response_data = {
                'success': True,
                'data': formatted_notes,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'page': page,
                    'per_page': per_page,
                    'total': total_count
                }
            }
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            print(f"Error in notes list API: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'获取笔记列表失败: {str(e)}'
            }).encode('utf-8'))
    
    def do_DELETE(self):
        """处理删除笔记请求"""
        try:
            # 初始化数据库
            db.init_database()
            
            # 从查询参数中提取note_id
            # URL格式: /api/xiaohongshu_notes_list?note_id={note_id}
            query_params = {}
            if self.path and '?' in self.path:
                query_string = self.path.split('?', 1)[1]
                query_params = parse_qs(query_string)
            
            note_id = None
            if 'note_id' in query_params:
                note_id = query_params['note_id'][0]
            
            if not note_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': '缺少笔记ID'
                }).encode('utf-8'))
                return
            
            # 解析Cookie进行认证
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = urllib.parse.unquote(value)
            
            req_data = {
                'method': 'DELETE',
                'body': {},
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            # 检查用户认证
            user_id = require_auth(req_data)
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
            
            # 删除笔记
            success = db.delete_note(user_id, note_id)
            
            if success:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': f'笔记 {note_id} 删除成功'
                }, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': '笔记不存在或删除失败'
                }).encode('utf-8'))
        
        except Exception as e:
            print(f"Error in delete note API: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'删除笔记失败: {str(e)}'
            }).encode('utf-8'))