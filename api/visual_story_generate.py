"""
Visual Story Generation API endpoint for Vercel
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict, Optional

# Add project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, session
from api._database import db
from api.gemini_visual_story import create_gemini_client


def require_auth(func):
    """Authentication decorator"""
    def wrapper(*args, **kwargs):
        if not session.get('logged_in') or not session.get('user_id'):
            return jsonify({
                'success': False,
                'error': '请先登录'
            }), 401
        return func(*args, **kwargs)
    return wrapper


def get_current_user_id():
    """Get current logged-in user ID"""
    return session.get('user_id')


async def generate_visual_story_handler():
    """Handle visual story generation request"""
    try:
        # Get request data
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
        model = data.get('model', 'gemini-2.0-flash-exp')
        
        # Get user's Gemini API key
        user_config = db.get_user_config(user_id)
        gemini_api_key = user_config.get('gemini_api_key')
        
        if not gemini_api_key:
            return jsonify({
                'success': False,
                'error': '请先在设置中配置Gemini API密钥'
            }), 400
        
        # Check user credits/usage
        visual_story_used = db.get_user_usage(user_id, 'visual_story') or 0
        max_free_usage = 10  # As per PRD
        
        if visual_story_used >= max_free_usage and not gemini_api_key:
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
        
        # Generate visual story
        try:
            story_result = await gemini_client.generate_visual_story(title, content)
            
            if not story_result['success']:
                return jsonify({
                    'success': False,
                    'error': f'生成视觉故事失败: {story_result["error"]}'
                }), 500
            
            story_data = story_result['data']
            
            # Save visual story to database
            visual_story_record = {
                'user_id': user_id,
                'history_id': history_id,
                'title': title,
                'content': content,
                'cover_card': story_data['cover_card'],
                'content_cards': story_data['content_cards'],
                'html_content': story_data['html'],
                'model_used': model,
                'created_at': datetime.now().isoformat()
            }
            
            # Save to visual story history table
            visual_story_id = save_visual_story_history(visual_story_record)
            
            if visual_story_id:
                # Increment user usage
                db.increment_user_usage(user_id, 'visual_story')
                
                return jsonify({
                    'success': True,
                    'data': {
                        'visual_story_id': visual_story_id,
                        'cover_card': story_data['cover_card'],
                        'content_cards': story_data['content_cards'],
                        'html': story_data['html'],
                        'remaining_credits': max_free_usage - (visual_story_used + 1) if not gemini_api_key else -1
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


def save_visual_story_history(record: Dict) -> Optional[int]:
    """Save visual story to database"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Convert complex data to JSON strings
        cover_card_json = json.dumps(record['cover_card'], ensure_ascii=False)
        content_cards_json = json.dumps(record['content_cards'], ensure_ascii=False)
        
        if db.use_postgres:
            cursor.execute('''
                INSERT INTO visual_story_history 
                (user_id, history_id, title, content, cover_card_data, content_cards_data, 
                 html_content, model_used, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (
                record['user_id'],
                record['history_id'],
                record['title'],
                record['content'],
                cover_card_json,
                content_cards_json,
                record['html_content'],
                record['model_used'],
                record['created_at']
            ))
            visual_story_id = cursor.fetchone()[0]
        else:
            cursor.execute('''
                INSERT INTO visual_story_history 
                (user_id, history_id, title, content, cover_card_data, content_cards_data, 
                 html_content, model_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record['user_id'],
                record['history_id'],
                record['title'],
                record['content'],
                cover_card_json,
                content_cards_json,
                record['html_content'],
                record['model_used'],
                record['created_at']
            ))
            visual_story_id = cursor.lastrowid
        
        conn.commit()
        return visual_story_id
        
    except Exception as e:
        print(f"保存视觉故事历史失败: {e}")
        return None
    finally:
        conn.close()


def get_visual_story_history(user_id: int, limit: int = 20, offset: int = 0) -> Dict:
    """Get user's visual story history"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.use_postgres:
            cursor.execute('''
                SELECT id, history_id, title, model_used, created_at
                FROM visual_story_history 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            ''', (user_id, limit, offset))
            
            # Get total count
            cursor.execute('SELECT COUNT(*) FROM visual_story_history WHERE user_id = %s', (user_id,))
        else:
            cursor.execute('''
                SELECT id, history_id, title, model_used, created_at
                FROM visual_story_history 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))
            
            # Get total count
            cursor.execute('SELECT COUNT(*) FROM visual_story_history WHERE user_id = ?', (user_id,))
        
        rows = cursor.fetchall()
        total_count = cursor.fetchone()[0]
        
        columns = [desc[0] for desc in cursor.description[:5]]  # Only first 5 columns
        history_list = [dict(zip(columns, row)) for row in rows]
        
        return {
            'success': True,
            'data': {
                'history': history_list,
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'获取视觉故事历史失败: {str(e)}'
        }
    finally:
        conn.close()


# Export the handler function for Vercel
handler = generate_visual_story_handler


# For local testing
if __name__ == "__main__":
    app = Flask(__name__)
    app.secret_key = 'test_key'
    
    @app.route('/api/visual-story/generate', methods=['POST'])
    @require_auth
    async def generate_endpoint():
        return await generate_visual_story_handler()
    
    @app.route('/api/visual-story/history', methods=['GET'])
    @require_auth
    def history_endpoint():
        user_id = get_current_user_id()
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        result = get_visual_story_history(user_id, limit, offset)
        return jsonify(result)
    
    app.run(debug=True)