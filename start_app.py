#!/usr/bin/env python3
"""
小红书笔记数据采集、二创和管理系统启动脚本
"""
import os
import sys
import subprocess
import time
import threading
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    print("=" * 60)
    print("🌸 小红书数据研究院 - 启动脚本")
    print("📝 数据采集 · 🤖 AI二创 · 📊 智能管理")
    print("=" * 60)

def check_python_dependencies():
    """检查Python依赖"""
    print("🔍 检查Python依赖...")
    required_packages = [
        'flask', 'flask_cors', 'requests', 'sqlite3'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing_packages)}")
        print("请运行以下命令安装:")
        if 'sqlite3' in missing_packages:
            missing_packages.remove('sqlite3')  # sqlite3是内置模块
        if missing_packages:
            print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ Python依赖检查完成")
    return True

def check_node_dependencies():
    """检查Node.js依赖"""
    print("\n🔍 检查Node.js依赖...")
    
    if not os.path.exists('node_modules'):
        print("❌ 未找到node_modules目录")
        print("正在安装前端依赖...")
        try:
            subprocess.run(['npm', 'install'], check=True)
            print("✅ 前端依赖安装完成")
        except subprocess.CalledProcessError:
            print("❌ 前端依赖安装失败")
            return False
        except FileNotFoundError:
            print("❌ 未找到npm命令，请先安装Node.js")
            return False
    else:
        print("✅ 前端依赖已存在")
    
    return True

def start_backend():
    """启动后端服务"""
    print("\n🚀 启动后端服务...")
    try:
        # 初始化数据库
        from database import db
        print("✅ 数据库初始化完成")
        
        # 启动Flask应用
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ 后端启动失败: {e}")

def start_frontend():
    """启动前端服务"""
    print("\n🎨 启动前端服务...")
    try:
        subprocess.run(['npm', 'run', 'dev'], check=True)
    except subprocess.CalledProcessError:
        print("❌ 前端启动失败")
    except FileNotFoundError:
        print("❌ 未找到npm命令")

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_python_dependencies():
        sys.exit(1)
    
    if not check_node_dependencies():
        sys.exit(1)
    
    print("\n🎯 系统信息:")
    print("  📡 后端服务: http://localhost:5000")
    print("  🎨 前端应用: http://localhost:3000")
    print("  📚 API文档: http://localhost:5000/api/health")
    print("\n🔑 默认登录账号:")
    print("  用户名: admin / 密码: admin123")
    print("  用户名: user  / 密码: user123")
    print("\n" + "=" * 60)
    
    # 启动后端服务（在新线程中）
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # 等待后端启动
    print("⏳ 等待后端服务启动...")
    time.sleep(3)
    
    # 启动前端服务
    try:
        start_frontend()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")

if __name__ == '__main__':
    main()