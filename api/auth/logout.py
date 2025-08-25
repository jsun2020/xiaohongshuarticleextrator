"""
用户登出API - Vercel Serverless函数
"""
import sys
import os

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from _utils import parse_request, create_response
except ImportError as e:
    print(f"Import error: {e}")
    # 尝试相对导入
    import importlib.util
    
    utils_path = os.path.join(parent_dir, '_utils.py')
    
    spec = importlib.util.spec_from_file_location("_utils", utils_path)
    _utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_utils)
    
    parse_request = _utils.parse_request
    create_response = _utils.create_response

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