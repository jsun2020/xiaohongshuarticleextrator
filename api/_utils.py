"""
Vercel Serverless 工具函数
"""
import json
import os
import jwt
from urllib.parse import parse_qs
from http.cookies import SimpleCookie
from datetime import datetime, timedelta
from typing import Optional

# JWT认证配置
JWT_SECRET = os.environ.get('JWT_SECRET', 'xiaohongshu_app_secret_key_2024')

def parse_request(request):
    """解析Vercel请求对象"""
    method = request.method
    
    # 解析请求体
    body = {}
    if hasattr(request, 'body') and request.body:
        try:
            body = json.loads(request.body.decode('utf-8'))
        except:
            body = {}
    
    # 解析查询参数
    query = {}
    if hasattr(request, 'args'):
        query = dict(request.args)
    elif hasattr(request, 'query'):
        query = dict(request.query)
    
    # 解析Cookies
    cookies = {}
    headers = dict(request.headers) if hasattr(request, 'headers') else {}
    
    if hasattr(request, 'cookies'):
        cookies = dict(request.cookies)
    elif 'cookie' in headers:
        try:
            cookie = SimpleCookie()
            cookie.load(headers['cookie'])
            cookies = {key: morsel.value for key, morsel in cookie.items()}
        except:
            # 简单解析cookie字符串
            cookie_str = headers['cookie']
            for item in cookie_str.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookies[key] = value
    elif 'Cookie' in headers:
        try:
            cookie = SimpleCookie()
            cookie.load(headers['Cookie'])
            cookies = {key: morsel.value for key, morsel in cookie.items()}
        except:
            # 简单解析cookie字符串
            cookie_str = headers['Cookie']
            for item in cookie_str.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookies[key] = value
    
    return {
        'method': method,
        'body': body,
        'query': query,
        'cookies': cookies,
        'headers': dict(request.headers) if hasattr(request, 'headers') else {}
    }

def create_response(data, status_code=200, cookies=None):
    """创建Vercel响应"""
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
    
    if cookies:
        cookie_strings = []
        for name, value in cookies.items():
            if isinstance(value, dict):
                cookie_str = f"{name}={value.get('value', '')}"
                if value.get('httponly'):
                    cookie_str += "; HttpOnly"
                if value.get('secure'):
                    cookie_str += "; Secure"
                if value.get('samesite'):
                    cookie_str += f"; SameSite={value['samesite']}"
                if value.get('max_age'):
                    cookie_str += f"; Max-Age={value['max_age']}"
                cookie_strings.append(cookie_str)
            else:
                cookie_strings.append(f"{name}={value}")
        
        if cookie_strings:
            headers['Set-Cookie'] = cookie_strings

    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(data, ensure_ascii=False)
    }

def create_session_token(user_id: int) -> str:
    """创建JWT会话令牌"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1),  # 24小时过期
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_session_token(token: str) -> Optional[int]:
    """验证JWT会话令牌并返回用户ID"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(req_data):
    """检查用户认证状态 - 支持JWT tokens"""
    # 1. 尝试从Authorization header获取token
    headers = req_data.get('headers', {})
    auth_header = headers.get('authorization') or headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]  # 移除 'Bearer ' 前缀
        user_id = verify_session_token(token)
        if user_id:
            return user_id
    
    # 2. 尝试从Cookie获取token
    cookies = req_data.get('cookies', {})
    session_token = cookies.get('session_token')
    if session_token:
        user_id = verify_session_token(session_token)
        if user_id:
            return user_id
    
    # 3. 兼容旧的cookie格式
    session_id = cookies.get('session_id')
    user_id_cookie = cookies.get('user_id')
    
    if session_id and user_id_cookie:
        try:
            user_id = int(user_id_cookie)
            return user_id
        except:
            pass
    
    return None

def get_database_url():
    """获取数据库连接URL"""
    # 从环境变量获取数据库URL
    # 在Vercel中，SQLite不适用，需要使用外部数据库
    return os.getenv('DATABASE_URL', 'sqlite:///xiaohongshu_notes.db')