"""
用户登录API - Vercel Serverless函数
"""
from _utils import parse_request, create_response, create_session_token
from _database import db
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_utils import verify_password

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
            return create_response({
                'success': False,
                'error': '用户名和密码不能为空'
            }, 400)
        
        # 获取用户信息
        user = db.get_user_by_username(username)
        if not user:
            return create_response({
                'success': False,
                'error': '用户名或密码错误'
            }, 401)
        
        # 验证密码
        if not verify_password(password, user['password_hash']):
            return create_response({
                'success': False,
                'error': '用户名或密码错误'
            }, 401)
        
        # 创建会话令牌
        token = create_session_token(user['id'])
        
        # 设置cookie
        cookies = {
            'session_token': {
                'value': token,
                'httponly': True,
                'secure': True,
                'samesite': 'Strict',
                'max_age': 86400  # 24小时
            }
        }
        
        return create_response({
            'success': True,
            'message': '登录成功',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'nickname': user.get('nickname', user['username']),
                'email': user.get('email', '')
            },
            'token': token
        }, 200, cookies)
        
    except Exception as e:
        return create_response({
            'success': False,
            'error': f'登录失败: {str(e)}'
        }, 500)