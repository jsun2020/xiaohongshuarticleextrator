"""
Gemini API integration for visual story generation
Based on the AI Visual Story system prompt requirements
"""
import google.generativeai as genai
import json
import re
import base64
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import os


class GeminiVisualStoryGenerator:
    """Gemini API client for visual story generation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
    def test_connection(self) -> Dict:
        """Test Gemini API connection"""
        try:
            response = self.model.generate_content("Hello, test connection")
            if response.text:
                return {
                    'success': True,
                    'message': 'Gemini API连接成功'
                }
            else:
                return {
                    'success': False,
                    'error': 'Gemini API响应为空'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Gemini API连接失败: {str(e)}'
            }
    
    async def generate_visual_story(self, title: str, content: str) -> Dict:
        """
        Generate visual story from title and content
        Returns: {
            'success': bool,
            'data': {
                'cover_card': dict,
                'content_cards': list,
                'html': str
            },
            'error': str (if failed)
        }
        """
        try:
            # Step 1: Analyze content and generate card structure
            analysis_result = await self._analyze_content(title, content)
            if not analysis_result['success']:
                return analysis_result
            
            cards_data = analysis_result['data']
            
            # Step 2: Generate images for all cards
            image_generation_result = await self._generate_card_images(cards_data)
            if not image_generation_result['success']:
                return image_generation_result
            
            cards_with_images = image_generation_result['data']
            
            # Step 3: Build HTML
            html_result = self._build_html(cards_with_images)
            
            return {
                'success': True,
                'data': {
                    'cover_card': cards_with_images['cover'],
                    'content_cards': cards_with_images['content_cards'],
                    'html': html_result
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'生成视觉故事失败: {str(e)}'
            }
    
    async def _analyze_content(self, title: str, content: str) -> Dict:
        """Analyze content and extract key concepts for cards"""
        system_prompt = """
你是一位顶级的AI视觉叙事专家。你需要将给定的标题和内容转化为视觉故事卡片结构。

请严格按照以下步骤执行：

1. 封面卡片生成：
   - 提炼一个核心总标题（最能概括全文精髓）
   - 构思全局逻辑图的视觉prompt（用于生成思维导图风格的插图）

2. 内容卡片生成：
   - 从文章中提取3-9个核心概念或逻辑段落
   - 为每个概念创作：
     * 核心标题（20字以内，引人注目）
     * 核心阐述（金句式提炼，100字以内，精炼有力）
     * 插图prompt（具体的视觉隐喻描述）
     * 布局类型（a/b/c中选择，必须多样化）

3. 布局规则：
   - a: 图上文下（经典布局）
   - b: 文上图下（倒置布局）  
   - c: 图底文上（覆盖布局）
   - 必须使用至少2种不同布局
   - 相邻卡片避免使用相同布局

请以JSON格式返回结果，格式如下：
{
  "cover": {
    "title": "总标题",
    "image_prompt": "全局逻辑图prompt",
    "layout": "c"
  },
  "content_cards": [
    {
      "title": "核心标题",
      "content": "核心阐述",
      "image_prompt": "插图prompt",
      "layout": "a/b/c"
    }
  ]
}

