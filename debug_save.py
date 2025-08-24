#!/usr/bin/env python3
"""
调试数据库保存问题
"""
from database import db
import traceback

def test_save_note():
    """测试保存笔记功能"""
    print("🔍 测试数据库保存功能...")
    
    # 创建测试数据
    test_note_data = {
        "note_id": "test123456",
        "title": "测试标题",
        "content": "测试内容",
        "type": "图文",
        "author": {
            "nickname": "测试用户",
            "user_id": "test_user_123",
            "avatar": "https://example.com/avatar.jpg"
        },
        "stats": {
            "likes": 100,
            "collects": 50,
            "comments": 20,
            "shares": 10
        },
        "publish_time": "2024-01-15 14:30:00",
        "location": "北京",
        "tags": ["测试", "调试"],
        "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
        "videos": [],
        "original_url": "https://test.com/note/123"
    }
    
    try:
        print("📝 测试数据:")
        for key, value in test_note_data.items():
            print(f"  {key}: {value}")
        
        print("\n💾 开始保存...")
        result = db.save_note(test_note_data)
        
        if result:
            print("✅ 保存成功!")
            
            # 验证数据是否正确保存
            print("\n🔍 验证保存的数据...")
            notes = db.get_notes_list(limit=1)
            if notes:
                saved_note = notes[0]
                print("📋 保存的笔记:")
                for key, value in saved_note.items():
                    print(f"  {key}: {value}")
            else:
                print("❌ 未找到保存的笔记")
        else:
            print("❌ 保存失败!")
            
    except Exception as e:
        print(f"❌ 保存过程中出现异常: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()

def test_save_with_missing_fields():
    """测试缺少字段的情况"""
    print("\n🔍 测试缺少字段的情况...")
    
    # 创建缺少某些字段的测试数据
    incomplete_note_data = {
        "note_id": "test_incomplete",
        "title": "不完整的测试数据",
        "content": None,  # 可能为空
        "type": "图文",
        "author": {
            "nickname": "测试用户2",
            "user_id": "test_user_456",
            "avatar": None  # 可能为空
        },
        "stats": {
            "likes": "1,234",  # 可能包含逗号
            "collects": "",    # 可能为空字符串
            "comments": None,  # 可能为None
            "shares": 0
        },
        "publish_time": None,  # 可能为空
        "location": "",        # 可能为空字符串
        "tags": [],           # 可能为空列表
        "images": [],         # 可能为空列表
        "videos": []          # 可能为空列表
    }
    
    try:
        print("📝 不完整的测试数据:")
        for key, value in incomplete_note_data.items():
            print(f"  {key}: {value}")
        
        print("\n💾 开始保存...")
        result = db.save_note(incomplete_note_data)
        
        if result:
            print("✅ 保存成功!")
        else:
            print("❌ 保存失败!")
            
    except Exception as e:
        print(f"❌ 保存过程中出现异常: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()

if __name__ == '__main__':
    test_save_note()
    test_save_with_missing_fields()