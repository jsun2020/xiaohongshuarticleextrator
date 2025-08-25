"""
健康检查API - Vercel Serverless函数
"""
from _utils import parse_request, create_response, require_auth
from _database import db

def handler(request):
    """处理健康检查请求"""
    req_data = parse_request(request)
    
    if req_data['method'] != 'GET':
        return create_response({'success': False, 'error': '只支持GET请求'}, 405)
    
    try:
        # 初始化数据库
        db.init_database()
        
        # 检查用户登录状态
        user_id = require_auth(req_data)
        logged_in = user_id is not None
        
        # 获取笔记总数
        total_notes = 0
        if user_id:
            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                
                if db.use_postgres:
                    cursor.execute('SELECT COUNT(*) FROM notes WHERE user_id = %s', (user_id,))
                else:
                    cursor.execute('SELECT COUNT(*) FROM notes WHERE user_id = ?', (user_id,))
                
                total_notes = cursor.fetchone()[0]
                conn.close()
            except:
                total_notes = 0
        
        # 检查用户的DeepSeek配置
        deepseek_configured = False
        if user_id:
            try:
                user_config = db.get_user_config(user_id)
                deepseek_configured = bool(user_config.get('deepseek_api_key', '').strip())
            except:
                deepseek_configured = False
        
        return create_response({
            'success': True,
            'status': 'healthy',
            'database_status': 'connected',
            'total_notes': total_notes,
            'deepseek_configured': deepseek_configured,
            'logged_in': logged_in
        }, 200)
        
    except Exception as e:
        return create_response({
            'success': False,
            'status': 'error',
            'error': str(e)
        }, 500)