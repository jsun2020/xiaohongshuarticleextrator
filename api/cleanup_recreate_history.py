"""
Database cleanup script for recreate_history table
Run this once to clean up corrupted data
"""
from http.server import BaseHTTPRequestHandler
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from _database import db

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Clean up recreate_history table"""
        try:
            print(f"[CLEANUP] Starting database cleanup...")
            
            # Initialize database
            db.init_database()
            
            # Get connection
            conn = db.get_connection()
            cursor = conn.cursor()
            
            try:
                # Count existing records first
                cursor.execute('SELECT COUNT(*) FROM recreate_history')
                count_before = cursor.fetchone()[0]
                print(f"[CLEANUP] Records before cleanup: {count_before}")
                
                # Delete all records
                cursor.execute('DELETE FROM recreate_history')
                
                # Reset auto increment (if SQLite)
                if not getattr(db, 'use_postgres', False):
                    cursor.execute('DELETE FROM sqlite_sequence WHERE name="recreate_history"')
                
                conn.commit()
                print(f"[CLEANUP] Successfully deleted {count_before} records")
                
                # Verify cleanup
                cursor.execute('SELECT COUNT(*) FROM recreate_history')
                count_after = cursor.fetchone()[0]
                print(f"[CLEANUP] Records after cleanup: {count_after}")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': f'Cleaned up {count_before} corrupted records',
                    'records_before': count_before,
                    'records_after': count_after
                }).encode('utf-8'))
                
            finally:
                conn.close()
                
        except Exception as e:
            print(f"[CLEANUP ERROR] {e}")
            import traceback
            print(f"[CLEANUP ERROR] Traceback: {traceback.format_exc()}")
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json') 
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode('utf-8'))