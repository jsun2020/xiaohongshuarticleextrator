#!/usr/bin/env python3
"""
DeepSeek API Key 诊断工具
"""
import requests
import json
from config import config

def diagnose_api_key():
    """诊断API Key问题"""
    print("🔍 DeepSeek API Key 诊断工具")
    print("=" * 50)
    
    # 获取配置
    deepseek_config = config.get_deepseek_config()
    api_key = deepseek_config.get('api_key', '')
    
    print(f"📋 当前配置:")
    print(f"  API Key: {api_key[:10]}***{api_key[-4:] if len(api_key) > 10 else '****'}")
    print(f"  Base URL: {deepseek_config.get('base_url', 'https://api.deepseek.com')}")
    print(f"  Model: {deepseek_config.get('model', 'deepseek-chat')}")
    
    # 1. 基本格式检查
    print("\n1️⃣ API Key 格式检查:")
    if not api_key:
        print("   ❌ API Key 为空")
        return
    elif not api_key.startswith('sk-'):
        print("   ❌ API Key 格式错误，应以 'sk-' 开头")
        return
    elif len(api_key) < 20:
        print("   ❌ API Key 长度不足，可能不完整")
        return
    else:
        print("   ✅ API Key 格式正确")
    
    # 2. 网络连接检查
    print("\n2️⃣ 网络连接检查:")
    try:
        response = requests.get("https://api.deepseek.com", timeout=10)
        print("   ✅ 可以访问 DeepSeek API 服务器")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ 无法访问 DeepSeek API 服务器: {e}")
        return
    
    # 3. API Key 有效性检查
    print("\n3️⃣ API Key 有效性检查:")
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # 尝试一个简单的API调用
    data = {
        'model': deepseek_config.get('model', 'deepseek-chat'),
        'messages': [
            {'role': 'user', 'content': 'Hello'}
        ],
        'max_tokens': 10
    }
    
    try:
        response = requests.post(
            f"{deepseek_config.get('base_url', 'https://api.deepseek.com')}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            print("   ✅ API Key 有效，连接成功")
            result = response.json()
            print(f"   📝 测试响应: {result.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')}")
        elif response.status_code == 401:
            error_info = response.json()
            print(f"   ❌ API Key 无效: {error_info.get('error', {}).get('message', '未知错误')}")
            
            # 详细错误分析
            error_message = error_info.get('error', {}).get('message', '')
            if 'invalid' in error_message.lower():
                print("   💡 可能的原因:")
                print("      • API Key 输入错误或不完整")
                print("      • API Key 已被删除或禁用")
                print("      • 复制粘贴时包含了额外的字符")
            
        elif response.status_code == 429:
            print("   ⚠️  请求过于频繁，请稍后重试")
        elif response.status_code == 402:
            print("   💰 账户余额不足，请充值")
        else:
            print(f"   ❌ API 调用失败: {response.status_code}")
            try:
                error_info = response.json()
                print(f"   📄 错误详情: {error_info}")
            except:
                print(f"   📄 响应内容: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"   ❌ 网络请求失败: {e}")
    
    # 4. 解决建议
    print("\n4️⃣ 解决建议:")
    print("   🔧 请尝试以下步骤:")
    print("   1. 登录 https://platform.deepseek.com")
    print("   2. 检查 API Keys 页面，确认密钥状态")
    print("   3. 如果密钥已过期或被禁用，创建新的 API Key")
    print("   4. 检查账户余额是否充足")
    print("   5. 重新复制完整的 API Key（确保没有多余空格）")
    print("   6. 在系统设置中重新保存 API Key")

if __name__ == '__main__':
    diagnose_api_key()