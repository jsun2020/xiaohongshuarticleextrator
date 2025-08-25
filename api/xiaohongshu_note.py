"""
获取小红书笔记API - Vercel Serverless函数
"""
from _utils import parse_request, create_response, require_auth
from _database import db
from _xhs_crawler import get_xiaohongshu_note

def handler(request):
    """处理获取小红书笔记请求"""
    # 初始化数据库
    db.init_database()
    
    req_data = parse_request(request)
    
    if req_data['method'] != 'POST':
        return create_response({'success': False, 'error': '只支持POST请求'}, 405)
    
    # 检查用户认证
    user_id = require_auth(req_data)
    if not user_id:
        return create_response({'success': False, 'error': '请先登录'}, 401)
    
    try:
        data = req_data['body']
        url = data.get('url', '').strip()
        
        if not url:
            return create_response({'success': False, 'error': '请提供小红书链接'}, 400)
        
        # 调用爬虫获取笔记信息
        result = get_xiaohongshu_note(url)
        
        if result.get('success'):
            note_data = result['data']
            
            # 保存到数据库
            save_success = db.save_note(note_data, user_id)
            
            if save_success:
                return create_response({
                    'success': True,
                    'message': '笔记获取并保存成功',
                    'data': note_data,
                    'saved_to_db': True
                }, 200)
            else:
                return create_response({
                    'success': True,
                    'message': '笔记获取成功，但保存失败',
                    'data': note_data,
                    'saved_to_db': False
                }, 200)
        else:
            return create_response({
                'success': False,
                'error': result.get('error', '获取笔记失败')
            }, 400)
            
    except Exception as e:
        return create_response({
            'success': False,
            'error': f'处理请求失败: {str(e)}'
        }, 500)