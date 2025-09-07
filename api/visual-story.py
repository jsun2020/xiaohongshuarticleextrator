"""
Visual Story API - Vercel Serverless函数
处理视觉故事生成、历史记录等请求
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from _utils import parse_request, create_response, require_auth
from _database import db
from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
from urllib.parse import urlparse, parse_qs
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
    
    def do_POST(self):
        """处理POST请求"""
        try:
            print(f"[VISUAL_STORY DEBUG] POST request path: {self.path}")
            
            # 解析路径
            parsed_url = urlparse(self.path)
            path_parts = parsed_url.path.strip('/').split('/')
            
            if 'generate' in self.path or len(path_parts) >= 2 and path_parts[1] == 'generate':
                self.handle_generate()
            else:
                self.send_json_response({'success': False, 'error': 'Invalid endpoint'}, 404)
                
        except Exception as e:
            print(f"[VISUAL_STORY DEBUG] Error in do_POST: {str(e)}")
            self.send_json_response({'success': False, 'error': f'请求处理失败: {str(e)}'}, 500)
    
    def do_GET(self):
        """处理GET请求"""
        try:
            print(f"[VISUAL_STORY DEBUG] GET request path: {self.path}")
            
            if 'history' in self.path:
                self.handle_get_history()
            else:
                self.send_json_response({'success': False, 'error': 'Invalid endpoint'}, 404)
                
        except Exception as e:
            print(f"[VISUAL_STORY DEBUG] Error in do_GET: {str(e)}")
            self.send_json_response({'success': False, 'error': f'请求处理失败: {str(e)}'}, 500)
    
    def do_DELETE(self):
        """处理DELETE请求"""
        try:
            print(f"[VISUAL_STORY DEBUG] DELETE request path: {self.path}")
            
            if 'history' in self.path:
                self.handle_delete_history()
            else:
                self.send_json_response({'success': False, 'error': 'Invalid endpoint'}, 404)
                
        except Exception as e:
            print(f"[VISUAL_STORY DEBUG] Error in do_DELETE: {str(e)}")
            self.send_json_response({'success': False, 'error': f'请求处理失败: {str(e)}'}, 500)
    
    def handle_generate(self):
        """处理视觉故事生成请求"""
        try:
            print(f"[VISUAL_STORY DEBUG] Starting generate process...")
            
            # 检查认证
            cookies = {}
            cookie_header = self.headers.get('Cookie', '')
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookies[key] = value
            
            req_data = {
                'method': 'POST',
                'cookies': cookies,
                'headers': dict(self.headers)
            }
            
            user_id = require_auth(req_data)
            if not user_id:
                print(f"[VISUAL_STORY DEBUG] Authentication failed")
                self.send_json_response({'success': False, 'error': '请先登录'}, 401)
                return
            
            print(f"[VISUAL_STORY DEBUG] User authenticated: {user_id}")
            
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            print(f"[VISUAL_STORY DEBUG] Request data: {data}")
            
            # 验证必需字段
            required_fields = ['history_id', 'title', 'content']
            for field in required_fields:
                if field not in data:
                    self.send_json_response({
                        'success': False,
                        'error': f'缺少必需字段: {field}'
                    }, 400)
                    return
            
            history_id = data['history_id']
            title = data['title']
            content = data['content']
            model = data.get('model', 'gemini-2.0-flash-exp')
            
            print(f"[VISUAL_STORY DEBUG] Processing: history_id={history_id}, model={model}")
            
            # 初始化数据库
            db.init_database()
            
            # 验证历史记录是否存在且属于当前用户
            conn = db.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    SELECT id, user_id FROM recreate_history 
                    WHERE id = ? AND user_id = ?
                """, (history_id, user_id))
                
                history_record = cursor.fetchone()
                if not history_record:
                    self.send_json_response({
                        'success': False,
                        'error': '历史记录不存在或无权访问'
                    }, 404)
                    return
                
                print(f"[VISUAL_STORY DEBUG] History record found, generating visual story...")
                
                # 调用Gemini生成视觉故事
                try:
                    from gemini_visual_story import create_gemini_client
                    
                    print(f"[VISUAL_STORY DEBUG] Creating Gemini client...")
                    gemini_client = create_gemini_client()
                    
                    if not gemini_client:
                        print(f"[VISUAL_STORY DEBUG] Failed to create Gemini client")
                        self.send_json_response({
                            'success': False,
                            'error': 'Gemini服务初始化失败，请检查API密钥配置'
                        }, 500)
                        return
                    
                    # 生成提示词
                    prompt = f"""
根据以下标题和内容，生成一个视觉故事描述。请用中文回复，包含详细的视觉元素描述。

标题：{title}

内容：{content}

请生成一个包含以下元素的视觉故事：
1. 场景描述
2. 人物形象
3. 色彩搭配
4. 构图建议
5. 氛围营造

请以JSON格式返回，包含story_description字段。
"""
                    
                    print(f"[VISUAL_STORY DEBUG] Sending request to Gemini...")
                    
                    # 发送到Gemini
                    response = gemini_client.generate_content(prompt)
                    
                    if response and response.text:
                        story_result = response.text
                        print(f"[VISUAL_STORY DEBUG] Gemini response received: {len(story_result)} characters")
                        
                        # 保存到数据库
                        created_at = datetime.now().isoformat()
                        cursor.execute("""
                            INSERT INTO visual_story_history 
                            (history_id, user_id, title, content, html_content, model_used, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (history_id, user_id, title, content, story_result, model, created_at))
                        
                        story_id = cursor.lastrowid
                        conn.commit()
                        
                        print(f"[VISUAL_STORY DEBUG] Story saved to database with ID: {story_id}")
                        
                        self.send_json_response({
                            'success': True,
                            'message': '视觉故事生成成功',
                            'data': {
                                'story_id': story_id,
                                'html_content': story_result,
                                'model_used': model,
                                'created_at': created_at
                            }
                        }, 200)
                        return
                    else:
                        print(f"[VISUAL_STORY DEBUG] No response from Gemini")
                        self.send_json_response({
                            'success': False,
                            'error': 'Gemini服务无响应'
                        }, 500)
                        return
                        
                except ImportError as e:
                    print(f"[VISUAL_STORY DEBUG] Import error: {str(e)}")
                    self.send_json_response({
                        'success': False,
                        'error': 'Gemini服务模块导入失败'
                    }, 500)
                    return
                except Exception as e:
                    print(f"[VISUAL_STORY DEBUG] Gemini error: {str(e)}")
                    self.send_json_response({
                        'success': False,
                        'error': f'生成视觉故事失败: {str(e)}'
                    }, 500)
                    return
                    
            finally:
                conn.close()
                
        except Exception as e:
            print(f"[VISUAL_STORY DEBUG] Exception in handle_generate: {str(e)}")
            self.send_json_response({'success': False, 'error': f'生成失败: {str(e)}'}, 500)
    
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
            path_parts = self.path.strip('/').split('/')
            story_id = None
            for i, part in enumerate(path_parts):
                if part == 'history' and i + 1 < len(path_parts):
                    try:
                        story_id = int(path_parts[i + 1])
                        break
                    except (ValueError, IndexError):
                        pass
            
            if not story_id:
                self.send_json_response({'success': False, 'error': '无效的故事ID'}, 400)
                return
            
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