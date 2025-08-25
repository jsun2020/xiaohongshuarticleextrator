"""
二创历史API - Vercel Serverless函数
"""
from _utils import parse_request, create_response, require_auth
from _database import db

def handler(request):
    """处理二创历史请求"""
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
        
        # 获取二创历史
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            offset = (page - 1) * per_page
            
            if db.use_postgres:
                cursor.execute('''
                    SELECT rh.*, n.title as note_title, n.original_url
                    FROM recreate_history rh
                    LEFT JOIN notes n ON rh.note_id = n.id
                    WHERE rh.user_id = %s
                    ORDER BY rh.created_at DESC
                    LIMIT %s OFFSET %s
                ''', (user_id, per_page, offset))
            else:
                cursor.execute('''
                    SELECT rh.*, n.title as note_title, n.original_url
                    FROM recreate_history rh
                    LEFT JOIN notes n ON rh.note_id = n.id
                    WHERE rh.user_id = ?
                    ORDER BY rh.created_at DESC
                    LIMIT ? OFFSET ?
                ''', (user_id, per_page, offset))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            history_list = []
            for row in rows:
                history = dict(zip(columns, row))
                history_list.append({
                    'id': history['id'],
                    'note_id': history['note_id'],
                    'note_title': history.get('note_title', ''),
                    'original_url': history.get('original_url', ''),
                    'original_title': history['original_title'],
                    'original_content': history['original_content'],
                    'recreated_title': history['recreated_title'],
                    'recreated_content': history['recreated_content'],
                    'created_at': history['created_at']
                })
            
            return create_response({
                'success': True,
                'data': history_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': len(history_list)
                }
            }, 200)
            
        finally:
            conn.close()
            
    except Exception as e:
        return create_response({
            'success': False,
            'error': f'获取二创历史失败: {str(e)}'
        }, 500)