"""
获取笔记列表API - Vercel Serverless函数
"""
from _utils import parse_request, create_response, require_auth
from _database import db

def handler(request):
    """处理获取笔记列表请求"""
    # 初始化数据库
    db.init_database()
    
    req_data = parse_request(request)
    
    if req_data['method'] != 'GET':
        return create_response({'success': False, 'error': '只支持GET请求'}, 405)
    
    # 检查用户认证
    user_id = require_auth(req_data['cookies'])
    if not user_id:
        return create_response({'success': False, 'error': '请先登录'}, 401)
    
    try:
        # 获取分页参数
        page = int(req_data['query'].get('page', [1])[0] if isinstance(req_data['query'].get('page'), list) else req_data['query'].get('page', 1))
        per_page = int(req_data['query'].get('per_page', [10])[0] if isinstance(req_data['query'].get('per_page'), list) else req_data['query'].get('per_page', 10))
        
        # 获取用户的笔记列表
        notes = db.get_notes(user_id, page, per_page)
        
        # 格式化笔记数据
        formatted_notes = []
        for note in notes:
            formatted_note = {
                'id': note['id'],
                'note_id': note['note_id'],
                'title': note['title'],
                'content': note['content'],
                'type': note['note_type'],
                'publish_time': note['publish_time'],
                'location': note['location'],
                'original_url': note['original_url'],
                'author': note.get('author_data', {}),
                'stats': note.get('stats_data', {}),
                'images': note.get('images_data', []),
                'created_at': note['created_at']
            }
            formatted_notes.append(formatted_note)
        
        return create_response({
            'success': True,
            'data': formatted_notes,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(formatted_notes)
            }
        }, 200)
        
    except Exception as e:
        return create_response({
            'success': False,
            'error': f'获取笔记列表失败: {str(e)}'
        }, 500)