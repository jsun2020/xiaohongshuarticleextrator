"""
Visual Story Generate API - Vercel Serverless函数
处理视觉故事生成请求，使用HTTP请求调用Gemini API
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _utils import parse_request, create_response, require_auth
from _database import db
from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime
import requests

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
            
            self.handle_generate()
                
        except Exception as e:
            print(f"[VISUAL_STORY DEBUG] Error in do_POST: {str(e)}")
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
            model = data.get('model', 'gemini-2.5-flash-image-preview')
            
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
                
                # 调用Gemini API生成视觉故事
                try:
                    print(f"[VISUAL_STORY DEBUG] Preparing Gemini API call...")
                    
                    # 获取API密钥
                    api_key = os.environ.get('GEMINI_API_KEY')
                    if not api_key:
                        print(f"[VISUAL_STORY DEBUG] GEMINI_API_KEY not found")
                        self.send_json_response({
                            'success': False,
                            'error': 'Gemini API密钥未配置，请检查环境变量GEMINI_API_KEY'
                        }, 500)
                        return
                    
                    print(f"[VISUAL_STORY DEBUG] Using model: {model}")
                    
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
                    
                    print(f"[VISUAL_STORY DEBUG] Sending request to Gemini API...")
                    
                    # 调用Gemini API
                    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                    headers = {
                        'Content-Type': 'application/json',
                        'x-goog-api-key': api_key
                    }
                    
                    payload = {
                        "contents": [{
                            "parts": [{
                                "text": prompt
                            }]
                        }]
                    }
                    
                    response = requests.post(gemini_url, headers=headers, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if 'candidates' in response_data and len(response_data['candidates']) > 0:
                            story_result = response_data['candidates'][0]['content']['parts'][0]['text']
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
                            print(f"[VISUAL_STORY DEBUG] No candidates in Gemini response")
                            self.send_json_response({
                                'success': False,
                                'error': 'Gemini API返回了空响应'
                            }, 500)
                            return
                    else:
                        print(f"[VISUAL_STORY DEBUG] Gemini API error: {response.status_code} - {response.text}")
                        self.send_json_response({
                            'success': False,
                            'error': f'Gemini API调用失败: {response.status_code}'
                        }, 500)
                        return
                        
                except requests.exceptions.RequestException as e:
                    print(f"[VISUAL_STORY DEBUG] Request error: {str(e)}")
                    self.send_json_response({
                        'success': False,
                        'error': f'网络请求失败: {str(e)}'
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
    
    def send_json_response(self, data, status_code):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Cookie')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))