"""
DeepSeek配置API - Vercel Serverless函数
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _utils import parse_request, create_response, require_auth
from _database import db
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs

def mask_api_key(api_key):
    """掩码API Key显示"""
    if not api_key or len(api_key) < 8:
        return api_key
    return api_key[:8] + '*' * (len(api_key) - 12) + api_key[-4:]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """获取DeepSeek配置"""
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
                'method': 'GET',
                'body': {},
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            # 检查用户认证
            user_id = require_auth(req_data)
            if not user_id:
                self.send_error_response({'success': False, 'error': '请先登录'}, 401)
                return
            
            # 获取用户配置
            user_config = db.get_user_config(user_id)
            print(f"[DEBUG] GET config for user {user_id}: {list(user_config.keys()) if user_config else 'None'}")
            
            # 掩码显示API Key
            raw_api_key = user_config.get('deepseek_api_key', '')
            masked_api_key = mask_api_key(raw_api_key)
            print(f"[DEBUG] Raw API key: {'Yes' if raw_api_key else 'No'}")
            print(f"[DEBUG] Masked API key: {masked_api_key}")
            
            masked_config = {
                'api_key': masked_api_key,
                'base_url': user_config.get('deepseek_base_url', 'https://api.deepseek.com'),
                'model': user_config.get('deepseek_model', 'deepseek-chat'),
                'temperature': float(user_config.get('deepseek_temperature', '0.7')),
                'max_tokens': int(user_config.get('deepseek_max_tokens', '1000'))
            }
            
            self.send_json_response({
                'success': True,
                'config': masked_config
            }, 200)
            
        except Exception as e:
            print(f"Error in deepseek config GET: {e}")
            self.send_error_response({
                'success': False,
                'error': f'获取配置失败: {str(e)}'
            }, 500)
    
    def do_POST(self):
        """保存DeepSeek配置"""
        # 初始化数据库
        db.init_database()
        
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            # 解析Cookie进行认证
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
            
            req_data = {
                'method': 'POST',
                'body': data,
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            # 检查用户认证
            user_id = require_auth(req_data)
            if not user_id:
                self.send_error_response({'success': False, 'error': '请先登录'}, 401)
                return
            
            # 更新用户配置
            api_key = data.get('api_key', '').strip()
            base_url = data.get('base_url', 'https://api.deepseek.com').strip()
            model = data.get('model', 'deepseek-chat').strip()
            temperature = data.get('temperature', 0.7)
            max_tokens = data.get('max_tokens', 1000)
            
            print(f"[DEBUG] POST data received: api_key={'Yes' if api_key else 'No'}, base_url={base_url}")
            
            # 验证必填字段
            if not api_key:
                self.send_error_response({
                    'success': False,
                    'error': 'API Key不能为空'
                }, 400)
                return
            
            # 检查是否是掩码值，如果是则不更新
            current_config = db.get_user_config(user_id)
            current_api_key = current_config.get('deepseek_api_key', '')
            masked_key = mask_api_key(current_api_key)
            
            print(f"[DEBUG] Current API key: {'Yes' if current_api_key else 'No'}")
            print(f"[DEBUG] Masked key: {masked_key}")
            print(f"[DEBUG] Input key matches mask: {api_key == masked_key}")
            
            if api_key != masked_key:
                # 不是掩码值，更新API Key
                print(f"[DEBUG] Saving new API key...")
                result = db.set_user_config(user_id, 'deepseek_api_key', api_key)
                print(f"[DEBUG] Save result: {result}")
            else:
                print(f"[DEBUG] Skipping API key save (masked value)")
            
            # 更新其他配置
            db.set_user_config(user_id, 'deepseek_base_url', base_url)
            db.set_user_config(user_id, 'deepseek_model', model)
            db.set_user_config(user_id, 'deepseek_temperature', str(temperature))
            db.set_user_config(user_id, 'deepseek_max_tokens', str(max_tokens))
            
            self.send_json_response({
                'success': True,
                'message': 'DeepSeek配置保存成功'
            }, 200)
            
        except Exception as e:
            print(f"Error in deepseek config POST: {e}")
            self.send_error_response({
                'success': False,
                'error': f'保存配置失败: {str(e)}'
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