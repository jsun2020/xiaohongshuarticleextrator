"""
DeepSeek配置API - Vercel Serverless函数
"""
from _utils import parse_request, create_response, require_auth
from _database import db

def mask_api_key(api_key):
    """掩码API Key显示"""
    if not api_key or len(api_key) < 8:
        return api_key
    return api_key[:8] + '*' * (len(api_key) - 12) + api_key[-4:]

def handler(request):
    """处理DeepSeek配置请求"""
    # 初始化数据库
    db.init_database()
    
    req_data = parse_request(request)
    
    # 检查用户认证
    user_id = require_auth(req_data['cookies'])
    if not user_id:
        return create_response({'success': False, 'error': '请先登录'}, 401)
    
    if req_data['method'] == 'GET':
        # 获取用户配置
        try:
            user_config = db.get_user_config(user_id)
            
            # 掩码显示API Key
            masked_config = {
                'api_key': mask_api_key(user_config.get('deepseek_api_key', '')),
                'base_url': user_config.get('deepseek_base_url', 'https://api.deepseek.com'),
                'model': user_config.get('deepseek_model', 'deepseek-chat'),
                'temperature': float(user_config.get('deepseek_temperature', '0.7')),
                'max_tokens': int(user_config.get('deepseek_max_tokens', '1000'))
            }
            
            return create_response({
                'success': True,
                'config': masked_config
            }, 200)
            
        except Exception as e:
            return create_response({
                'success': False,
                'error': f'获取配置失败: {str(e)}'
            }, 500)
    
    elif req_data['method'] == 'POST':
        # 更新用户配置
        try:
            data = req_data['body']
            
            api_key = data.get('api_key', '').strip()
            base_url = data.get('base_url', 'https://api.deepseek.com').strip()
            model = data.get('model', 'deepseek-chat').strip()
            temperature = data.get('temperature', 0.7)
            max_tokens = data.get('max_tokens', 1000)
            
            # 验证必填字段
            if not api_key:
                return create_response({
                    'success': False,
                    'error': 'API Key不能为空'
                }, 400)
            
            # 检查是否是掩码值，如果是则不更新
            current_config = db.get_user_config(user_id)
            current_api_key = current_config.get('deepseek_api_key', '')
            
            if api_key != mask_api_key(current_api_key):
                # 不是掩码值，更新API Key
                db.set_user_config(user_id, 'deepseek_api_key', api_key)
            
            # 更新其他配置
            db.set_user_config(user_id, 'deepseek_base_url', base_url)
            db.set_user_config(user_id, 'deepseek_model', model)
            db.set_user_config(user_id, 'deepseek_temperature', str(temperature))
            db.set_user_config(user_id, 'deepseek_max_tokens', str(max_tokens))
            
            return create_response({
                'success': True,
                'message': 'DeepSeek配置保存成功'
            }, 200)
            
        except Exception as e:
            return create_response({
                'success': False,
                'error': f'保存配置失败: {str(e)}'
            }, 500)
    
    else:
        return create_response({
            'success': False,
            'error': '不支持的请求方法'
        }, 405)