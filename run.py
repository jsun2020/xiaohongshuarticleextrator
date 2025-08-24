#!/usr/bin/env python3
"""
小红书数据研究院 - 简化启动脚本
"""
import os
import sys

def main():
    print("🌸 小红书数据研究院")
    print("=" * 50)
    print("📡 后端服务: http://localhost:5000")
    print("🎨 前端应用: http://localhost:3000")
    print("🔑 登录账号: admin/admin123 或 user/user123")
    print("=" * 50)
    
    print("\n🚀 启动后端服务...")
    
    try:
        from app import app
        print("✅ 后端服务启动成功")
        print("💡 请在另一个终端运行 'npm run dev' 启动前端")
        print("⚠️  按 Ctrl+C 停止服务")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == '__main__':
    main()