"""
检查登录状态API + 图片代理 + 管理员统计 - Vercel Serverless函数
支持:
- GET /api/auth_status - 检查登录状态
- GET /api/auth_status?proxy_url=<image_url> - 图片代理（绕过防盗链）
- GET /api/auth_status?admin_stats=true - 管理员统计数据
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response, require_auth
from _database import db
from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import urllib.request
from urllib.parse import parse_qs, urlparse

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求 - 登录状态检查或图片代理"""
        try:
            # 解析查询参数
            query_params = {}
            if self.path and '?' in self.path:
                query_string = self.path.split('?', 1)[1]
                query_params = parse_qs(query_string)
            
            # 检查是否是图片代理请求
            proxy_url = query_params.get('proxy_url')
            if proxy_url and len(proxy_url) > 0:
                self.handle_image_proxy(urllib.parse.unquote(proxy_url[0]))
                return
            
            # 检查是否是管理员统计请求
            admin_stats = query_params.get('admin_stats')
            if admin_stats and admin_stats[0].lower() == 'true':
                self.handle_admin_stats()
                return
            
            # 否则处理登录状态检查
            self.handle_auth_status()
            
        except Exception as e:
            self.send_json_response({
                'logged_in': False,
                'user': None,
                'error': str(e)
            }, 200)
    
    def handle_image_proxy(self, image_url):
        """处理图片代理请求"""
        try:
            print(f"[Image Proxy] Proxying image: {image_url}")
            
            if not image_url:
                self.send_response(400)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'URL parameter is missing')
                return
            
            # 设置请求头，伪造 Referer 绕过防盗链
            headers = {
                'Referer': 'https://www.xiaohongshu.com/',
                'Origin': 'https://www.xiaohongshu.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            print(f"[Image Proxy] Request headers: {headers}")
            
            # 创建请求
            request = urllib.request.Request(image_url, headers=headers)
            
            # 获取图片
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status == 200:
                    # 获取内容类型
                    content_type = response.headers.get('Content-Type', 'image/jpeg')
                    content_length = response.headers.get('Content-Length')
                    
                    # 设置响应头
                    self.send_response(200)
                    self.send_header('Content-Type', content_type)
                    if content_length:
                        self.send_header('Content-Length', content_length)
                    
                    # 设置缓存头
                    self.send_header('Cache-Control', 'public, max-age=86400')  # 缓存1天
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    # 流式传输图片数据
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                else:
                    self.send_response(response.status)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f'Failed to fetch image: {response.status}'.encode())
        
        except urllib.error.HTTPError as e:
            print(f"[Image Proxy] HTTP Error {e.code}: {e.reason} for URL: {image_url}")
            self.send_response(e.code if e.code != 403 else 200)  # Convert 403 to 200 to avoid client errors
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(f'HTTP Error: {e.code} - {e.reason}'.encode())
        except urllib.error.URLError as e:
            print(f"[Image Proxy] URL Error: {str(e)} for URL: {image_url}")
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(f'URL Error: {str(e)}'.encode())
        except Exception as e:
            print(f"[Image Proxy] General Error: {str(e)} for URL: {image_url}")
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(f'Error proxying image: {str(e)}'.encode())
    
    def handle_auth_status(self):
        """处理登录状态检查"""
        try:
            # 解析Cookie
            cookies = {}
            cookie_header = self.headers.get('Cookie', '') or self.headers.get('cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
            
            # 检查认证
            req_data = {
                'method': 'GET',
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            user_id = require_auth(req_data)
            
            if not user_id:
                self.send_json_response({
                    'logged_in': False,
                    'user': None
                }, 200)
                return
            
            # 初始化数据库并获取完整用户信息
            db.init_database()
            user_data = db.get_user_by_id(user_id)
            
            if not user_data:
                # User ID is valid but user no longer exists in DB
                self.send_json_response({
                    'logged_in': False,
                    'user': None
                }, 200)
                return
            
            # 返回完整用户信息
            self.send_json_response({
                'logged_in': True,
                'user': {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'nickname': user_data['nickname'] or user_data['username'],
                    'email': user_data['email'] or ''
                }
            }, 200)
            
        except Exception as e:
            self.send_json_response({
                'logged_in': False,
                'user': None,
                'error': str(e)
            }, 200)
    
    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def handle_admin_stats(self):
        """处理管理员统计数据请求"""
        try:
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
                'body': {},
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            # 检查用户认证
            user_id = require_auth(req_data)
            if not user_id:
                self.send_json_response({
                    'success': False,
                    'error': '请先登录'
                }, 401)
                return
            
            # 简单的管理员检查 - 这里假设用户ID为1的是管理员
            # 实际项目中应该在数据库中添加is_admin字段
            if user_id != 1:
                self.send_json_response({
                    'success': False,
                    'error': '权限不足，仅管理员可访问'
                }, 403)
                return
            
            # 查询统计数据
            db.init_database()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            try:
                if db.use_postgres:
                    # PostgreSQL查询
                    cursor.execute("SELECT COUNT(*) FROM users")
                    stats['total_users'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL '24 hours'")
                    stats['new_users_today'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM notes")
                    stats['total_notes'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM notes WHERE created_at > NOW() - INTERVAL '24 hours'")
                    stats['notes_today'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM recreate_history")
                    stats['total_recreations'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM recreate_history WHERE created_at > NOW() - INTERVAL '24 hours'")
                    stats['recreations_today'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM notes WHERE created_at > NOW() - INTERVAL '24 hours'")
                    stats['active_users_today'] = cursor.fetchone()[0]
                    
                else:
                    # SQLite查询
                    cursor.execute("SELECT COUNT(*) FROM users")
                    stats['total_users'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM users WHERE created_at > datetime('now', '-1 day')")
                    stats['new_users_today'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM notes")
                    stats['total_notes'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM notes WHERE created_at > datetime('now', '-1 day')")
                    stats['notes_today'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM recreate_history")
                    stats['total_recreations'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM recreate_history WHERE created_at > datetime('now', '-1 day')")
                    stats['recreations_today'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM notes WHERE created_at > datetime('now', '-1 day')")
                    stats['active_users_today'] = cursor.fetchone()[0]
                
                self.send_json_response({
                    'success': True,
                    'data': stats
                }, 200)
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"获取管理员统计数据失败: {e}")
            self.send_json_response({
                'success': False,
                'error': f'获取统计数据失败: {str(e)}'
            }, 500)