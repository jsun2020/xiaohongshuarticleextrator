"""
用户登录API - Vercel Serverless函数
"""
import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from _utils import parse_request, create_response
    from _database import db
except ImportError as e:
    print(f"Import error: {e}")
    # 尝试相对导入
    import importlib.util
    
    utils_path = os.path.join(parent_dir, '_utils.py')
    db_path = os.path.join(parent_dir, '_database.py')
    
    spec = importlib.util.spec_from_file_location("_utils", utils_path)
    _utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_utils)
    
    spec = importlib.util.spec_from_file_location("_database", db_path)
    _database = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_database)
    
    parse_request = _utils.parse_request
    create_response = _utils.create_response
    db = _database.db
import hashlib
import secrets

def verify_password(password, stored_hash):
    """验证密码"""
    try:
        salt, hash_value = stored_hash.split(':')
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash == hash_value
    except:
        return False

import json

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
    
    if request.method == 'POST':
        # 初始化数据库
        db.init_database()
        
        try:
            # 读取请求体
            data = json.loads(request.body)
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                return send_error_response({'success': False, 'error': '用户名和密码不能为空'}, 400)
            
            # 查找用户
            user = db.get_user_by_username(username)
            if not user:
                return send_error_response({'success': False, 'error': '用户名或密码错误'}, 401)
            
            # 验证密码
            if not verify_password(password, user['password_hash']):
                return send_error_response({'success': False, 'error': '用户名或密码错误'}, 401)
            
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
            return send_success_response({
                'success': True,
                'message': '登录成功',
                'token': token,  # 添加token到响应体
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'nickname': user['nickname'] or user['username'],
                    'email': user['email']
                }
            }, session_id, user['id'], token)
            
        except Exception as e:
            return send_error_response({'success': False, 'error': f'登录失败: {str(e)}'}, 500)
    
    return send_error_response({'error': 'Method not allowed'}, 405)

def send_success_response(data, session_id, user_id, token):
    """发送成功响应"""
    # 设置Cookie - 在生产环境中使用Secure标志
    secure_flag = '; Secure'
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cookie',
            'Set-Cookie': [
                f'session_id={session_id}; Path=/; HttpOnly{secure_flag}; SameSite=Lax; Max-Age={86400 * 7}',
                f'session_token={token}; Path=/; HttpOnly{secure_flag}; SameSite=Lax; Max-Age={86400 * 7}',
                f'user_id={user_id}; Path=/; HttpOnly{secure_flag}; SameSite=Lax; Max-Age={86400 * 7}',
                f'logged_in=true; Path=/{secure_flag}; SameSite=Lax; Max-Age={86400 * 7}'
            ]
        },
        'body': json.dumps(data, ensure_ascii=False)
    }

def send_error_response(data, status_code):
    """发送错误响应"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cookie'
        },
        'body': json.dumps(data, ensure_ascii=False)
    }