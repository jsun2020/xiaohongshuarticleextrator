"""
DeepSeek配置API - Vercel Serverless函数
"""
from http.server import BaseHTTPRequestHandler
import sys
import os
import json
import urllib.parse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response, require_auth
from _database import db

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_GET(self):
        """获取DeepSeek配置"""
        try:
            # 解析Cookie进行认证
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = urllib.parse.unquote(value)
            
            req_data = {
                'method': 'GET',
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            # 检查用户认证
            user_id = require_auth(req_data)
            if not user_id:
                self.send_json_response({
                    'success': False, 
                    'error': '请先登录'
                }, 401)
                return
            
            # 初始化数据库
            db.init_database()
            
            # 获取用户配置
            config = db.get_user_config(user_id)
            
            # 返回DeepSeek相关配置
            deepseek_config = {
                'deepseek_api_key': config.get('deepseek_api_key', ''),
                'deepseek_base_url': config.get('deepseek_base_url', 'https://api.deepseek.com'),
                'deepseek_model': config.get('deepseek_model', 'deepseek-chat'),
                'deepseek_max_tokens': config.get('deepseek_max_tokens', '1000'),
                'deepseek_temperature': config.get('deepseek_temperature', '0.7')
            }
            
            # 获取用户AI二创使用次数
            usage_count = db.get_user_usage(user_id, 'ai_recreate')
            
            self.send_json_response({
                'success': True,
                'data': {
                    'config': deepseek_config,
                    'usage': {
                        'ai_recreate_used': usage_count,
                        'ai_recreate_limit': 3
                    }
                }
            }, 200)
            
        except Exception as e:
            print(f"[DeepSeek Config] Error in GET: {str(e)}")
            self.send_json_response({
                'success': False,
                'error': f'获取配置失败: {str(e)}'
            }, 500)
    
    def do_POST(self):
        """更新DeepSeek配置"""
        try:
            # 获取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                try:
                    data = json.loads(body.decode('utf-8'))
                except json.JSONDecodeError:
                    data = {}
            else:
                data = {}
            
            # 解析Cookie进行认证
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = urllib.parse.unquote(value)
            
            req_data = {
                'method': 'POST',
                'body': data,
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            # 检查用户认证
            user_id = require_auth(req_data)
            if not user_id:
                self.send_json_response({
                    'success': False, 
                    'error': '请先登录'
                }, 401)
                return
            
            # 初始化数据库
            db.init_database()
            
            # 获取要更新的配置
            config_updates = {}
            
            # 提取DeepSeek相关配置
            if 'deepseek_api_key' in data:
                config_updates['deepseek_api_key'] = data['deepseek_api_key']
            if 'deepseek_base_url' in data:
                config_updates['deepseek_base_url'] = data['deepseek_base_url']
            if 'deepseek_model' in data:
                config_updates['deepseek_model'] = data['deepseek_model']
            if 'deepseek_max_tokens' in data:
                config_updates['deepseek_max_tokens'] = str(data['deepseek_max_tokens'])
            if 'deepseek_temperature' in data:
                config_updates['deepseek_temperature'] = str(data['deepseek_temperature'])
            
            # 更新配置
            success = db.update_user_config(user_id, config_updates)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'message': 'DeepSeek配置更新成功'
                }, 200)
            else:
                self.send_json_response({
                    'success': False,
                    'error': '配置更新失败'
                }, 500)
                
        except Exception as e:
            print(f"[DeepSeek Config] Error in POST: {str(e)}")
            self.send_json_response({
                'success': False,
                'error': f'更新配置失败: {str(e)}'
            }, 500)
    
    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))