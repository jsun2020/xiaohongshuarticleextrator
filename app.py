from flask import Flask, request, jsonify, session
from flask_cors import CORS
from xhs_v2 import get_xiaohongshu_note
from database import db
from deepseek_api import deepseek_api
from config import config
import json
import os
import hashlib
from datetime import datetime

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 允许跨域请求并支持凭据
app.secret_key = 'xiaohongshu_app_secret_key_2024'  # 用于session加密

# 简单的用户认证（实际项目中应使用更安全的方式）
USERS = {
    'admin': hashlib.md5('admin123'.encode()).hexdigest(),
    'user': hashlib.md5('user123'.encode()).hexdigest()
}

def require_auth(f):
    """认证装饰器"""
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'error': '请先登录'
            }), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

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
            
            save_success = db.save_note(note_data)
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
        notes = db.get_notes_list(limit=limit, offset=offset)
        total_count = db.get_notes_count()
        
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
        success = db.delete_note(note_id)
        
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

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': '用户名和密码不能为空'
            }), 400
        
        # 验证用户凭据
        password_hash = hashlib.md5(password.encode()).hexdigest()
        if username in USERS and USERS[username] == password_hash:
            session['user'] = username
            session['logged_in'] = True
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user': username
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': '用户名或密码错误'
            }), 401
            
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
    if session.get('logged_in'):
        return jsonify({
            'success': True,
            'logged_in': True,
            'user': session.get('user')
        }), 200
    else:
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
            
            history_saved = db.save_recreate_history(history_data)
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
        
        history_list = db.get_recreate_history(limit=limit, offset=offset)
        total_count = db.get_recreate_history_count()
        
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
        success = db.delete_recreate_history(history_id)
        
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
        # 获取配置（隐藏API Key）
        deepseek_config = config.get_deepseek_config()
        safe_config = deepseek_config.copy()
        if safe_config.get('api_key'):
            api_key = safe_config['api_key']
            if len(api_key) > 8:
                safe_config['api_key'] = api_key[:8] + '***' + api_key[-4:]
            elif len(api_key) > 4:
                safe_config['api_key'] = '***' + api_key[-4:]
            else:
                safe_config['api_key'] = '***'
        
        return jsonify({
            'success': True,
            'config': safe_config
        }), 200
    
    elif request.method == 'POST':
        # 更新配置
        try:
            data = request.get_json()
            
            if 'api_key' in data:
                config.set_deepseek_api_key(data['api_key'])
            if 'model' in data:
                config.set('deepseek.model', data['model'])
            if 'temperature' in data:
                config.set('deepseek.temperature', float(data['temperature']))
            if 'max_tokens' in data:
                config.set('deepseek.max_tokens', int(data['max_tokens']))
            
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