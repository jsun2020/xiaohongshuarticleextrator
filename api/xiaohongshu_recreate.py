"""
小红书笔记二创API - Vercel Serverless函数
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response, require_auth
from _database import db
from _deepseek_api import deepseek_api
import json

def handler(request):
    """Vercel serverless function handler"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cookie'
            }
        }
    
    if request.method == 'POST':
        """处理笔记二创请求"""
        # 初始化数据库
        db.init_database()
        print(f"[CRITICAL DEBUG] AI recreate - database path: {db.db_path}")
        print(f"[CRITICAL DEBUG] AI recreate - database exists: {os.path.exists(db.db_path)}")
        print(f"[CRITICAL DEBUG] AI recreate - current working dir: {os.getcwd()}")
        print(f"[CRITICAL DEBUG] AI recreate - temp dir: {os.environ.get('TMPDIR', 'not set')}")
        
        try:
            # 读取请求体
            if hasattr(request, 'json') and request.json:
                data = request.json
            elif hasattr(request, 'body'):
                if isinstance(request.body, (bytes, str)):
                    body_str = request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body
                    data = json.loads(body_str) if body_str else {}
                else:
                    data = request.body or {}
            else:
                data = {}
            
            # 解析Cookie进行认证
            cookies = {}
            cookie_header = request.headers.get('cookie', '') or request.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
            
            req_data = {
                'method': 'POST',
                'body': data,
                'cookies': cookies,
                'headers': dict(request.headers)
            }
            
            # 检查用户认证
            user_id = require_auth(req_data)
            if not user_id:
                return {
                    'statusCode': 401,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'success': False, 'error': '请先登录'})
                }
            
            note_id = data.get('note_id')
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            
            if not title or not content:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': '标题和内容不能为空'
                    })
                }
            
            # 获取用户配置
            user_config = db.get_user_config(user_id)
            
            # 调用DeepSeek API进行二创
            recreate_result = deepseek_api.recreate_note(title, content, user_config, user_id)
            
            if recreate_result['success']:
                recreated_data = recreate_result['data']
                
                # 保存二创历史
                if note_id:
                    print(f"[DB DEBUG] Saving recreate history for user {user_id}, note {note_id}")
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
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cookie'
                    },
                    'body': json.dumps({
                        'success': True,
                        'message': '笔记二创成功',
                        'data': {
                            'original_title': title,
                            'original_content': content,
                            'new_title': recreated_data['new_title'],
                            'new_content': recreated_data['new_content']
                        }
                    }, ensure_ascii=False)
                }
            else:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': recreate_result.get('error', '二创失败')
                    })
                }
                
        except Exception as e:
            print(f"Error in recreate API: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'处理二创请求失败: {str(e)}'
                })
            }
    
    return {
        'statusCode': 405,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': 'Method not allowed'})
    }