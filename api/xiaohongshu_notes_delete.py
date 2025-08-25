"""
删除笔记API - Vercel Serverless函数
"""
from _utils import parse_request, create_response, require_auth
from _database import db

def handler(request):
    """处理删除笔记请求"""
    # 初始化数据库
    db.init_database()
    
    req_data = parse_request(request)
    
    if req_data['method'] != 'DELETE':
        return create_response({'success': False, 'error': '只支持DELETE请求'}, 405)
    
    # 检查用户认证
    user_id = require_auth(req_data['cookies'])
    if not user_id:
        return create_response({'success': False, 'error': '请先登录'}, 401)
    
    try:
        # 从查询参数获取note_id
        note_id = req_data['query'].get('note_id')
        if not note_id:
            return create_response({'success': False, 'error': '缺少笔记ID'}, 400)
        
        # 删除笔记（需要在数据库类中添加此方法）
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            if db.use_postgres:
                cursor.execute('DELETE FROM notes WHERE id = %s AND user_id = %s', (note_id, user_id))
            else:
                cursor.execute('DELETE FROM notes WHERE id = ? AND user_id = ?', (note_id, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return create_response({
                    'success': True,
                    'message': '笔记删除成功'
                }, 200)
            else:
                return create_response({
                    'success': False,
                    'error': '笔记不存在或无权限删除'
                }, 404)
                
        finally:
            conn.close()
            
    except Exception as e:
        return create_response({
            'success': False,
            'error': f'删除笔记失败: {str(e)}'
        }, 500)