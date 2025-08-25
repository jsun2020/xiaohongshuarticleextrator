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

def handler(request):
    """处理用户登录请求"""
    # 初始化数据库
    db.init_database()
    
    req_data = parse_request(request)
    
    if req_data['method'] != 'POST':
        return create_response({'success': False, 'error': '只支持POST请求'}, 405)
    
    try:
        data = req_data['body']
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return create_response({'success': False, 'error': '用户名和密码不能为空'}, 400)
        
        # 查找用户
        user = db.get_user_by_username(username)
        if not user:
            return create_response({'success': False, 'error': '用户名或密码错误'}, 401)
        
        # 验证密码
        if not verify_password(password, user['password_hash']):
            return create_response({'success': False, 'error': '用户名或密码错误'}, 401)
        
        # 生成会话ID
        session_id = secrets.token_hex(32)
        
        # 设置Cookie
        cookies = {
            'session_id': {
                'value': session_id,
                'httponly': True,
                'secure': True,
                'samesite': 'Lax',
                'max_age': 86400 * 7
            },
            'user_id': {
                'value': str(user['id']),
                'httponly': True,
                'secure': True,
                'samesite': 'Lax',
                'max_age': 86400 * 7
            },
            'logged_in': {
                'value': 'true',
                'secure': True,
                'samesite': 'Lax',
                'max_age': 86400 * 7
            }
        }
        
        return create_response({
            'success': True,
            'message': '登录成功',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'nickname': user['nickname'] or user['username'],
                'email': user['email']
            }
        }, 200, cookies)
        
    except Exception as e:
        return create_response({'success': False, 'error': f'登录失败: {str(e)}'}, 500)