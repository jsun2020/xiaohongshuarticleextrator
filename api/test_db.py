# api/test_db.py
import os
import json
import psycopg2  # 确保这个包在 requirements.txt 中

def handler(request):
    """Vercel serverless function handler"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }
        }
    
    if request.method == 'GET':
        db_url = os.environ.get("DATABASE_URL")
        
        if not db_url:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    "status": "Error",
                    "message": "DATABASE_URL environment variable is not set."
                })
            }

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
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    "status": "Success",
                    "message": "Database connection successful!",
                    "db_version": db_version[0]
                })
            }

        except Exception as e:
            # 如果连接失败，返回详细的错误信息
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    "status": "Error",
                    "message": "Failed to connect to the database.",
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                })
            }
    
    return {
        'statusCode': 405,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': 'Method not allowed'})
    }