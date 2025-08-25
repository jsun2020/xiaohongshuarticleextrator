#!/usr/bin/env python3
"""
用户认证工具函数
"""
import hashlib
import secrets
import re
from typing import Optional

def hash_password(password: str) -> str:
    """对密码进行哈希加密"""
    # 生成随机盐值
    salt = secrets.token_hex(16)
    # 使用SHA-256进行哈希
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    # 返回盐值和哈希值的组合
    return f"{salt}:{password_hash}"

def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    try:
        salt, stored_hash = password_hash.split(':')
        # 使用相同的盐值对输入密码进行哈希
        input_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return input_hash == stored_hash
    except ValueError:
        return False

def validate_username(username: str) -> tuple[bool, str]:
    """验证用户名格式"""
    if not username:
        return False, "用户名不能为空"
    
    if len(username) < 3:
        return False, "用户名至少需要3个字符"
    
    if len(username) > 20:
        return False, "用户名不能超过20个字符"
    
    # 只允许字母、数字、下划线
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    
    return True, ""

def validate_password(password: str) -> tuple[bool, str]:
    """验证密码强度"""
    if not password:
        return False, "密码不能为空"
    
    if len(password) < 6:
        return False, "密码至少需要6个字符"
    
    if len(password) > 50:
        return False, "密码不能超过50个字符"
    
    # 检查是否包含至少一个字母和一个数字
    has_letter = re.search(r'[a-zA-Z]', password)
    has_digit = re.search(r'\d', password)
    
    if not (has_letter and has_digit):
        return False, "密码必须包含至少一个字母和一个数字"
    
    return True, ""

def validate_email(email: str) -> tuple[bool, str]:
    """验证邮箱格式"""
    if not email:
        return True, ""  # 邮箱是可选的
    
    # 简单的邮箱格式验证
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "邮箱格式不正确"
    
    if len(email) > 100:
        return False, "邮箱地址过长"
    
    return True, ""

def generate_session_token() -> str:
    """生成会话令牌"""
    return secrets.token_urlsafe(32)

if __name__ == "__main__":
    # 测试认证工具函数
    print("🔧 测试认证工具函数...")
    
    # 测试密码哈希
    password = "test123"
    hashed = hash_password(password)
    print(f"原密码: {password}")
    print(f"哈希后: {hashed}")
    print(f"验证结果: {verify_password(password, hashed)}")
    print(f"错误密码验证: {verify_password('wrong', hashed)}")
    
    # 测试用户名验证
    test_usernames = ["test", "user123", "a", "user_name", "user@name", "verylongusernamethatexceedslimit"]
    for username in test_usernames:
        valid, msg = validate_username(username)
        print(f"用户名 '{username}': {'✅' if valid else '❌'} {msg}")
    
    # 测试密码验证
    test_passwords = ["123", "password", "pass123", "verylongpasswordthatexceedsthelimitof50characters"]
    for pwd in test_passwords:
        valid, msg = validate_password(pwd)
        print(f"密码 '{pwd}': {'✅' if valid else '❌'} {msg}")
    
    # 测试邮箱验证
    test_emails = ["", "test@example.com", "invalid-email", "user@domain", "test@example.co.uk"]
    for email in test_emails:
        valid, msg = validate_email(email)
        print(f"邮箱 '{email}': {'✅' if valid else '❌'} {msg}")
    
    print("✅ 认证工具函数测试完成")