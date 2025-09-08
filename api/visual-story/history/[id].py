"""
Visual Story History Dynamic API - Vercel Serverless函数
处理特定视觉故事历史记录的删除请求
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _utils import parse_request, create_response, require_auth
from _database import db
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_DELETE(self):
        """处理DELETE请求"""
        try:
            print(f"[VISUAL_STORY DEBUG] DELETE request path: {self.path}")
            
            self.handle_delete_history()
                
        except Exception as e:
            print(f"[VISUAL_STORY DEBUG] Error in do_DELETE: {str(e)}")
            self.send_json_response({'success': False, 'error': f'请求处理失败: {str(e)}'}, 500)
    
    def handle_delete_history(self):
        """处理删除历史记录请求"""
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
                'method': 'DELETE',
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            user_id = require_auth(req_data)
            if not user_id:
                self.send_json_response({'success': False, 'error': '请先登录'}, 401)
                return
            
            # 从路径中提取story_id
            # 路径格式: /api/visual-story/history/123
            path_parts = self.path.strip('/').split('/')
            story_id = None
            
            # 查找数字ID（最后一个路径段）
            if path_parts:
                try:
                    story_id = int(path_parts[-1])
                except (ValueError, IndexError):
                    pass
            
            # 如果无法从路径获取，尝试从查询参数获取
            if not story_id:
                from urllib.parse import urlparse, parse_qs
                parsed_url = urlparse(self.path)
                query_params = parse_qs(parsed_url.query)
                if 'id' in query_params:
                    try:
                        story_id = int(query_params['id'][0])
                    except (ValueError, IndexError):
                        pass
            
            if not story_id:
                self.send_json_response({'success': False, 'error': '无效的故事ID'}, 400)
                return
            
            print(f"[VISUAL_STORY DEBUG] Deleting story ID: {story_id} for user: {user_id}")
            
            # 初始化数据库
            db.init_database()
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            try:
                # 验证记录是否存在且属于当前用户
                cursor.execute("""
                    SELECT id FROM visual_story_history 
                    WHERE id = ? AND user_id = ?
                """, (story_id, user_id))
                
                if not cursor.fetchone():
                    self.send_json_response({'success': False, 'error': '记录不存在或无权删除'}, 404)
                    return
                
                # 删除记录
                cursor.execute("""
                    DELETE FROM visual_story_history 
                    WHERE id = ? AND user_id = ?
                """, (story_id, user_id))
                
                conn.commit()
                
                print(f"[VISUAL_STORY DEBUG] Successfully deleted story ID: {story_id}")
                
                self.send_json_response({
                    'success': True,
                    'message': '删除成功'
                }, 200)
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"[VISUAL_STORY DEBUG] Exception in handle_delete_history: {str(e)}")
            self.send_json_response({'success': False, 'error': f'删除失败: {str(e)}'}, 500)
    
    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))