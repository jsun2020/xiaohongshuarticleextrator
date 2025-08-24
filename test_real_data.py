#!/usr/bin/env python3
"""
测试真实数据采集和保存
"""
from app import app
import json

def test_note_collection():
    """测试笔记采集功能"""
    print("🔍 测试笔记采集和保存功能...")
    
    with app.test_client() as client:
        # 先登录
        login_response = client.post('/api/auth/login', 
                                   json={'username': 'admin', 'password': 'admin123'})
        
        if login_response.status_code != 200:
            print("❌ 登录失败")
            return
        
        print("✅ 登录成功")
        
        # 测试采集接口（使用一个测试URL）
        test_url = "https://www.xiaohongshu.com/explore/test123"
        
        # 模拟采集数据（因为真实采集需要有效的小红书链接）
        mock_data = {
            "url": test_url
        }
        
        print(f"📝 测试采集URL: {test_url}")
        
        response = client.post('/api/xiaohongshu/note', json=mock_data)
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📋 响应内容: {response.get_json()}")
        
        # 检查笔记列表
        list_response = client.get('/api/xiaohongshu/notes')
        if list_response.status_code == 200:
            data = list_response.get_json()
            print(f"📚 笔记总数: {data['data']['total']}")
        
        # 检查健康状态
        health_response = client.get('/api/health')
        if health_response.status_code == 200:
            health_data = health_response.get_json()
            print(f"🏥 数据库状态: {health_data['database_status']}")
            print(f"📊 笔记总数: {health_data['total_notes']}")

if __name__ == '__main__':
    test_note_collection()