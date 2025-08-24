#!/usr/bin/env python3
"""
API Key安全存储和显示测试
"""
from app import app
import json

def test_api_key_security():
    """测试API Key的安全存储和显示机制"""
    print("🔐 API Key安全机制测试")
    print("=" * 50)
    
    with app.test_client() as client:
        # 登录
        login_response = client.post('/api/auth/login', 
                                   json={'username': 'admin', 'password': 'admin123'})
        if login_response.status_code != 200:
            print("❌ 登录失败")
            return
        
        print("✅ 登录成功")
        
        # 1. 保存完整的API Key
        test_api_key = "sk-test1234567890abcdef1234567890abcdef1234567890"
        print(f"\n1️⃣ 保存测试API Key: {test_api_key[:10]}...{test_api_key[-10:]}")
        
        save_response = client.post('/api/deepseek/config', json={
            'api_key': test_api_key,
            'temperature': 0.7
        })
        
        if save_response.status_code == 200:
            print("   ✅ API Key保存成功")
        else:
            print("   ❌ API Key保存失败")
            return
        
        # 2. 获取配置（应该显示掩码）
        print("\n2️⃣ 获取配置（检查掩码显示）")
        config_response = client.get('/api/deepseek/config')
        
        if config_response.status_code == 200:
            config_data = config_response.get_json()
            displayed_key = config_data['config']['api_key']
            print(f"   📱 前端显示: {displayed_key}")
            
            if '***' in displayed_key:
                print("   ✅ API Key正确显示为掩码")
            else:
                print("   ❌ API Key未正确掩码")
                return
        else:
            print("   ❌ 获取配置失败")
            return
        
        # 3. 验证实际存储（应该是完整的）
        print("\n3️⃣ 验证后端存储（检查完整性）")
        from config import config
        actual_key = config.get_deepseek_config().get('api_key', '')
        print(f"   💾 实际存储: {actual_key[:10]}...{actual_key[-10:]}")
        
        if actual_key == test_api_key:
            print("   ✅ 后端存储完整正确")
        else:
            print("   ❌ 后端存储不正确")
            return
        
        # 4. 测试掩码保存（不应该覆盖原值）
        print("\n4️⃣ 测试掩码保存（防止覆盖）")
        mask_save_response = client.post('/api/deepseek/config', json={
            'api_key': displayed_key,  # 使用掩码值
            'temperature': 0.8
        })
        
        if mask_save_response.status_code == 200:
            print("   ✅ 掩码保存请求成功")
            
            # 验证原API Key未被覆盖
            actual_key_after = config.get_deepseek_config().get('api_key', '')
            if actual_key_after == test_api_key:
                print("   ✅ 原API Key未被掩码覆盖")
            else:
                print(f"   ❌ 原API Key被覆盖: {actual_key_after}")
                return
        else:
            print("   ❌ 掩码保存请求失败")
            return
        
        # 5. 测试新API Key保存
        print("\n5️⃣ 测试新API Key保存")
        new_api_key = "sk-new9876543210fedcba9876543210fedcba9876543210"
        new_save_response = client.post('/api/deepseek/config', json={
            'api_key': new_api_key
        })
        
        if new_save_response.status_code == 200:
            print("   ✅ 新API Key保存成功")
            
            # 验证新API Key被正确保存
            actual_new_key = config.get_deepseek_config().get('api_key', '')
            if actual_new_key == new_api_key:
                print("   ✅ 新API Key正确保存")
            else:
                print(f"   ❌ 新API Key保存错误: {actual_new_key}")
                return
        else:
            print("   ❌ 新API Key保存失败")
            return
        
        # 6. 清理测试数据
        print("\n6️⃣ 清理测试数据")
        client.post('/api/deepseek/config', json={'api_key': ''})
        print("   ✅ 测试数据清理完成")
        
        print("\n" + "="*50)
        print("🎉 API Key安全机制测试通过！")
        print("\n✅ 验证通过的功能:")
        print("   • API Key安全存储（完整保存）")
        print("   • API Key掩码显示（前端安全）")
        print("   • 掩码保存防护（防止覆盖）")
        print("   • 新API Key更新（正常保存）")

if __name__ == '__main__':
    test_api_key_security()