插图prompt要求：
- 必须包含：主题、动作/关系、环境背景
- 风格要求：modern stylized illustration, clean composition, minimalist
- 严禁边框、圆角，必须满幅呈现
- 当涉及流程或关系时，明确要求生成flowchart、mind map或diagram
"""

        try:
            user_message = f"标题：{title}\n\n内容：{content}"
            
            response = self.model.generate_content([
                {"role": "system", "parts": [{"text": system_prompt}]},
                {"role": "user", "parts": [{"text": user_message}]}
            ])
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Extract JSON from response (handle potential markdown formatting)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find JSON without markdown formatting
                json_text = response_text
            
            cards_data = json.loads(json_text)
            
            # Validate structure
            if not self._validate_cards_structure(cards_data):
                return {
                    'success': False,
                    'error': '生成的卡片结构不符合要求'
                }
            
            return {
                'success': True,
                'data': cards_data
            }
            
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'解析AI响应失败: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'内容分析失败: {str(e)}'
            }
    
    def _validate_cards_structure(self, cards_data: Dict) -> bool:
        """Validate the structure of generated cards"""
        try:
            # Check cover card
            if 'cover' not in cards_data:
                return False
            
            cover = cards_data['cover']
            if not all(k in cover for k in ['title', 'image_prompt', 'layout']):
                return False
            
            # Check content cards
            if 'content_cards' not in cards_data:
                return False
            
            content_cards = cards_data['content_cards']
            if not isinstance(content_cards, list) or len(content_cards) < 3 or len(content_cards) > 9:
                return False
            
            # Check layout diversity
            layouts = [card.get('layout') for card in content_cards]
            if len(set(layouts)) < 2:
                return False
            
            # Check each content card
            for card in content_cards:
                if not all(k in card for k in ['title', 'content', 'image_prompt', 'layout']):
                    return False
                if card['layout'] not in ['a', 'b', 'c']:
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def _generate_card_images(self, cards_data: Dict) -> Dict:
        """Generate images for all cards using Gemini image generation"""
        try:
            # Generate cover image
            cover_image_url = await self._generate_single_image(cards_data['cover']['image_prompt'])
            if not cover_image_url:
                return {
                    'success': False,
                    'error': '封面图片生成失败'
                }
            
            cards_data['cover']['image_url'] = cover_image_url
            
            # Generate content card images
            for i, card in enumerate(cards_data['content_cards']):
                image_url = await self._generate_single_image(card['image_prompt'])
                if not image_url:
                    return {
                        'success': False,
                        'error': f'第{i+1}张内容卡片图片生成失败'
                    }
                card['image_url'] = image_url
            
            return {
                'success': True,
                'data': cards_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'图片生成失败: {str(e)}'
            }
    
    async def _generate_single_image(self, prompt: str) -> Optional[str]:
        """Generate a single image using Gemini"""
        try:
            # Note: This is a placeholder for actual Gemini image generation
            # The actual implementation would depend on Gemini's image generation API
            # For now, we'll return a placeholder or use the text-to-image model
            
            # Enhance prompt with style requirements
            enhanced_prompt = f"{prompt}. Modern stylized illustration, clean composition, minimalist, no borders, no frames, full-bleed, sharp 90-degree corners."
            
            # TODO: Implement actual Gemini image generation
            # For now, return a placeholder URL
            # In production, this would call Gemini's image generation API
            
            # Placeholder implementation - would be replaced with actual API call
            return "https://via.placeholder.com/600x800/f0f0f0/333?text=Generated+Image"
            
        except Exception as e:
            print(f"Image generation failed: {e}")
            return None
    
    def _build_html(self, cards_data: Dict) -> str:
        """Build complete HTML with all cards and download functionality"""
        cover_card = cards_data['cover']
        content_cards = cards_data['content_cards']
        
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Story</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.0/FileSaver.min.js"></script>
    <style>
        body {{
            margin: 0;
            background-color: #f0f0f0;
            font-family: 'Inter', 'Noto Sans SC', sans-serif;
        }}
        .download-container {{
            text-align: center;
            padding: 20px;
            background-color: #e9ecef;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        #download-all-btn {{
            padding: 12px 25px;
            font-size: 16px;
            font-weight: bold;
            color: #fff;
            background-color: #007bff;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }}
        #download-all-btn:hover {{ background-color: #0056b3; }}
        #download-all-btn:disabled {{ background-color: #6c757d; cursor: not-allowed; }}
        #download-status {{ color: #495057; font-size: 14px; margin-top: 10px; height: 20px; }}
        
        .card-stream {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 40px;
            padding: 40px 20px;
            padding-top: 20px;
        }}
        
        .card {{
            width: 100%;
            max-width: 600px;
            aspect-ratio: 3 / 4;
            background-color: #FFFFFF;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            color: #111;
        }}
        
        .illustration-area {{
            flex-grow: 1;
            background-size: cover;
            background-position: center;
        }}
        
        .info-area {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 40px;
            box-sizing: border-box;
        }}
        
        .info-area h1 {{
            font-size: 34px;
            font-weight: bold;
            margin: 0 0 15px 0;
            line-height: 1.3;
        }}
        
        .info-area p {{
            font-size: 21px;
            color: #555;
            line-height: 1.6;
            margin: 0;
        }}
        
        /* Layout A (default): 图上文下 */
        .card.layout-a {{
            flex-direction: column;
            text-align: left;
        }}
        .card.layout-a .info-area {{
            flex-grow: 0;
            flex-shrink: 0;
            height: auto;
        }}
        
        /* Layout B: 文上图下 */
        .card.layout-b {{
            flex-direction: column-reverse;
            text-align: left;
        }}
        .card.layout-b .info-area {{
            flex-grow: 0;
            flex-shrink: 0;
            height: auto;
        }}
        
        /* Layout C: 图底文上 */
        .card.layout-c {{
            position: relative;
            color: #FFFFFF;
            text-align: center;
            justify-content: flex-end;
        }}
        .card.layout-c .illustration-area {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
        }}
        .card.layout-c .info-area {{
            position: relative;
            z-index: 2;
            background: linear-gradient(to top, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 100%);
            width: 100%;
        }}
        .card.layout-c .info-area p {{
            color: #f0f0f0;
        }}
    </style>
</head>
<body>
    <div class="download-container">
        <button id="download-all-btn">下载全部卡片 (Zip)</button>
        <p id="download-status"></p>
    </div>
    
    <div class="card-stream">
        {self._generate_card_html(cover_card, is_cover=True)}
        {self._generate_content_cards_html(content_cards)}
    </div>
    
    <script>
        const downloadBtn = document.getElementById('download-all-btn');
        const statusEl = document.getElementById('download-status');
        const cards = document.querySelectorAll('.card');
        
        downloadBtn.addEventListener('click', async () => {{
            if (!cards || cards.length === 0) {{
                statusEl.textContent = '页面上没有可供下载的卡片。';
                return;
            }}
            
            downloadBtn.disabled = true;
            statusEl.textContent = '正在转换卡片... (0%)';
            
            const zip = new JSZip();
            let convertedCount = 0;
            
            try {{
                for (const [i, card] of cards.entries()) {{
                    const canvas = await html2canvas(card, {{
                        useCORS: true,
                        allowTaint: true,
                        scale: 2
                    }});
                    
                    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
                    zip.file(`card-${{i + 1}}.png`, blob);
                    
                    convertedCount++;
                    const progress = Math.round((convertedCount / cards.length) * 100);
                    statusEl.textContent = `正在转换卡片... (${{progress}}%)`;
                }}
                
                statusEl.textContent = '正在生成压缩包...';
                const content = await zip.generateAsync({{ type: 'blob' }});
                
                saveAs(content, 'visual-story-cards.zip');
                statusEl.textContent = '下载完成！';
                
            }} catch (error) {{
                console.error("下载失败:", error);
                statusEl.textContent = `下载出错: ${{error.message}}。请检查控制台。`;
            }} finally {{
                downloadBtn.disabled = false;
            }}
        }});
    </script>
</body>
</html>"""
        
        return html_template
    
    def _generate_card_html(self, card_data: Dict, is_cover: bool = False) -> str:
        """Generate HTML for a single card"""
        layout = card_data.get('layout', 'c' if is_cover else 'a')
        image_url = card_data.get('image_url', '')
        title = card_data.get('title', '')
        content = card_data.get('content', '') if not is_cover else ''
        
        return f"""
        <div class="card layout-{layout}">
            <div class="illustration-area" style="background-image: url('{image_url}');"></div>
            <div class="info-area">
                <h1>{title}</h1>
                {f'<p>{content}</p>' if content else ''}
            </div>
        </div>
        """
    
    def _generate_content_cards_html(self, cards: List[Dict]) -> str:
        """Generate HTML for all content cards"""
        return '\n'.join([self._generate_card_html(card) for card in cards])


def create_gemini_client(api_key: str = None) -> GeminiVisualStoryGenerator:
    """Create a Gemini client instance"""
    if not api_key:
        # Read from environment variable
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
    return GeminiVisualStoryGenerator(api_key)


# Test function
if __name__ == "__main__":
    import asyncio
    
    # Test with dummy API key
    test_api_key = "test_key"
    client = create_gemini_client(test_api_key)
    
    # Test connection
    result = client.test_connection()
    print("Connection test:", result)