"""
删除二创历史记录API - Vercel Serverless函数
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from _utils import parse_request, create_response, require_auth
from _database import db
import json

def handler(request):
    """Vercel serverless function handler for deleting recreate history"""
    
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
    
    if request.method == 'DELETE':
        """处理删除二创历史记录请求"""
        # 初始化数据库
        db.init_database()
        
        try:
            # Extract history_id from the URL path
            # For Vercel API routes, the dynamic parameter is available in request.query
            history_id = None
            if hasattr(request, 'query') and 'historyId' in request.query:
                history_id = request.query['historyId']
            elif hasattr(request, 'url'):
                # Parse from URL path
                import urllib.parse
                parsed_url = urllib.parse.urlparse(request.url)
                path_parts = parsed_url.path.split('/')
                if len(path_parts) >= 6 and path_parts[-2] == 'history':
                    history_id = path_parts[-1]
            
            if not history_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'success': False, 'error': '缺少历史记录ID'})
                }
            
            # Convert to integer
            try:
                history_id = int(history_id)
            except ValueError:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'success': False, 'error': '历史记录ID格式错误'})
                }
            
            # 解析Cookie和Authorization header进行认证
            cookies = {}
            cookie_header = request.headers.get('cookie', '') or request.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
            
            req_data = {
                'method': 'DELETE',
                'body': {},
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
            
            # 删除二创历史记录
            success = db.delete_recreate_history(user_id, history_id)
            
            if success:
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
                        'message': f'历史记录 {history_id} 删除成功'
                    }, ensure_ascii=False)
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': '历史记录不存在或删除失败'
                    })
                }
                
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': f'删除历史记录失败: {str(e)}'
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