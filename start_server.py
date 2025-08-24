#!/usr/bin/env python3
"""
小红书笔记采集API服务器启动脚本
"""
import os
import sys
import subprocess

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import flask
        import flask_cors
        import requests
        print("✅ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False

def start_server():
    """启动Flask服务器"""
    if not check_dependencies():
        return
    
    print("🚀 正在启动小红书笔记采集API服务器...")
    print("📡 服务地址: http://localhost:5000")
    print("🔗 API文档: http://localhost:5000/api/health")
    print("⚠️  请确保前端应用在端口3000运行")
    print("=" * 50)
    
    try:
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == '__main__':
    start_server()
