"""
DeepSeek API 集成模块 - Vercel兼容版本
用于笔记二创功能
"""

import json
import requests
import os
from typing import Dict, Any, Optional

class DeepSeekAPI:
    """DeepSeek API 客户端"""
    
    def __init__(self):
        # 不在初始化时缓存配置，每次使用时动态获取
        pass
    
    def _get_current_config(self, user_config=None, use_system_key=False):
        """获取当前配置"""
        if use_system_key:
            # 使用系统配置的API Key
            system_api_key = os.getenv('DEEPSEEK_API_KEY', '')
            return {
                'api_key': system_api_key,
                'base_url': 'https://api.deepseek.com',
                'model': 'deepseek-chat',
                'max_tokens': 1000,
                'temperature': 0.7
            }
        elif user_config:
            # 使用传入的用户配置
            return {
                'api_key': user_config.get('deepseek_api_key', ''),
                'base_url': user_config.get('deepseek_base_url', 'https://api.deepseek.com'),
                'model': user_config.get('deepseek_model', 'deepseek-chat'),
                'max_tokens': int(user_config.get('deepseek_max_tokens', '1000')),
                'temperature': float(user_config.get('deepseek_temperature', '0.7'))
            }
        else:
            # 默认配置
            return {
                'api_key': '',
                'base_url': 'https://api.deepseek.com',
                'model': 'deepseek-chat',
                'max_tokens': 1000,
                'temperature': 0.7
            }
    
    def _validate_config(self, user_config=None, use_system_key=False) -> bool:
        """验证API配置"""
        current_config = self._get_current_config(user_config, use_system_key)
        api_key = current_config['api_key']
        if not api_key or not api_key.strip():
            return False
        return True
    
    def recreate_note(self, title: str, content: str, user_config=None, user_id=None) -> Dict[str, Any]:
        """
        对笔记进行二创
        
        Args:
            title: 原标题
            content: 原内容
            user_config: 用户配置（可选）
            user_id: 用户ID（用于跟踪使用次数）
            
        Returns:
            dict: 包含新标题和内容的字典
        """
        # Import here to avoid circular import
        from _database import db
        
        use_system_key = False
        
        # 检查用户是否还有免费使用次数
        if user_id:
            usage_count = db.get_user_usage(user_id, 'ai_recreate')
            if usage_count < 3:
                # 还有免费次数，使用系统API Key
                use_system_key = True
                print(f"[AI二创] 用户{user_id}使用免费次数({usage_count + 1}/3)")
            else:
                # 免费次数已用完，检查用户配置
                if not self._validate_config(user_config):
                    return {
                        'success': False,
                        'error': 'AI二创失败，请检查DeepSeek配置。您的3次免费试用已用完，请在"设置"中配置您自己的DeepSeek API Key。'
                    }
                print(f"[AI二创] 用户{user_id}使用自己的API Key")
        else:
            # 没有用户ID，尝试使用系统配置
            use_system_key = True
        
        # 验证配置
        if not self._validate_config(user_config, use_system_key):
            if use_system_key:
                return {
                    'success': False,
                    'error': 'AI二创失败，请检查DeepSeek配置。系统API Key未配置，请联系管理员。'
                }
            else:
                return {
                    'success': False,
                    'error': 'AI二创失败，请检查DeepSeek配置。请在"设置"中配置正确的DeepSeek API Key。'
                }
        
        try:
            # 构建提示词
            prompt = self._build_recreate_prompt(title, content)
            
            # 调用API
            response = self._call_api(prompt, user_config, use_system_key)
            
            if response['success']:
                # 如果使用系统API Key成功，增加用户使用次数
                if use_system_key and user_id and db.get_user_usage(user_id, 'ai_recreate') < 3:
                    db.increment_user_usage(user_id, 'ai_recreate')
                
                # 解析返回的内容
                result = self._parse_recreate_result(response['content'])
                return {
                    'success': True,
                    'data': result
                }
            else:
                return {
                    'success': False,
                    'error': response['error']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'笔记二创失败: {str(e)}'
            }
    
    def _build_recreate_prompt(self, title: str, content: str) -> str:
        """构建二创提示词"""
        prompt = f"""你是一个专业的内容创作助手，擅长将现有内容进行创意改写和优化。

请根据以下小红书笔记内容，创作一个全新版本的笔记：

原标题：{title}
原内容：{content}

要求：
1. 保持原意和核心信息不变
2. 使用不同的表达方式和句式结构
3. 标题要吸引人，适合小红书平台
4. 内容要生动有趣，符合小红书用户喜好
5. 可以适当添加emoji表情
6. 保持积极正面的语调

请按照以下JSON格式返回结果：
{{
    "new_title": "新标题",
    "new_content": "新内容"
}}

注意：只返回JSON格式的结果，不要包含其他解释性文字。"""
        
        return prompt
    
    def _call_api(self, prompt: str, user_config=None, use_system_key=False) -> Dict[str, Any]:
        """调用DeepSeek API"""
        try:
            # 获取当前配置
            current_config = self._get_current_config(user_config, use_system_key)
            
            headers = {
                'Authorization': f'Bearer {current_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': current_config['model'],
                'messages': [
                    {
                        'role': 'system', 
                        'content': '你是一个专业的内容创作助手，擅长将现有内容进行创意改写和优化。'
                    },
                    {
                        'role': 'user', 
                        'content': prompt
                    }
                ],
                'max_tokens': current_config['max_tokens'],
                'temperature': current_config['temperature'],
                'stream': False
            }
            
            response = requests.post(
                f'{current_config["base_url"]}/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return {
                    'success': True,
                    'content': content
                }
            else:
                return {
                    'success': False,
                    'error': f'API调用失败: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'API请求异常: {str(e)}'
            }
    
    def _parse_recreate_result(self, content: str) -> Dict[str, str]:
        """解析二创结果"""
        try:
            # 尝试解析JSON
            result = json.loads(content.strip())
            
            new_title = result.get('new_title', '').strip()
            new_content = result.get('new_content', '').strip()
            
            if not new_title or not new_content:
                raise ValueError("返回的标题或内容为空")
            
            return {
                'new_title': new_title,
                'new_content': new_content
            }
            
        except json.JSONDecodeError:
            # 如果不是标准JSON，尝试提取内容
            lines = content.strip().split('\n')
            new_title = ""
            new_content = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('标题') or line.startswith('新标题'):
                    new_title = line.split('：', 1)[-1].split(':', 1)[-1].strip()
                elif line.startswith('内容') or line.startswith('新内容'):
                    new_content = line.split('：', 1)[-1].split(':', 1)[-1].strip()
            
            if not new_title and not new_content:
                # 如果都提取不到，直接使用返回内容作为新内容
                new_title = "AI生成的新标题"
                new_content = content.strip()
            
            return {
                'new_title': new_title or "AI生成的新标题",
                'new_content': new_content or content.strip()
            }
        
        except Exception as e:
            return {
                'new_title': "解析失败",
                'new_content': f"内容解析出错: {str(e)}\n\n原始返回: {content}"
            }
    
    def test_connection(self, user_config=None) -> Dict[str, Any]:
        """测试API连接"""
        if not self._validate_config(user_config):
            return {
                'success': False,
                'error': 'DeepSeek API配置不完整，请检查API Key设置'
            }
        
        try:
            # 发送测试请求
            test_prompt = "请回复'连接测试成功'"
            result = self._call_api(test_prompt, user_config)
            
            if result['success']:
                return {
                    'success': True,
                    'message': 'DeepSeek API连接测试成功'
                }
            else:
                return {
                    'success': False,
                    'error': f'API调用失败: {result["error"]}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'连接测试失败: {str(e)}'
            }

# 全局API实例
deepseek_api = DeepSeekAPI()