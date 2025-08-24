#!/usr/bin/env python3
"""
演示数据生成脚本
"""
from database import db
from datetime import datetime
import json

def create_demo_data():
    """创建演示数据"""
    print("🎭 创建演示数据...")
    
    # 先清理旧数据
    try:
        import os
        if os.path.exists("xiaohongshu_notes.db"):
            os.remove("xiaohongshu_notes.db")
            print("🗑️ 清理旧数据库文件")
    except:
        pass
    
    # 重新初始化数据库
    from database import XiaohongshuDatabase
    db_new = XiaohongshuDatabase()
    
    # 演示笔记数据
    demo_notes = [
        {
            "note_id": "demo001",
            "title": "秋日穿搭分享 | 温柔奶茶色系搭配",
            "content": "今天分享一套超温柔的奶茶色系穿搭～\n\n上衣：选择了一件米色针织衫，质感很好，颜色很显白\n下装：搭配了一条卡其色阔腿裤，很显腿长\n鞋子：选择了小白鞋，简约百搭\n包包：奶茶色小方包，和整体色调很搭\n\n这套搭配很适合秋天，温柔又有气质～\n你们觉得怎么样呀？",
            "type": "图文",
            "author": {
                "user_id": "user_demo_001",
                "nickname": "小红薯穿搭师",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/demo1.jpg"
            },
            "stats": {
                "likes": 1234,
                "collects": 567,
                "comments": 89,
                "shares": 23
            },
            "publish_time": "2024-01-15 14:30:00",
            "location": "上海",
            "tags": ["穿搭", "秋日搭配", "奶茶色", "温柔风"],
            "images": [
                "https://sns-webpic-qc.xhscdn.com/demo1_1.jpg",
                "https://sns-webpic-qc.xhscdn.com/demo1_2.jpg",
                "https://sns-webpic-qc.xhscdn.com/demo1_3.jpg"
            ],
            "videos": []
        },
        {
            "note_id": "demo002", 
            "title": "超简单的蜂蜜柠檬茶制作方法",
            "content": "天气转凉了，来一杯暖暖的蜂蜜柠檬茶吧～\n\n🍋 材料准备：\n- 新鲜柠檬 1个\n- 蜂蜜 2勺\n- 温水 300ml\n- 薄荷叶 几片（可选）\n\n👩‍🍳 制作步骤：\n1. 柠檬洗净切片，去籽\n2. 将柠檬片放入杯中\n3. 加入蜂蜜\n4. 倒入温水，搅拌均匀\n5. 最后放上薄荷叶装饰\n\n酸甜可口，还能美白养颜哦～\n姐妹们快试试吧！",
            "type": "图文",
            "author": {
                "user_id": "user_demo_002",
                "nickname": "美食小达人",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/demo2.jpg"
            },
            "stats": {
                "likes": 2156,
                "collects": 892,
                "comments": 156,
                "shares": 45
            },
            "publish_time": "2024-01-14 16:45:00",
            "location": "北京",
            "tags": ["美食", "饮品", "蜂蜜柠檬茶", "简单易做"],
            "images": [
                "https://sns-webpic-qc.xhscdn.com/demo2_1.jpg",
                "https://sns-webpic-qc.xhscdn.com/demo2_2.jpg"
            ],
            "videos": []
        },
        {
            "note_id": "demo003",
            "title": "护肤分享 | 我的晚间护肤routine",
            "content": "分享一下我的晚间护肤步骤～\n\n🧴 产品清单：\n1. 卸妆油 - 温和卸妆\n2. 洁面乳 - 深层清洁\n3. 爽肤水 - 二次清洁+补水\n4. 精华液 - 美白淡斑\n5. 面霜 - 锁水保湿\n6. 眼霜 - 淡化细纹\n\n💡 小贴士：\n- 卸妆一定要彻底\n- 护肤品要按分子大小使用\n- 坚持才有效果\n\n用了这套routine一个月，皮肤状态明显改善了～\n有什么护肤问题可以问我哦！",
            "type": "图文",
            "author": {
                "user_id": "user_demo_003",
                "nickname": "护肤小仙女",
                "avatar": "https://sns-avatar-qc.xhscdn.com/avatar/demo3.jpg"
            },
            "stats": {
                "likes": 3421,
                "collects": 1567,
                "comments": 234,
                "shares": 78
            },
            "publish_time": "2024-01-13 21:20:00",
            "location": "广州",
            "tags": ["护肤", "晚间护肤", "护肤routine", "美容"],
            "images": [
                "https://sns-webpic-qc.xhscdn.com/demo3_1.jpg",
                "https://sns-webpic-qc.xhscdn.com/demo3_2.jpg",
                "https://sns-webpic-qc.xhscdn.com/demo3_3.jpg",
                "https://sns-webpic-qc.xhscdn.com/demo3_4.jpg"
            ],
            "videos": []
        }
    ]
    
    # 保存演示数据
    success_count = 0
    for note_data in demo_notes:
        if db_new.save_note(note_data):
            success_count += 1
    
    print(f"✅ 成功创建 {success_count}/{len(demo_notes)} 条演示数据")
    
    # 创建一些演示的二创历史
    demo_history = [
        {
            "original_note_id": "demo001",
            "original_title": "秋日穿搭分享 | 温柔奶茶色系搭配",
            "original_content": "今天分享一套超温柔的奶茶色系穿搭～",
            "new_title": "🍂 秋日温柔穿搭 | 奶茶色系的浪漫邂逅",
            "new_content": "秋风起，叶渐黄，是时候换上温柔的奶茶色系了～\n\n✨ 今日搭配灵感：\n🤎 上衣：精选米色羊绒针织衫，触感如云朵般柔软\n👖 下装：高腰卡其色阔腿裤，优雅显高又藏肉\n👟 足下：经典小白鞋，简约中透露着青春活力\n👜 配饰：奶茶色迷你方包，精致点缀整体look\n\n这样的搭配既有秋日的温暖，又不失时尚感～\n姐妹们，你们的秋日穿搭是什么风格呢？"
        }
    ]
    
    for history_data in demo_history:
        db_new.save_recreate_history(history_data)
    
    print(f"✅ 成功创建 {len(demo_history)} 条二创历史记录")
    
    # 显示统计信息
    total_notes = db_new.get_notes_count()
    total_history = db_new.get_recreate_history_count()
    
    print(f"\n📊 数据库统计:")
    print(f"  📝 笔记总数: {total_notes}")
    print(f"  🤖 二创历史: {total_history}")
    print(f"\n🎉 演示数据创建完成！现在可以体验完整功能了")

if __name__ == '__main__':
    create_demo_data()