"""
删除二创历史API - Vercel Serverless函数
Dynamic route: /api/xiaohongshu/recreate/history/{historyId}
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from _utils import parse_request, create_response, require_auth
from _database import db
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse

class handler(BaseHTTPRequestHandler):
    def do_DELETE(self):
        """处理删除二创历史请求"""
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
            
            # 从URL路径中提取historyId
            # 在Vercel中，动态路由参数通过环境变量传递
            import os
            history_id = os.environ.get('historyId')
            
            if not history_id:
                # 尝试从URL路径解析
                parsed_url = urlparse(self.path)
                path_parts = parsed_url.path.strip('/').split('/')
                if len(path_parts) >= 5 and path_parts[-1]:
                    history_id = path_parts[-1]
            
            if not history_id:
                self.send_error_response({'success': False, 'error': '缺少历史记录ID'}, 400)
                return
            
            try:
                history_id = int(history_id)
            except ValueError:
                self.send_error_response({'success': False, 'error': '无效的历史记录ID'}, 400)
                return
            
            # 删除二创历史
            conn = db.get_connection()
            cursor = conn.cursor()
            
            try:
                if db.use_postgres:
                    cursor.execute('DELETE FROM recreate_history WHERE id = %s AND user_id = %s', (history_id, user_id))
                else:
                    cursor.execute('DELETE FROM recreate_history WHERE id = ? AND user_id = ?', (history_id, user_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    self.send_json_response({
                        'success': True,
                        'message': f'二创历史 {history_id} 删除成功'
                    }, 200)
                else:
                    self.send_error_response({
                        'success': False,
                        'error': '历史记录不存在或无权限删除'
                    }, 404)
                    
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Error in delete recreate history API: {e}")
            self.send_error_response({
                'success': False,
                'error': f'删除二创历史失败: {str(e)}'
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