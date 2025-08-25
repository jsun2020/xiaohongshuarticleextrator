"""
Vercel Serverless 工具函数
"""
import json
import os
from urllib.parse import parse_qs
from http.cookies import SimpleCookie

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
    if hasattr(request, 'cookies'):
        cookies = dict(request.cookies)
    elif 'cookie' in request.headers:
        cookie = SimpleCookie()
        cookie.load(request.headers['cookie'])
        cookies = {key: morsel.value for key, morsel in cookie.items()}
    
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

def require_auth(cookies):
    """检查用户认证状态"""
    session_id = cookies.get('session_id')
    user_id = cookies.get('user_id')
    
    if not session_id or not user_id:
        return None
    
    # 这里应该验证session的有效性
    # 简化版本，实际应该查询数据库验证session
    try:
        return int(user_id)
    except:
        return None

def get_database_url():
    """获取数据库连接URL"""
    # 从环境变量获取数据库URL
    # 在Vercel中，SQLite不适用，需要使用外部数据库
    return os.getenv('DATABASE_URL', 'sqlite:///xiaohongshu_notes.db')