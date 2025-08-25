"""
用户登出API - Vercel Serverless函数
"""
from _utils import parse_request, create_response

def handler(request):
    """处理用户登出请求"""
    req_data = parse_request(request)
    
    if req_data['method'] != 'POST':
        return create_response({'success': False, 'error': '只支持POST请求'}, 405)
    
    # 清除Cookie
    cookies = {
        'session_id': {
            'value': '',
            'max_age': 0
        },
        'user_id': {
            'value': '',
            'max_age': 0
        },
        'logged_in': {
            'value': '',
            'max_age': 0
        }
    }
    
    return create_response({
        'success': True,
        'message': '登出成功'
    }, 200, cookies)