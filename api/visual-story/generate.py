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
import base64
import time

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
                    api_key = os.environ.get('MY_GEMINI_API_KEY')
                    if not api_key:
                        print(f"[VISUAL_STORY DEBUG] MY_GEMINI_API_KEY not found")
                        self.send_json_response({
                            'success': False,
                            'error': 'Gemini API密钥未配置，请检查环境变量MY_GEMINI_API_KEY'
                        }, 500)
                        return
                    
                    print(f"[VISUAL_STORY DEBUG] Using model: {model}")
                    
                    # 翻译中文内容为英文提示词
                    def translate_to_english_prompt(chinese_text, prompt_type="general"):
                        """将中文内容转换为适合图像生成的英文提示词"""
                        # 简单的关键词映射和翻译逻辑
                        translations = {
                            # 技术相关
                            "更新": "update", "升级": "upgrade", "版本": "version", "功能": "feature",
                            "工具": "tool", "软件": "software", "代码": "code", "编程": "programming",
                            "效率": "efficiency", "性能": "performance", "优化": "optimization",
                            "安全": "security", "界面": "interface", "体验": "experience",
                            "CLI": "CLI", "命令行": "command line", "终端": "terminal",
                            
                            # 视觉相关
                            "科技": "technology", "未来": "futuristic", "现代": "modern",
                            "炫酷": "cool", "专业": "professional", "简洁": "clean",
                            "创新": "innovative", "智能": "smart", "高级": "advanced"
                        }
                        
                        # 根据内容生成英文提示词
                        if "CLI" in chinese_text or "命令行" in chinese_text or "代码" in chinese_text:
                            if prompt_type == "cover":
                                return "Professional tech software update cover, modern CLI terminal interface, glowing code elements, futuristic blue and purple gradient, sleek design, 4K quality"
                            else:
                                return f"Technology illustration showing software development, command line interface, coding environment, modern UI design, tech innovation theme, scene {prompt_type}"
                        elif "更新" in chinese_text or "升级" in chinese_text:
                            if prompt_type == "cover":
                                return "Software update announcement cover, modern tech design, upgrade arrows, glowing interface elements, professional gradient background, clean typography space"
                            else:
                                return f"Software upgrade illustration, modern interface design, progress indicators, tech innovation, professional style, scene {prompt_type}"
                        elif "工具" in chinese_text or "效率" in chinese_text:
                            if prompt_type == "cover":
                                return "Productivity tool cover design, efficiency concept, modern workflow visualization, clean professional interface, tech productivity theme"
                            else:
                                return f"Productivity and efficiency illustration, workflow optimization, modern tools interface, professional design, scene {prompt_type}"
                        else:
                            # 通用科技主题
                            if prompt_type == "cover":
                                return "Modern technology cover design, innovative software interface, professional tech theme, clean design, futuristic elements"
                            else:
                                return f"Technology and innovation illustration, modern interface design, professional tech theme, clean style, scene {prompt_type}"
                    
                    print(f"[VISUAL_STORY DEBUG] Generating images with English prompts...")
                    
                    # 调用Gemini API
                    base_url = "https://api.tu-zi.com"
                    gemini_url = f"{base_url}/v1beta/models/{model}:generateContent"
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {api_key}'
                    }
                    
                    # 生成封面图片 (使用英文提示词)
                    cover_prompt = translate_to_english_prompt(title + " " + content, "cover")
                    payload = {
                        "contents": [{
                            "parts": [{
                                "text": cover_prompt
                            }]
                        }],
                        "generationConfig": {"maxOutputTokens": 7680, "temperature": 0.1}
                    }
                    
                    response = requests.post(gemini_url, headers=headers, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if 'candidates' in response_data and len(response_data['candidates']) > 0:
                            print(f"[VISUAL_STORY DEBUG] Processing Gemini response for cover image...")
                            
                            # Initialize structured story data
                            structured_story = {
                                'cover_card': {
                                    'title': title,
                                    'layout': 'c',
                                    'image_url': None
                                },
                                'content_cards': [],
                                'html': content
                            }
                            
                            # Process cover image
                            candidate = response_data['candidates'][0]
                            cover_image_url = None
                            
                            for part in candidate['content']['parts']:
                                if 'text' in part:
                                    print(f"[VISUAL_STORY DEBUG] Cover text response: {part['text'][:100]}...")
                                elif 'inlineData' in part:
                                    # Handle generated image
                                    print(f"[VISUAL_STORY DEBUG] Found generated cover image")
                                    image_data = part['inlineData']['data']
                                    mime_type = part['inlineData']['mimeType']
                                    cover_image_url = f"data:{mime_type};base64,{image_data}"
                                    break
                            
                            # Set cover image
                            if cover_image_url:
                                structured_story['cover_card']['image_url'] = cover_image_url
                                print(f"[VISUAL_STORY DEBUG] Cover image set successfully")
                            else:
                                # Fallback if no image generated
                                fallback_svg = f'''<svg width="600" height="800" xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" fill="#6366f1"/>
<text x="50%" y="50%" font-family="Arial,sans-serif" font-size="24" fill="#ffffff" text-anchor="middle" dy=".3em">{title[:20]}</text>
</svg>'''
                                structured_story['cover_card']['image_url'] = f"data:image/svg+xml;base64,{base64.b64encode(fallback_svg.encode()).decode()}"
                                print(f"[VISUAL_STORY DEBUG] Using fallback cover image")
                            
                            # Generate content images (使用英文提示词)
                            content_images = []
                            content_prompts = [
                                translate_to_english_prompt(title + " " + content, "1"),
                                translate_to_english_prompt(title + " " + content, "2"), 
                                translate_to_english_prompt(title + " " + content, "3")
                            ]
                            
                            print(f"[VISUAL_STORY DEBUG] Cover prompt: {cover_prompt}")
                            print(f"[VISUAL_STORY DEBUG] Content prompts: {content_prompts}")
                            
                            for i, prompt in enumerate(content_prompts):
                                print(f"[VISUAL_STORY DEBUG] Generating content image {i+1}...")
                                content_payload = {
                                    "contents": [{
                                        "parts": [{
                                            "text": prompt
                                        }]
                                    }],
                                    "generationConfig": {"maxOutputTokens": 7680, "temperature": 0.3}
                                }
                                
                                content_response = requests.post(gemini_url, headers=headers, json=content_payload, timeout=30)
                                
                                if content_response.status_code == 200:
                                    content_data = content_response.json()
                                    if 'candidates' in content_data and len(content_data['candidates']) > 0:
                                        content_candidate = content_data['candidates'][0]
                                        content_image_url = None
                                        
                                        for part in content_candidate['content']['parts']:
                                            if 'inlineData' in part:
                                                image_data = part['inlineData']['data']
                                                mime_type = part['inlineData']['mimeType']
                                                content_image_url = f"data:{mime_type};base64,{image_data}"
                                                break
                                        
                                        # Add content card
                                        layouts = ['a', 'b', 'c']
                                        if content_image_url:
                                            structured_story['content_cards'].append({
                                                'title': f'场景 {i+1}',
                                                'content': content[:100] + '...',
                                                'layout': layouts[i % 3],
                                                'image_url': content_image_url
                                            })
                                            print(f"[VISUAL_STORY DEBUG] Content image {i+1} generated successfully")
                                        else:
                                            # Fallback content image
                                            colors = ["8b5cf6", "06b6d4", "10b981"]
                                            fallback_svg = f'''<svg width="600" height="800" xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" fill="#{colors[i]}"/>
<text x="50%" y="50%" font-family="Arial,sans-serif" font-size="24" fill="#ffffff" text-anchor="middle" dy=".3em">场景 {i+1}</text>
</svg>'''
                                            structured_story['content_cards'].append({
                                                'title': f'场景 {i+1}',
                                                'content': content[:100] + '...',
                                                'layout': layouts[i % 3],
                                                'image_url': f"data:image/svg+xml;base64,{base64.b64encode(fallback_svg.encode()).decode()}"
                                            })
                                            print(f"[VISUAL_STORY DEBUG] Using fallback for content image {i+1}")
                                
                                # Add small delay between requests
                                time.sleep(0.5)
                            
                            print(f"[VISUAL_STORY DEBUG] Generated {len(structured_story['content_cards'])} content images")
                            
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