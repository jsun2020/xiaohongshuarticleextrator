#!/usr/bin/env python3
"""
API Key 验证工具
"""

def validate_api_key(api_key):
    """验证API Key格式"""
    print("🔍 API Key 格式验证")
    print("=" * 30)
    
    if not api_key:
        print("❌ API Key 为空")
        return False
    
    print(f"📏 长度: {len(api_key)} 字符")
    print(f"🔤 格式: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else api_key}")
    
    # 检查前缀
    if not api_key.startswith('sk-'):
        print("❌ API Key 必须以 'sk-' 开头")
        return False
    else:
        print("✅ 前缀正确 (sk-)")
    
    # 检查长度
    if len(api_key) < 40:
        print("❌ API Key 长度不足，可能不完整")
        print(f"   当前长度: {len(api_key)}")
        print(f"   期望长度: 51 字符")
        return False
    elif len(api_key) == 51:
        print("✅ 长度正确 (51 字符)")
    else:
        print(f"⚠️  长度异常: {len(api_key)} 字符 (期望: 51)")
    
    # 检查字符
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-')
    if all(c in allowed_chars for c in api_key):
        print("✅ 字符格式正确")
    else:
        print("❌ 包含无效字符")
        return False
    
    print("\n✅ API Key 格式验证通过")
    return True

if __name__ == '__main__':
    # 测试当前配置的API Key
    from config import config
    current_api_key = config.get_deepseek_config().get('api_key', '')
    
    print("当前配置的API Key:")
    validate_api_key(current_api_key)
    
    print("\n" + "="*50)
    print("💡 如果验证失败，请:")
    print("1. 访问 https://platform.deepseek.com")
    print("2. 登录并进入 API Keys 页面")
    print("3. 创建新的 API Key")
    print("4. 复制完整的 API Key (51个字符)")
    print("5. 在系统设置中重新保存")