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
                # Check database type
                use_postgres = getattr(db, 'use_postgres', False)
                
                if use_postgres:
                    cursor.execute("""
                        SELECT id, user_id FROM recreate_history 
                        WHERE id = %s AND user_id = %s
                    """, (history_id, user_id))
                else:
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
                            
                            # Parse and structure the visual story response
                            try:
                                import re
                                
                                # Try to parse JSON if it's in the response
                                json_match = re.search(r'\{.*\}', story_result, re.DOTALL)
                                structured_story = None
                                
                                if json_match:
                                    try:
                                        parsed_json = json.loads(json_match.group())
                                        print(f"[VISUAL_STORY DEBUG] Parsed JSON structure: {parsed_json}")
                                        
                                        # Create structured visual story data
                                        def create_svg_placeholder(text, bg_color="6366f1", text_color="ffffff", width=600, height=800):
                                            """Generate SVG data URI for placeholder image"""
                                            svg_text = text[:20].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                                            svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" fill="#{bg_color}"/>
<text x="50%" y="50%" font-family="Arial,sans-serif" font-size="24" fill="#{text_color}" text-anchor="middle" dy=".3em">{svg_text}</text>
</svg>'''
                                            import base64
                                            return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"
                                        
                                        structured_story = {
                                            'cover_card': {
                                                'title': title,
                                                'layout': 'c',
                                                'image_url': create_svg_placeholder(title, "6366f1", "ffffff")
                                            },
                                            'content_cards': [],
                                            'html': story_result
                                        }
                                        
                                        # Process story elements
                                        if 'story_description' in parsed_json:
                                            for i, element in enumerate(parsed_json['story_description'][:8]):  # Max 8 cards
                                                if isinstance(element, dict):
                                                    element_title = element.get('element', f'场景 {i+1}')
                                                    element_desc = element.get('description', '')[:100] + '...'
                                                    
                                                    # Generate SVG placeholder with description
                                                    layouts = ['a', 'b', 'c']
                                                    colors = ["8b5cf6", "06b6d4", "10b981", "f59e0b", "ef4444", "ec4899"]
                                                    
                                                    structured_story['content_cards'].append({
                                                        'title': element_title,
                                                        'content': element_desc,
                                                        'layout': layouts[i % 3],
                                                        'image_url': create_svg_placeholder(element_title, colors[i % len(colors)], "ffffff")
                                                    })
                                    except json.JSONDecodeError:
                                        print(f"[VISUAL_STORY DEBUG] Failed to parse JSON, using fallback")
                                
                                # If no structured data, create basic fallback
                                if not structured_story:
                                    def create_svg_placeholder_fallback(text, bg_color="6366f1", text_color="ffffff", width=600, height=800):
                                        """Generate SVG data URI for placeholder image"""
                                        svg_text = text[:20].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                                        svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" fill="#{bg_color}"/>
<text x="50%" y="50%" font-family="Arial,sans-serif" font-size="24" fill="#{text_color}" text-anchor="middle" dy=".3em">{svg_text}</text>
</svg>'''
                                        import base64
                                        return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"
                                    
                                    structured_story = {
                                        'cover_card': {
                                            'title': title,
                                            'layout': 'c',
                                            'image_url': create_svg_placeholder_fallback(title, "6366f1", "ffffff")
                                        },
                                        'content_cards': [{
                                            'title': '生成的视觉故事',
                                            'content': story_result[:200] + '...' if len(story_result) > 200 else story_result,
                                            'layout': 'a',
                                            'image_url': create_svg_placeholder_fallback('Visual Story', "8b5cf6", "ffffff")
                                        }],
                                        'html': story_result
                                    }
                                
                                # 保存到数据库 (save structured data as JSON)
                                created_at = datetime.now().isoformat()
                                story_data_json = json.dumps(structured_story, ensure_ascii=False)
                                
                                if use_postgres:
                                    cursor.execute("""
                                        INSERT INTO visual_story_history 
                                        (history_id, user_id, title, content, html_content, model_used, created_at)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                                    """, (history_id, user_id, title, content, story_data_json, model, created_at))
                                else:
                                    cursor.execute("""
                                        INSERT INTO visual_story_history 
                                        (history_id, user_id, title, content, html_content, model_used, created_at)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)
                                    """, (history_id, user_id, title, content, story_data_json, model, created_at))
                                
                                story_id = cursor.lastrowid
                                conn.commit()
                                
                                print(f"[VISUAL_STORY DEBUG] Story saved to database with ID: {story_id}")
                                
                                self.send_json_response({
                                    'success': True,
                                    'message': '视觉故事生成成功',
                                    'data': {
                                        'story_id': story_id,
                                        'visual_story': structured_story,
                                        'model_used': model,
                                        'created_at': created_at
                                    }
                                }, 200)
                                return
                                
                            except Exception as parse_error:
                                print(f"[VISUAL_STORY DEBUG] Parsing error: {str(parse_error)}")
                                # Fallback to original behavior
                                pass
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