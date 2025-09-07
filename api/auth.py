"""
统一认证API - Vercel Serverless函数
处理登录、注册、登出请求
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response
from _database import db
from http.server import BaseHTTPRequestHandler
import json
import hashlib
import secrets
import re
import urllib.parse
import urllib.request
from urllib.parse import urlparse, parse_qs

# 认证工具函数
def validate_username(username):
    """验证用户名格式"""
    if not username or len(username) < 3 or len(username) > 20:
        return False, "用户名长度必须在3-20个字符之间"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    
    return True, ""

def validate_password(password):
    """验证密码强度"""
    if not password or len(password) < 6:
        return False, "密码至少需要6个字符"
    
    if len(password) > 50:
        return False, "密码不能超过50个字符"
    
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_letter and has_digit):
        return False, "密码必须包含至少一个字母和一个数字"
    
    return True, ""

def validate_email(email):
    """验证邮箱格式"""
    if not email:
        return True, ""  # 邮箱是可选的
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "邮箱格式不正确"
    
    return True, ""

def hash_password(password):
    """密码哈希"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password, stored_hash):
    """验证密码"""
    try:
        salt, hash_value = stored_hash.split(':')
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash == hash_value
    except:
        return False

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_POST(self):
        """根据路径参数处理不同的认证请求"""
        try:
            # 获取查询参数来确定操作类型
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # 从查询参数获取action，如果没有则从路径获取
            action = query_params.get('action', [None])[0]
            if not action:
                # 从路径中提取action，例如 /api/auth?action=login
                path_parts = parsed_url.path.strip('/').split('/')
                if 'login' in self.path:
                    action = 'login'
                elif 'register' in self.path:
                    action = 'register'
                elif 'logout' in self.path:
                    action = 'logout'
                elif 'status' in self.path:
                    action = 'status'
            
            # 初始化数据库
            db.init_database()
            
            if action == 'login':
                self.handle_login()
            elif action == 'register':
                self.handle_register()
            elif action == 'logout':
                self.handle_logout()
            elif action == 'status':
                self.handle_status()
            else:
                self.send_json_response({'success': False, 'error': 'Invalid action'}, 400)
                
        except Exception as e:
            self.send_json_response({'success': False, 'error': f'请求处理失败: {str(e)}'}, 500)
    
    def do_GET(self):
        """处理GET请求（主要用于status检查、图片代理、管理员统计）"""
        try:
            # 解析查询参数
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # 检查是否是图片代理请求
            proxy_url = query_params.get('proxy_url')
            if proxy_url and len(proxy_url) > 0:
                self.handle_image_proxy(urllib.parse.unquote(proxy_url[0]))
                return
            
            # 检查是否是管理员统计请求
            admin_stats = query_params.get('admin_stats')
            if admin_stats and admin_stats[0].lower() == 'true':
                db.init_database()
                self.handle_admin_stats()
                return
            
            # 否则处理登录状态检查
            if 'status' in self.path or query_params.get('action', [''])[0] == 'status':
                db.init_database()
                self.handle_status()
            else:
                self.send_json_response({'success': False, 'error': 'Method not allowed'}, 405)
        except Exception as e:
            self.send_json_response({'success': False, 'error': f'请求处理失败: {str(e)}'}, 500)
    
    def handle_login(self):
        """处理登录请求"""
        # 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            self.send_json_response({'success': False, 'error': '用户名和密码不能为空'}, 400)
            return
        
        # 查找用户
        user = db.get_user_by_username(username)
        if not user:
            self.send_json_response({'success': False, 'error': '用户名或密码错误'}, 401)
            return
        
        # 验证密码
        if not verify_password(password, user['password_hash']):
            self.send_json_response({'success': False, 'error': '用户名或密码错误'}, 401)
            return
        
        # 生成会话ID和JWT token
        session_id = secrets.token_hex(32)
        
        # 导入JWT相关函数
        try:
            from _utils import create_session_token
            token = create_session_token(user['id'])
        except ImportError:
            # 如果导入失败，使用session_id作为token
            token = session_id
        
        # 发送成功响应
        self.send_success_response({
            'success': True,
            'message': '登录成功',
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'nickname': user['nickname'] or user['username'],
                'email': user['email']
            }
        }, session_id, user['id'], token)
    
    def handle_register(self):
        """处理注册请求"""
        # 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        nickname = data.get('nickname', '').strip()
        
        # 验证输入
        valid, msg = validate_username(username)
        if not valid:
            self.send_json_response({'success': False, 'error': msg}, 400)
            return
        
        valid, msg = validate_password(password)
        if not valid:
            self.send_json_response({'success': False, 'error': msg}, 400)
            return
        
        valid, msg = validate_email(email)
        if not valid:
            self.send_json_response({'success': False, 'error': msg}, 400)
            return
        
        # 检查用户名是否已存在
        existing_user = db.get_user_by_username(username)
        if existing_user:
            self.send_json_response({'success': False, 'error': '用户名已存在'}, 400)
            return
        
        # 创建用户
        password_hash = hash_password(password)
        user_id = db.create_user(username, password_hash, email, nickname)
        
        if user_id:
            # 设置默认配置
            db.set_user_config(user_id, 'deepseek_base_url', 'https://api.deepseek.com')
            db.set_user_config(user_id, 'deepseek_model', 'deepseek-chat')
            db.set_user_config(user_id, 'deepseek_temperature', '0.7')
            db.set_user_config(user_id, 'deepseek_max_tokens', '1000')
            
            self.send_json_response({
                'success': True,
                'message': '用户注册成功',
                'user': {
                    'id': user_id,
                    'username': username,
                    'nickname': nickname or username
                }
            }, 201)
        else:
            self.send_json_response({'success': False, 'error': '用户创建失败'}, 500)
    
    def handle_logout(self):
        """处理登出请求"""
        # 清除所有认证相关的cookies
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        
        # Clear all auth cookies by setting them to expire immediately
        cookies_to_clear = ['session_id', 'session_token', 'user_id', 'logged_in']
        for cookie_name in cookies_to_clear:
            self.send_header('Set-Cookie', f'{cookie_name}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT')
        
        self.end_headers()
        
        response_data = {
            'success': True,
            'message': '登出成功'
        }
        
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
    
    def handle_status(self):
        """处理状态检查请求"""
        try:
            # 从cookies中获取session信息
            cookies = {}
            if 'Cookie' in self.headers:
                cookie_header = self.headers['Cookie']
                for cookie in cookie_header.split(';'):
                    if '=' in cookie:
                        key, value = cookie.strip().split('=', 1)
                        cookies[key] = value
            
            session_id = cookies.get('session_id')
            user_id = cookies.get('user_id')
            logged_in = cookies.get('logged_in')
            
            if session_id and user_id and logged_in == 'true':
                # 验证用户是否存在
                user = db.get_user_by_id(int(user_id))
                if user:
                    self.send_json_response({
                        'success': True,
                        'logged_in': True,
                        'user': {
                            'id': user['id'],
                            'username': user['username'],
                            'nickname': user['nickname'] or user['username'],
                            'email': user['email']
                        }
                    }, 200)
                    return
            
            self.send_json_response({
                'success': True,
                'logged_in': False
            }, 200)
            
        except Exception as e:
            self.send_json_response({
                'success': True,
                'logged_in': False
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
            try:
                from _utils import require_auth
                user_id = require_auth(req_data)
            except ImportError:
                # 如果导入失败，使用简单的cookie检查
                user_id = cookies.get('user_id')
                if user_id:
                    try:
                        user_id = int(user_id)
                    except:
                        user_id = None
            
            if not user_id:
                self.send_json_response({
                    'success': False,
                    'error': '请先登录'
                }, 401)
                return
            
            # 简单的管理员检查 - 这里假设用户ID为1的是管理员
            if int(user_id) != 1:
                self.send_json_response({
                    'success': False,
                    'error': '权限不足，仅管理员可访问'
                }, 403)
                return
            
            # 查询统计数据
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
    
    def send_success_response(self, data, session_id, user_id, token):
        """发送成功响应"""
        # 设置Cookie - 在生产环境中使用Secure标志
        secure_flag = '; Secure'
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        
        # Set multiple cookies by calling send_header multiple times with different values
        cookies = [
            f'session_id={session_id}; Path=/; HttpOnly{secure_flag}; SameSite=Lax; Max-Age={86400 * 7}',
            f'session_token={token}; Path=/; HttpOnly{secure_flag}; SameSite=Lax; Max-Age={86400 * 7}',
            f'user_id={user_id}; Path=/; HttpOnly{secure_flag}; SameSite=Lax; Max-Age={86400 * 7}',
            f'logged_in=true; Path=/{secure_flag}; SameSite=Lax; Max-Age={86400 * 7}'
        ]
        
        # Add each cookie as a separate header
        for cookie in cookies:
            self.send_header('Set-Cookie', cookie)
            
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))