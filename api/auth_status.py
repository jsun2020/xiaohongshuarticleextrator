"""
检查登录状态API + 图片代理 - Vercel Serverless函数
支持:
- GET /api/auth_status - 检查登录状态
- GET /api/auth_status?proxy_url=<image_url> - 图片代理（绕过防盗链）
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
            if not image_url:
                self.send_response(400)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'URL parameter is missing')
                return
            
            # 设置请求头，伪造 Referer 绕过防盗链
            headers = {
                'Referer': 'https://www.xiaohongshu.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            # 创建请求
            request = urllib.request.Request(image_url, headers=headers)
            
            # 获取图片
            with urllib.request.urlopen(request, timeout=30) as response:
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
            self.send_response(e.code)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'HTTP Error: {e.code}'.encode())
        except urllib.error.URLError as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')  
            self.end_headers()
            self.wfile.write(f'URL Error: {str(e)}'.encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
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