"""
小红书笔记二创API - Vercel Serverless函数
"""
from _utils import parse_request, create_response, require_auth
from _database import db
from _deepseek_api import deepseek_api

def handler(request):
    """处理笔记二创请求"""
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
        note_id = data.get('note_id')
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        
        if not title or not content:
            return create_response({
                'success': False,
                'error': '标题和内容不能为空'
            }, 400)
        
        # 获取用户配置
        user_config = db.get_user_config(user_id)
        
        # 调用DeepSeek API进行二创
        recreate_result = deepseek_api.recreate_note(title, content, user_config)
        
        if recreate_result['success']:
            recreated_data = recreate_result['data']
            
            # 保存二创历史（需要在数据库中添加相关方法）
            if note_id:
                try:
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    
                    if db.use_postgres:
                        cursor.execute('''
                            INSERT INTO recreate_history (user_id, note_id, original_title, 
                                                        original_content, recreated_title, recreated_content)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        ''', (user_id, note_id, title, content, 
                              recreated_data['new_title'], recreated_data['new_content']))
                    else:
                        cursor.execute('''
                            INSERT INTO recreate_history (user_id, note_id, original_title, 
                                                        original_content, recreated_title, recreated_content)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (user_id, note_id, title, content, 
                              recreated_data['new_title'], recreated_data['new_content']))
                    
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"保存二创历史失败: {e}")
            
            return create_response({
                'success': True,
                'message': '笔记二创成功',
                'data': {
                    'original_title': title,
                    'original_content': content,
                    'new_title': recreated_data['new_title'],
                    'new_content': recreated_data['new_content']
                }
            }, 200)
        else:
            return create_response({
                'success': False,
                'error': recreate_result.get('error', '二创失败')
            }, 400)
            
    except Exception as e:
        return create_response({
            'success': False,
            'error': f'处理二创请求失败: {str(e)}'
        }, 500)