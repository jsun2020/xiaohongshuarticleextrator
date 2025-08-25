"""
检查登录状态API - Vercel Serverless函数
"""
import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from _utils import parse_request, create_response, require_auth
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
    require_auth = _utils.require_auth
    db = _database.db

def handler(request):
    """检查用户登录状态"""
    req_data = parse_request(request)
    
    if req_data['method'] != 'GET':
        return create_response({'success': False, 'error': '只支持GET请求'}, 405)
    
    try:
        user_id = require_auth(req_data)
        
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