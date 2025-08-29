"""
健康检查API - Vercel Serverless函数
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response, require_auth
from _database import db
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
    
    if request.method == 'GET':
        # 初始化数据库
        db.init_database()
        
        try:
            # 解析Cookie进行认证
            cookies = {}
            cookie_header = request.headers.get('cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
            
            req_data = {
                'method': 'GET',
                'query': {},
                'cookies': cookies,
                'headers': dict(request.headers)
            }
            
            # 检查用户登录状态
            user_id = require_auth(req_data)
            logged_in = user_id is not None
            
            # 获取笔记总数
            total_notes = 0
            if user_id:
                try:
                    total_notes = db.get_notes_count(user_id)
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
                    'status': 'healthy',
                    'database_status': 'connected',
                    'total_notes': total_notes,
                    'deepseek_configured': deepseek_configured,
                    'logged_in': logged_in
                }, ensure_ascii=False)
            }
            
        except Exception as e:
            print(f"Health check error: {e}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, Cookie'
                },
                'body': json.dumps({
                    'success': False,
                    'status': 'error',
                    'error': str(e)
                }, ensure_ascii=False)
            }
    
    return {
        'statusCode': 405,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': 'Method not allowed'})
    }