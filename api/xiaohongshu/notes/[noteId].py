"""
删除笔记API - Vercel Serverless函数
Dynamic route: /api/xiaohongshu/notes/{noteId}
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _utils import parse_request, create_response, require_auth
from _database import db
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse

class handler(BaseHTTPRequestHandler):
    def do_DELETE(self):
        """处理删除笔记请求"""
        # 初始化数据库
        db.init_database()
        
        try:
            # 解析Cookie进行认证
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
            
            # 检查用户认证
            user_id = require_auth(req_data)
            if not user_id:
                self.send_error_response({'success': False, 'error': '请先登录'}, 401)
                return
            
            # 从URL路径中提取noteId
            # 在Vercel中，动态路由参数通过环境变量传递
            import os
            note_id = os.environ.get('noteId')
            
            if not note_id:
                # 尝试从URL路径解析
                parsed_url = urlparse(self.path)
                path_parts = parsed_url.path.strip('/').split('/')
                if len(path_parts) >= 4 and path_parts[-1]:
                    note_id = path_parts[-1]
            
            if not note_id:
                self.send_error_response({'success': False, 'error': '缺少笔记ID'}, 400)
                return
            
            # 删除笔记
            conn = db.get_connection()
            cursor = conn.cursor()
            
            try:
                if db.use_postgres:
                    cursor.execute('DELETE FROM notes WHERE note_id = %s AND user_id = %s', (note_id, user_id))
                else:
                    cursor.execute('DELETE FROM notes WHERE note_id = ? AND user_id = ?', (note_id, user_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.send_json_response({
                        'success': True,
                        'message': f'笔记 {note_id} 删除成功'
                    }, 200)
                else:
                    self.send_error_response({
                        'success': False,
                        'error': '笔记不存在或无权限删除'
                    }, 404)
                    
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Error in delete API: {e}")
            self.send_error_response({
                'success': False,
                'error': f'删除笔记失败: {str(e)}'
            }, 500)
    
    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, data, status_code):
        """发送错误响应"""
        self.send_json_response(data, status_code)
    
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()