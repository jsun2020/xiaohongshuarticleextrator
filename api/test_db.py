# api/test_db.py
import os
import json
import psycopg2  # 确保这个包在 requirements.txt 中
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        db_url = os.environ.get("DATABASE_URL")
        
        if not db_url:
            self.send_response_and_data({
                "status": "Error",
                "message": "DATABASE_URL environment variable is not set."
            }, 500)
            return

        try:
            # 尝试连接数据库
            conn = psycopg2.connect(db_url)
            
            # 创建一个 cursor 对象
            cur = conn.cursor()
            
            # 执行一个简单的查询
            cur.execute("SELECT version();")
            
            # 获取查询结果
            db_version = cur.fetchone()
            
            # 关闭 cursor 和 connection
            cur.close()
            conn.close()
            
            self.send_response_and_data({
                "status": "Success",
                "message": "Database connection successful!",
                "db_version": db_version[0]
            }, 200)

        except Exception as e:
            # 如果连接失败，返回详细的错误信息
            self.send_response_and_data({
                "status": "Error",
                "message": "Failed to connect to the database.",
                "error_type": type(e).__name__,
                "error_details": str(e)
            }, 500)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def send_response_and_data(self, data, status_code):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))