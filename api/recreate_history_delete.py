"""
删除二创历史API - Vercel Serverless函数
"""
from _utils import parse_request, create_response, require_auth
from _database import db

def handler(request):
    """处理删除二创历史请求"""
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
        # 从查询参数获取history_id
        history_id = req_data['query'].get('history_id')
        if not history_id:
            return create_response({'success': False, 'error': '缺少历史记录ID'}, 400)
        
        # 删除二创历史
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            if db.use_postgres:
                cursor.execute('DELETE FROM recreate_history WHERE id = %s AND user_id = %s', (history_id, user_id))
            else:
                cursor.execute('DELETE FROM recreate_history WHERE id = ? AND user_id = ?', (history_id, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return create_response({
                    'success': True,
                    'message': '二创历史删除成功'
                }, 200)
            else:
                return create_response({
                    'success': False,
                    'error': '历史记录不存在或无权限删除'
                }, 404)
                
        finally:
            conn.close()
            
    except Exception as e:
        return create_response({
            'success': False,
            'error': f'删除二创历史失败: {str(e)}'
        }, 500)