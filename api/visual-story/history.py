"""
Visual Story History API - Vercel Serverless函数
处理视觉故事历史记录请求
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _utils import parse_request, create_response, require_auth
from _database import db
from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        try:
            print(f"[VISUAL_STORY DEBUG] GET request path: {self.path}")
            
            self.handle_get_history()
                
        except Exception as e:
            print(f"[VISUAL_STORY DEBUG] Error in do_GET: {str(e)}")
            self.send_json_response({'success': False, 'error': f'请求处理失败: {str(e)}'}, 500)
    
    
    def handle_get_history(self):
        """处理获取历史记录请求"""
        try:
            # 检查认证
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
            
            req_data = {
                'method': 'GET',
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            user_id = require_auth(req_data)
            if not user_id:
                self.send_json_response({'success': False, 'error': '请先登录'}, 401)
                return
            
            # 解析查询参数
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            limit = int(query_params.get('limit', [20])[0])
            offset = int(query_params.get('offset', [0])[0])
            
            # 初始化数据库
            db.init_database()
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    SELECT id, history_id, title, content, html_content, model_used, created_at
                    FROM visual_story_history 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))
                
                stories = cursor.fetchall()
                
                # 转换为字典格式
                result = []
                if stories:
                    columns = [description[0] for description in cursor.description]
                    for story in stories:
                        story_dict = dict(zip(columns, story))
                        result.append(story_dict)
                
                self.send_json_response({
                    'success': True,
                    'data': result,
                    'total': len(result)
                }, 200)
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"[VISUAL_STORY DEBUG] Exception in handle_get_history: {str(e)}")
            self.send_json_response({'success': False, 'error': f'获取历史记录失败: {str(e)}'}, 500)
    
    
    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))