"""
删除笔记API - Vercel Serverless函数
"""
from _utils import parse_request, create_response, require_auth
from _database import db
import re

def handler(request):
    """处理删除笔记请求"""
    # 初始化数据库
    db.init_database()
    
    req_data = parse_request(request)
    
    if req_data['method'] != 'DELETE':
        return create_response({'success': False, 'error': '只支持DELETE请求'}, 405)
    
    # 检查用户认证
    user_id = require_auth(req_data)
    if not user_id:
        return create_response({'success': False, 'error': '请先登录'}, 401)
    
    try:
        # 从URL路径中提取note_id
        # URL格式: /api/xiaohongshu/notes/{note_id}
        path = req_data.get('headers', {}).get('x-vercel-pathname', request.url if hasattr(request, 'url') else '')
        match = re.search(r'/api/xiaohongshu/notes/([^/]+)', path)
        
        if not match:
            # 尝试从查询参数获取note_id作为备用方案
            note_id = req_data['query'].get('note_id')
            if not note_id:
                return create_response({'success': False, 'error': '缺少笔记ID'}, 400)
        else:
            note_id = match.group(1)
        
        # 使用database manager的删除方法
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 删除笔记及其相关数据
            if db.use_postgres:
                cursor.execute('DELETE FROM notes WHERE note_id = %s AND user_id = %s', (note_id, user_id))
            else:
                cursor.execute('DELETE FROM notes WHERE note_id = ? AND user_id = ?', (note_id, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return create_response({
                    'success': True,
                    'message': f'笔记 {note_id} 删除成功'
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