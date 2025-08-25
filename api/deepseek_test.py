"""
测试DeepSeek连接API - Vercel Serverless函数
"""
from _utils import parse_request, create_response, require_auth
from _database import db
from _deepseek_api import deepseek_api

def handler(request):
    """处理DeepSeek连接测试请求"""
    # 初始化数据库
    db.init_database()
    
    req_data = parse_request(request)
    
    if req_data['method'] != 'POST':
        return create_response({'success': False, 'error': '只支持POST请求'}, 405)
    
    # 检查用户认证
    user_id = require_auth(req_data['cookies'])
    if not user_id:
        return create_response({'success': False, 'error': '请先登录'}, 401)
    
    try:
        # 获取用户配置
        user_config = db.get_user_config(user_id)
        
        # 测试连接
        result = deepseek_api.test_connection(user_config)
        
        if result['success']:
            return create_response(result, 200)
        else:
            return create_response(result, 400)
            
    except Exception as e:
        return create_response({
            'success': False,
            'error': f'测试连接失败: {str(e)}'
        }, 500)