"""
小红书笔记二创API + DeepSeek配置管理 - Vercel Serverless函数
支持:
- POST /api/xiaohongshu_recreate - AI笔记二创
- GET /api/xiaohongshu_recreate?action=config - 获取DeepSeek配置
- POST /api/xiaohongshu_recreate?action=config - 更新DeepSeek配置  
- POST /api/xiaohongshu_recreate?action=test - 测试DeepSeek连接
"""
from http.server import BaseHTTPRequestHandler
import sys
import os
import json
import urllib.parse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response, require_auth
from _database import db
from _deepseek_api import deepseek_api

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求 - DeepSeek配置获取"""
        try:
            # 解析查询参数
            query_params = {}
            if self.path and '?' in self.path:
                query_string = self.path.split('?', 1)[1]
                query_params = urllib.parse.parse_qs(query_string)
            
            action = query_params.get('action', [''])[0]
            
            if action == 'config':
                self.handle_get_config()
            else:
                # 默认返回错误
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'Invalid action parameter'
                }).encode('utf-8'))
                
        except Exception as e:
            print(f"[DeepSeek GET] Error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'处理请求失败: {str(e)}'
            }).encode('utf-8'))
    
    def do_POST(self):
        """处理POST请求 - 二创/配置更新/连接测试"""
        try:
            # 解析查询参数
            query_params = {}
            if self.path and '?' in self.path:
                query_string = self.path.split('?', 1)[1]
                query_params = urllib.parse.parse_qs(query_string)
            
            action = query_params.get('action', [''])[0]
            
            if action == 'config':
                self.handle_update_config()
            elif action == 'test':
                self.handle_test_connection()
            else:
                # 默认是二创功能
                self.handle_recreate_note()
                
        except Exception as e:
            print(f"[DeepSeek POST] Error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'处理请求失败: {str(e)}'
            }).encode('utf-8'))
    
    def handle_get_config(self):
        """处理获取DeepSeek配置"""
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
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False, 
                    'error': '请先登录'
                }).encode('utf-8'))
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
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
            self.end_headers()
            
            response_data = {
                'success': True,
                'data': {
                    'config': deepseek_config,
                    'usage': {
                        'ai_recreate_used': usage_count,
                        'ai_recreate_limit': 3
                    }
                }
            }
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            print(f"[DeepSeek Config GET] Error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'获取配置失败: {str(e)}'
            }).encode('utf-8'))
    
    def handle_update_config(self):
        """处理更新DeepSeek配置"""
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
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False, 
                    'error': '请先登录'
                }).encode('utf-8'))
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
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': 'DeepSeek配置更新成功'
                }).encode('utf-8'))
            else:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': '配置更新失败'
                }).encode('utf-8'))
                
        except Exception as e:
            print(f"[DeepSeek Config POST] Error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'更新配置失败: {str(e)}'
            }).encode('utf-8'))
    
    def handle_test_connection(self):
        """处理测试DeepSeek连接"""
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
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False, 
                    'error': '请先登录'
                }).encode('utf-8'))
                return
            
            # 初始化数据库
            db.init_database()
            
            # 获取用户配置
            user_config = db.get_user_config(user_id)
            
            print(f"[DeepSeek Test] Testing connection for user {user_id}")
            print(f"[DeepSeek Test] User config keys: {list(user_config.keys())}")
            
            # 调用DeepSeek API测试连接
            result = deepseek_api.test_connection(user_config)
            
            print(f"[DeepSeek Test] Test result: {result}")
            
            if result['success']:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': result['message']
                }).encode('utf-8'))
            else:
                self.send_response(200)  # Use 200 for business errors
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': result['error']
                }).encode('utf-8'))
                
        except Exception as e:
            print(f"[DeepSeek Test] Error: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'连接测试失败: {str(e)}'
            }).encode('utf-8'))
    
    def handle_recreate_note(self):
        """处理笔记二创请求"""
        try:
            # 初始化数据库
            db.init_database()
            
            # 调试信息 - 区分数据库类型
            if hasattr(db, 'db_path'):
                print(f"[CRITICAL DEBUG] AI recreate - SQLite database path: {db.db_path}")
                print(f"[CRITICAL DEBUG] AI recreate - database exists: {os.path.exists(db.db_path)}")
            else:
                print(f"[CRITICAL DEBUG] AI recreate - Using PostgreSQL database")
                print(f"[CRITICAL DEBUG] AI recreate - Database URL configured: {bool(db.db_url)}")
            
            print(f"[CRITICAL DEBUG] AI recreate - current working dir: {os.getcwd()}")
            print(f"[CRITICAL DEBUG] AI recreate - temp dir: {os.environ.get('TMPDIR', 'not set')}")
            
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
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False, 
                    'error': '请先登录'
                }).encode('utf-8'))
                return
            
            note_id = data.get('note_id')
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            
            if not title or not content:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': '标题和内容不能为空'
                }).encode('utf-8'))
                return
            
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
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
                self.end_headers()
                
                response_data = {
                    'success': True,
                    'message': '笔记二创成功',
                    'data': {
                        'original_title': title,
                        'original_content': content,
                        'new_title': recreated_data['new_title'],
                        'new_content': recreated_data['new_content']
                    }
                }
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': recreate_result.get('error', '二创失败')
                }).encode('utf-8'))
                
        except Exception as e:
            print(f"Error in recreate API: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'处理二创请求失败: {str(e)}'
            }).encode('utf-8'))