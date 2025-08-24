#!/usr/bin/env python3
"""
测试DeepSeek API连接
"""
from deepseek_api import deepseek_api
from config import config
import json

def test_deepseek_api():
    """测试DeepSeek API功能"""
    print("🔧 测试DeepSeek API连接...")
    
    # 显示当前配置
    current_config = config.get_deepseek_config()
    print(f"📋 当前配置:")
    print(f"  API Key: {current_config.get('api_key', '未设置')[:8]}***{current_config.get('api_key', '')[-4:] if len(current_config.get('api_key', '')) > 8 else '***'}")
    print(f"  Base URL: {current_config.get('base_url', '未设置')}")
    print(f"  Model: {current_config.get('model', '未设置')}")
    print(f"  Temperature: {current_config.get('temperature', '未设置')}")
    print(f"  Max Tokens: {current_config.get('max_tokens', '未设置')}")
    
    # 测试连接
    print(f"\n🔍 测试API连接...")
    result = deepseek_api.test_connection()
    
    if result['success']:
        print(f"✅ 连接成功: {result['message']}")
        
        # 测试二创功能
        print(f"\n🤖 测试二创功能...")
        recreate_result = deepseek_api.recreate_note(
            "测试标题", 
            "这是一个测试内容，用于验证DeepSeek API的二创功能是否正常工作。"
        )
        
        if recreate_result['success']:
            print(f"✅ 二创成功:")
            print(f"  新标题: {recreate_result['data']['new_title']}")
            print(f"  新内容: {recreate_result['data']['new_content'][:100]}...")
        else:
            print(f"❌ 二创失败: {recreate_result['error']}")
    else:
        print(f"❌ 连接失败: {result['error']}")
        
        # 提供解决建议
        print(f"\n💡 解决建议:")
        print(f"  1. 检查API Key是否正确")
        print(f"  2. 确认API Key有足够的余额")
        print(f"  3. 检查网络连接")
        print(f"  4. 验证API Key格式（应以sk-开头）")

def test_config_update():
    """测试配置更新功能"""
    print(f"\n🔧 测试配置更新功能...")
    
    # 保存当前配置
    original_api_key = config.get('deepseek.api_key')
    
    # 测试更新配置
    test_api_key = "sk-test123456789"
    config.set_deepseek_api_key(test_api_key)
    
    # 验证配置是否更新
    updated_api_key = config.get('deepseek.api_key')
    if updated_api_key == test_api_key:
        print(f"✅ 配置更新成功")
    else:
        print(f"❌ 配置更新失败")
    
    # 恢复原始配置
    config.set_deepseek_api_key(original_api_key)
    print(f"✅ 配置已恢复")

if __name__ == '__main__':
    test_deepseek_api()
    test_config_update()