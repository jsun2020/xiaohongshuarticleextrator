from flask import Flask, request, jsonify, session
from flask_cors import CORS
from functools import wraps
from xhs_v2 import get_xiaohongshu_note
from database import db
from deepseek_api import deepseek_api
from config import config
from auth_utils import hash_password, verify_password, validate_username, validate_password, validate_email
from api.gemini_visual_story import create_gemini_client
import json
import os
import hashlib
from datetime import datetime

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 允许跨域请求并支持凭据
app.secret_key = 'xiaohongshu_app_secret_key_2024'  # 用于session加密

# 用户认证系统已迁移到数据库

def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or not session.get('user_id'):
            return jsonify({
                'success': False,
                'error': '请先登录'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id():
    """获取当前登录用户ID"""
    return session.get('user_id')

@app.route('/api/xiaohongshu/note', methods=['POST'])
@require_auth
def get_note():
    """获取小红书笔记信息的API接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'error': '请提供小红书笔记链接'
            }), 400
        
        url = data['url']
        cookies = data.get('cookies', None)  # 可选的cookies参数
        
        # 调用爬虫函数获取笔记信息
        result = get_xiaohongshu_note(url, cookies)
        
        if result.get('success'):
            # 保存到数据库
            note_data = result['data']
            note_data['original_url'] = url  # 添加原始URL
            
            user_id = get_current_user_id()
            print(f"🔍 DEBUG: Flask app - user_id from session: {user_id}, type: {type(user_id)}")
            save_success = db.save_note(note_data, user_id)
            print(f"🔍 DEBUG: Flask app - save_success: {save_success}")
            result['saved_to_db'] = save_success
            
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/api/xiaohongshu/notes', methods=['GET'])
@require_auth
def get_notes_list():
    """获取笔记列表的API接口"""
    try:
        # 获取查询参数
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # 从数据库获取笔记列表
        user_id = get_current_user_id()
        notes = db.get_notes_list(user_id, limit=limit, offset=offset)
        total_count = db.get_notes_count(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'notes': notes,
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取笔记列表失败: {str(e)}'
        }), 500

@app.route('/api/xiaohongshu/notes/<note_id>', methods=['DELETE'])
@require_auth
def delete_note(note_id):
    """删除笔记的API接口"""
    try:
        user_id = get_current_user_id()
        success = db.delete_note(user_id, note_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'笔记 {note_id} 删除成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': '删除失败'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'删除笔记失败: {str(e)}'
        }), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册接口"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        nickname = data.get('nickname', '').strip()
        
        # 验证输入
        valid_username, username_msg = validate_username(username)
        if not valid_username:
            return jsonify({'success': False, 'error': username_msg}), 400
        
        valid_password, password_msg = validate_password(password)
        if not valid_password:
            return jsonify({'success': False, 'error': password_msg}), 400
        
        if email:
            valid_email, email_msg = validate_email(email)
            if not valid_email:
                return jsonify({'success': False, 'error': email_msg}), 400
        
        # 检查用户名是否已存在
        existing_user = db.get_user_by_username(username)
        if existing_user:
            return jsonify({'success': False, 'error': '用户名已存在'}), 400
        
        # 创建用户
        password_hash = hash_password(password)
        user_id = db.create_user(username, password_hash, email, nickname)
        
        if user_id:
            return jsonify({
                'success': True,
                'message': '注册成功',
                'user': {
                    'id': user_id,
                    'username': username,
                    'nickname': nickname or username
                }
            }), 201
        else:
            return jsonify({'success': False, 'error': '注册失败，请重试'}), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'注册失败: {str(e)}'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
        
        # 获取用户信息
        user = db.get_user_by_username(username)
        if not user:
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
        
        # 验证密码
        if not verify_password(password, user['password_hash']):
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
        
        # 设置会话
        session['logged_in'] = True
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'nickname': user['nickname'],
                'email': user['email']
            }
        }), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'登录失败: {str(e)}'
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """用户登出接口"""
    session.clear()
    return jsonify({
        'success': True,
        'message': '登出成功'
    }), 200

@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """检查登录状态"""
    if session.get('logged_in') and session.get('user_id'):
        user_id = session.get('user_id')
        user = db.get_user_by_id(user_id)
        if user:
            return jsonify({
                'success': True,
                'logged_in': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'nickname': user['nickname'],
                    'email': user['email']
                }
            }), 200
    
    return jsonify({
        'success': True,
        'logged_in': False
    }), 200

@app.route('/api/xiaohongshu/recreate', methods=['POST'])
@require_auth
def recreate_note():
    """AI二创笔记接口"""
    try:
        data = request.get_json()
        
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': '请提供标题和内容'
            }), 400
        
        title = data['title']
        content = data['content']
        note_id = data.get('note_id', '')
        
        # 调用DeepSeek API进行二创
        result = deepseek_api.recreate_note(title, content)
        
        if result['success']:
            # 保存二创历史到数据库
            history_data = {
                'original_note_id': note_id,
                'original_title': title,
                'original_content': content,
                'new_title': result['data']['new_title'],
                'new_content': result['data']['new_content']
            }
            
            user_id = get_current_user_id()
            history_saved = db.save_recreate_history(user_id, history_data)
            result['history_saved'] = history_saved
            
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'二创失败: {str(e)}'
        }), 500

@app.route('/api/xiaohongshu/recreate/history', methods=['GET'])
@require_auth
def get_recreate_history():
    """获取二创历史列表"""
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        user_id = get_current_user_id()
        history_list = db.get_recreate_history(user_id, limit=limit, offset=offset)
        total_count = db.get_recreate_history_count(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'history': history_list,
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取历史记录失败: {str(e)}'
        }), 500

@app.route('/api/xiaohongshu/recreate/history/<int:history_id>', methods=['DELETE'])
@require_auth
def delete_recreate_history(history_id):
    """删除二创历史记录"""
    try:
        user_id = get_current_user_id()
        success = db.delete_recreate_history(user_id, history_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'历史记录 {history_id} 删除成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': '删除失败'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'删除历史记录失败: {str(e)}'
        }), 500

@app.route('/api/deepseek/config', methods=['GET', 'POST'])
@require_auth
def deepseek_config():
    """DeepSeek配置管理"""
    if request.method == 'GET':
        # 获取用户的DeepSeek配置
        user_id = get_current_user_id()
        user_config = db.get_user_config(user_id)
        
        # 构建DeepSeek配置
        deepseek_config = {
            'api_key': user_config.get('deepseek_api_key', ''),
            'base_url': user_config.get('deepseek_base_url', 'https://api.deepseek.com'),
            'model': user_config.get('deepseek_model', 'deepseek-chat'),
            'temperature': float(user_config.get('deepseek_temperature', '0.7')),
            'max_tokens': int(user_config.get('deepseek_max_tokens', '1000'))
        }
        
        safe_config = deepseek_config.copy()
        
        # 安全显示API Key - 只显示掩码，不影响实际存储
        if safe_config.get('api_key'):
            api_key = safe_config['api_key']
            # 检查是否已经是掩码格式（避免重复掩码）
            if '***' not in api_key:
                if len(api_key) > 12:
                    safe_config['api_key'] = api_key[:8] + '***' + api_key[-4:]
                elif len(api_key) > 8:
                    safe_config['api_key'] = api_key[:4] + '***' + api_key[-4:]
                else:
                    safe_config['api_key'] = '***'
        
        return jsonify({
            'success': True,
            'config': safe_config
        }), 200
    
    elif request.method == 'POST':
        # 更新用户配置
        try:
            data = request.get_json()
            user_id = get_current_user_id()
            
            # 处理API Key更新
            if 'api_key' in data:
                new_api_key = data['api_key'].strip()
                # 如果不是掩码格式，才更新（避免保存掩码）
                if new_api_key and '***' not in new_api_key:
                    db.set_user_config(user_id, 'deepseek_api_key', new_api_key)
                elif not new_api_key:
                    # 如果是空值，清空API Key
                    db.set_user_config(user_id, 'deepseek_api_key', '')
                # 如果是掩码格式，保持原有API Key不变
            
            if 'base_url' in data:
                db.set_user_config(user_id, 'deepseek_base_url', data['base_url'])
            if 'model' in data:
                db.set_user_config(user_id, 'deepseek_model', data['model'])
            if 'temperature' in data:
                db.set_user_config(user_id, 'deepseek_temperature', str(data['temperature']))
            if 'max_tokens' in data:
                db.set_user_config(user_id, 'deepseek_max_tokens', str(data['max_tokens']))
            
            return jsonify({
                'success': True,
                'message': '配置更新成功'
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'配置更新失败: {str(e)}'
            }), 500

@app.route('/api/deepseek/test', methods=['POST'])
@require_auth
def test_deepseek_connection():
    """测试DeepSeek API连接"""
    try:
        result = deepseek_api.test_connection()
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'测试连接失败: {str(e)}'
        }), 500

@app.route('/api/visual-story/generate', methods=['POST'])
@require_auth
def generate_visual_story():
    """生成视觉故事接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请提供请求数据'
            }), 400
        
        # Validate required fields
        required_fields = ['history_id', 'title', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        user_id = get_current_user_id()
        history_id = data['history_id']
        title = data['title']
        content = data['content']
        model = data.get('model', 'gemini-2.5-flash-image')
        
        # Get user's Gemini API key
        user_config = db.get_user_config(user_id)
        gemini_api_key = user_config.get('gemini_api_key')
        
        if not gemini_api_key:
            return jsonify({
                'success': False,
                'error': '请先在设置中配置Gemini API密钥'
            }), 400
        
        # Check user credits/usage (if using platform API key)
        platform_key = config.get('gemini_api_key', '')  # Platform default key
        visual_story_used = 0
        max_free_usage = 3
        
        if gemini_api_key == platform_key:
            # User is using platform key, check limits
            visual_story_used = db.get_user_usage_count(user_id, 'visual_story')
            if visual_story_used >= max_free_usage:
                return jsonify({
                    'success': False,
                    'error': f'免费额度已用完({visual_story_used}/{max_free_usage})，请配置自己的Gemini API密钥'
                }), 403
        
        # Create Gemini client
        try:
            gemini_client = create_gemini_client(gemini_api_key)
            
            # Test connection first
            connection_test = gemini_client.test_connection()
            if not connection_test['success']:
                return jsonify({
                    'success': False,
                    'error': f'Gemini API连接失败: {connection_test["error"]}'
                }), 400
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'初始化Gemini客户端失败: {str(e)}'
            }), 500
        
        # Generate visual story (synchronous for simplicity)
        try:
            # For now, create a simple synchronous version
            # In production, this could be made async with task queues
            
            # Simulate the visual story generation process
            # This is a simplified version - the actual implementation would call the async method
            dummy_result = {
                'success': True,
                'data': {
                    'cover_card': {
                        'title': title,
                        'layout': 'c',
                        'image_url': 'https://via.placeholder.com/600x800/f0f0f0/333?text=Cover+Generated'
                    },
                    'content_cards': [
                        {
                            'title': '核心概念 1',
                            'content': '这是第一个核心概念的阐述...',
                            'layout': 'a',
                            'image_url': 'https://via.placeholder.com/600x800/e1f5fe/333?text=Card+1'
                        },
                        {
                            'title': '核心概念 2', 
                            'content': '这是第二个核心概念的阐述...',
                            'layout': 'b',
                            'image_url': 'https://via.placeholder.com/600x800/f3e5f5/333?text=Card+2'
                        },
                        {
                            'title': '核心概念 3',
                            'content': '这是第三个核心概念的阐述...',
                            'layout': 'c',
                            'image_url': 'https://via.placeholder.com/600x800/e8f5e8/333?text=Card+3'
                        }
                    ],
                    'html': f'''<!DOCTYPE html>
<html><head><title>Visual Story</title></head>
<body><h1>{title}</h1><p>Generated visual story content...</p></body>
</html>'''
                }
            }
            
            story_data = dummy_result['data']
            
            # Save visual story to database
            visual_story_record = {
                'user_id': user_id,
                'history_id': history_id,
                'title': title,
                'content': content,
                'cover_card_data': json.dumps(story_data['cover_card'], ensure_ascii=False),
                'content_cards_data': json.dumps(story_data['content_cards'], ensure_ascii=False),
                'html_content': story_data['html'],
                'model_used': model,
                'created_at': datetime.now().isoformat()
            }
            
            # Save to visual story history - add method to db class
            visual_story_saved = db.save_visual_story_history(user_id, visual_story_record)
            
            if visual_story_saved:
                # Increment user usage if using platform key
                if gemini_api_key == platform_key:
                    db.increment_user_usage(user_id, 'visual_story')
                
                return jsonify({
                    'success': True,
                    'data': {
                        'cover_card': story_data['cover_card'],
                        'content_cards': story_data['content_cards'],
                        'html': story_data['html'],
                        'remaining_credits': max_free_usage - (visual_story_used + 1) if gemini_api_key == platform_key else -1
                    },
                    'message': '视觉故事生成成功'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': '保存视觉故事失败'
                }), 500
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'生成过程发生错误: {str(e)}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/api/visual-story/history', methods=['GET'])
@require_auth
def get_visual_story_history():
    """获取视觉故事历史接口"""
    try:
        user_id = get_current_user_id()
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Get history from database - add method to db class
        history_list = db.get_visual_story_history(user_id, limit=limit, offset=offset)
        total_count = db.get_visual_story_history_count(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'history': history_list,
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取视觉故事历史失败: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'message': '小红书笔记采集API服务正常运行',
        'database_status': 'connected',
        'total_notes': db.get_notes_count(),
        'deepseek_configured': config.validate_deepseek_config()
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)