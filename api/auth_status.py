"""
检查登录状态API - Vercel Serverless函数
"""
from _utils import parse_request, create_response, require_auth
from _database import db

def handler(request):
    """检查用户登录状态"""
    req_data = parse_request(request)
    
    if req_data['method'] != 'GET':
        return create_response({'success': False, 'error': '只支持GET请求'}, 405)
    
    try:
        user_id = require_auth(req_data['cookies'])
        
        if not user_id:
            return create_response({
                'logged_in': False,
                'user': None
            }, 200)
        
        # 获取用户信息
        user = db.get_user_by_username('')  # 需要通过ID获取用户
        # 简化版本，实际应该有get_user_by_id方法
        
        return create_response({
            'logged_in': True,
            'user': {
                'id': user_id,
                'username': req_data['cookies'].get('username', ''),
                'nickname': req_data['cookies'].get('nickname', '')
            }
        }, 200)
        
    except Exception as e:
        return create_response({
            'logged_in': False,
            'user': None,
            'error': str(e)
        }, 200)