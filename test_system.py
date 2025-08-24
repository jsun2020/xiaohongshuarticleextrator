#!/usr/bin/env python3
"""
系统功能测试脚本
"""
import requests
import json

def test_backend():
    """测试后端功能"""
    print("🔍 测试后端服务...")
    
    try:
        # 测试健康检查
        response = requests.get('http://localhost:5000/api/health')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查: {data['message']}")
            print(f"📊 数据库状态: {data['database_status']}")
            print(f"📝 笔记总数: {data['total_notes']}")
            print(f"🤖 DeepSeek配置: {'已配置' if data['deepseek_configured'] else '未配置'}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
            
        # 测试登录接口
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        session = requests.Session()
        response = session.post('http://localhost:5000/api/auth/login', json=login_data)
        
        if response.status_code == 200:
            print("✅ 登录接口正常")
        else:
            print(f"❌ 登录接口异常: {response.status_code}")
            
        # 测试笔记列表接口
        response = session.get('http://localhost:5000/api/xiaohongshu/notes')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 笔记列表接口正常: 共{data['data']['total']}条记录")
        else:
            print(f"❌ 笔记列表接口异常: {response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保后端已启动")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_frontend():
    """测试前端服务"""
    print("\n🔍 测试前端服务...")
    
    try:
        response = requests.get('http://localhost:3000')
        if response.status_code == 200:
            print("✅ 前端服务正常")
            return True
        else:
            print(f"❌ 前端服务异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到前端服务，请确保前端已启动")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 小红书数据研究院 - 系统测试")
    print("=" * 50)
    
    backend_ok = test_backend()
    frontend_ok = test_frontend()
    
    print("\n📋 测试结果:")
    print(f"  后端服务: {'✅ 正常' if backend_ok else '❌ 异常'}")
    print(f"  前端服务: {'✅ 正常' if frontend_ok else '❌ 异常'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 系统测试通过！可以正常使用")
        print("🌐 访问地址: http://localhost:3000")
    else:
        print("\n⚠️  系统测试未完全通过，请检查服务状态")

if __name__ == '__main__':
    main()