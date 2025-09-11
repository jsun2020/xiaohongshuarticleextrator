"""
获取小红书笔记API - Vercel Serverless函数
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _utils import parse_request, create_response, require_auth
from _database import db
from _xhs_crawler import get_xiaohongshu_note
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
        """处理获取小红书笔记请求"""
        # 初始化数据库
        db.init_database()
        
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
            
            # 解析Cookie和Authorization header进行认证
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
            
            url = data.get('url', '').strip()
            if not url:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'success': False, 'error': '请提供小红书链接'})
                }
            
            # 调用爬虫获取笔记信息
            result = get_xiaohongshu_note(url)
            
            if result.get('success'):
                note_data = result['data']
                
                # 保存到数据库
                print(f"[API] Attempting to save note: {note_data.get('note_id')}")
                save_success = db.save_note(note_data, user_id)
                print(f"[API] Save result: {save_success}")
                
                if save_success:
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
                            'message': '笔记获取并保存成功',
                            'data': note_data,
                            'saved_to_db': True
                        }, ensure_ascii=False)
                    }
                else:
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
                            'message': '笔记获取成功，但保存失败',
                            'data': note_data,
                            'saved_to_db': False
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
                        'error': result.get('error', '获取笔记失败')
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
                    'error': f'处理请求失败: {str(e)}'
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