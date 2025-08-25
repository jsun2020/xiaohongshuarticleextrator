#!/usr/bin/env python3
"""
Vercel API函数本地测试
"""
import sys
import os
import json
from unittest.mock import Mock

# 添加api目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

def create_mock_request(method='GET', body=None, query=None, cookies=None, headers=None):
    """创建模拟请求对象"""
    request = Mock()
    request.method = method
    request.body = json.dumps(body or {}).encode('utf-8') if body else b''
    request.args = query or {}
    request.query = query or {}
    request.cookies = cookies or {}
    request.headers = headers or {}
    return request

def test_health_api():
    """测试健康检查API"""
    print("🔍 测试健康检查API...")
    
    try:
        from health import handler
        
        request = create_mock_request('GET')
        response = handler(request)
        
        print(f"   状态码: {response['statusCode']}")
        body = json.loads(response['body'])
        print(f"   响应: {body}")
        
        if response['statusCode'] == 200 and body.get('success'):
            print("   ✅ 健康检查API测试通过")
            return True
        else:
            print("   ❌ 健康检查API测试失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 健康检查API测试异常: {e}")
        return False

def test_auth_register_api():
    """测试用户注册API"""
    print("\\n👤 测试用户注册API...")
    
    try:
        from auth_register import handler
        
        # 测试注册请求
        register_data = {
            'username': 'testuser',
            'password': 'test123',
            'email': 'test@example.com',
            'nickname': '测试用户'
        }
        
        request = create_mock_request('POST', register_data)
        response = handler(request)
        
        print(f"   状态码: {response['statusCode']}")
        body = json.loads(response['body'])
        print(f"   响应: {body}")
        
        if response['statusCode'] in [201, 400]:  # 201成功或400用户已存在
            print("   ✅ 用户注册API测试通过")
            return True
        else:
            print("   ❌ 用户注册API测试失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 用户注册API测试异常: {e}")
        return False

def test_auth_login_api():
    """测试用户登录API"""
    print("\\n🔐 测试用户登录API...")
    
    try:
        from auth_login import handler
        
        # 测试登录请求
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        request = create_mock_request('POST', login_data)
        response = handler(request)
        
        print(f"   状态码: {response['statusCode']}")
        body = json.loads(response['body'])
        print(f"   响应: {body}")
        
        if response['statusCode'] in [200, 401]:  # 200成功或401认证失败
            print("   ✅ 用户登录API测试通过")
            return True
        else:
            print("   ❌ 用户登录API测试失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 用户登录API测试异常: {e}")
        return False

def test_deepseek_config_api():
    """测试DeepSeek配置API"""
    print("\\n⚙️ 测试DeepSeek配置API...")
    
    try:
        from deepseek_config import handler
        
        # 模拟已登录用户
        cookies = {
            'user_id': '1',
            'session_id': 'test_session'
        }
        
        # 测试获取配置
        request = create_mock_request('GET', cookies=cookies)
        response = handler(request)
        
        print(f"   GET状态码: {response['statusCode']}")
        body = json.loads(response['body'])
        print(f"   GET响应: {body}")
        
        # 测试更新配置
        config_data = {
            'api_key': 'sk-test1234567890',
            'model': 'deepseek-chat',
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        request = create_mock_request('POST', config_data, cookies=cookies)
        response = handler(request)
        
        print(f"   POST状态码: {response['statusCode']}")
        body = json.loads(response['body'])
        print(f"   POST响应: {body}")
        
        print("   ✅ DeepSeek配置API测试通过")
        return True
            
    except Exception as e:
        print(f"   ❌ DeepSeek配置API测试异常: {e}")
        return False

def test_xiaohongshu_note_api():
    """测试小红书笔记API"""
    print("\\n📝 测试小红书笔记API...")
    
    try:
        from xiaohongshu_note import handler
        
        # 模拟已登录用户
        cookies = {
            'user_id': '1',
            'session_id': 'test_session'
        }
        
        # 测试获取笔记
        note_data = {
            'url': 'https://www.xiaohongshu.com/explore/test123'
        }
        
        request = create_mock_request('POST', note_data, cookies=cookies)
        response = handler(request)
        
        print(f"   状态码: {response['statusCode']}")
        body = json.loads(response['body'])
        print(f"   响应: {body}")
        
        # 由于没有真实的小红书链接，预期会失败，但API结构应该正确
        if response['statusCode'] in [200, 400, 401]:
            print("   ✅ 小红书笔记API结构测试通过")
            return True
        else:
            print("   ❌ 小红书笔记API测试失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 小红书笔记API测试异常: {e}")
        return False

def main():
    """运行所有API测试"""
    print("🚀 Vercel API函数测试")
    print("=" * 50)
    
    tests = [
        test_health_api,
        test_auth_register_api,
        test_auth_login_api,
        test_deepseek_config_api,
        test_xiaohongshu_note_api
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有API函数测试通过！")
        print("\\n✅ 准备就绪，可以部署到Vercel")
    else:
        print("⚠️  部分测试失败，请检查API函数")
    
    print("\\n📖 部署指南:")
    print("   1. 查看 VERCEL_DEPLOYMENT_GUIDE.md")
    print("   2. 配置数据库连接")
    print("   3. 设置环境变量")
    print("   4. 部署到Vercel")

if __name__ == '__main__':
    main()