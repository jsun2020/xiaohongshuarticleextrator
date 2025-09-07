#!/usr/bin/env python3
"""
Local API Server for Testing Serverless Functions
Simulates Vercel's serverless environment locally
"""
import sys
import os
import json
import importlib.util
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# Add paths for imports
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

# Set environment variables
os.environ['JWT_SECRET'] = 'xiaohongshu_app_secret_key_2024_local_dev'

class MockRequest:
    """Mock request object for serverless functions"""
    def __init__(self, method: str, path: str, headers: dict, body: bytes, query: dict):
        self.method = method
        self.url = path
        self.headers = headers
        self.body = body
        self.query = query

class APIHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        self._handle_request('GET')
    
    def do_POST(self):
        """Handle POST requests"""
        self._handle_request('POST')
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        self._handle_request('DELETE')
    
    def _handle_request(self, method: str):
        """Handle all request types"""
        try:
            # Parse URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query = parse_qs(parsed_url.query)
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b''
            
            # Route to appropriate handler
            response = self._route_request(method, path, dict(self.headers), body, query)
            
            if response:
                # Send response
                status_code = response.get('statusCode', 200)
                response_headers = response.get('headers', {})
                response_body = response.get('body', '{}')
                
                self.send_response(status_code)
                self.send_header('Content-Type', 'application/json')
                self._send_cors_headers()
                
                for key, value in response_headers.items():
                    if key.lower() not in ['content-type', 'access-control-allow-origin', 
                                         'access-control-allow-methods', 'access-control-allow-headers']:
                        self.send_header(key, value)
                
                self.end_headers()
                self.wfile.write(response_body.encode('utf-8'))
            else:
                self._send_error(404, 'Endpoint not found')
        
        except Exception as e:
            self._send_error(500, f'Server error: {str(e)}')
    
    def _route_request(self, method: str, path: str, headers: dict, body: bytes, query: dict):
        """Route request to appropriate serverless function"""
        # Handle root API path
        if path == '/api' or path == '/api/':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': True,
                    'message': 'Xiaohongshu API Server',
                    'version': '1.0.0',
                    'endpoints': [
                        'GET /api/health',
                        'POST /api/auth/register',
                        'POST /api/auth/login',
                        'GET /api/auth/status',
                        'POST /api/xiaohongshu/note',
                        'GET /api/xiaohongshu/notes',
                        'POST /api/xiaohongshu/recreate',
                        'GET /api/deepseek/config',
                        'POST /api/deepseek/config'
                    ]
                })
            }
        
        # Map paths to API files
        route_map = {
            '/api/health': 'health.py',
            '/api/auth': 'auth.py',
            '/api/auth/login': 'auth.py',
            '/api/auth/register': 'auth.py',
            '/api/auth/logout': 'auth.py', 
            '/api/auth/status': 'auth.py',
            '/api/xiaohongshu/note': 'xiaohongshu_note.py',
            '/api/xiaohongshu/notes': 'xiaohongshu_notes.py',
            '/api/xiaohongshu/recreate': 'xiaohongshu_recreate.py',
            '/api/xiaohongshu/recreate/history': 'recreate_history.py',
            '/api/deepseek/config': 'deepseek_config.py',
            '/api/deepseek/test': 'deepseek_test.py'
        }
        
        # Handle delete endpoints with IDs
        if path.startswith('/api/xiaohongshu/notes/') and method == 'DELETE':
            api_file = 'xiaohongshu_notes_delete.py'
        elif path.startswith('/api/xiaohongshu/recreate/history/') and method == 'DELETE':
            api_file = 'recreate_history_delete.py'
        else:
            api_file = route_map.get(path)
        
        if not api_file:
            return None
        
        try:
            # Load the serverless function
            api_path = os.path.join(os.path.dirname(__file__), 'api', api_file)
            spec = importlib.util.spec_from_file_location("handler_module", api_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Create mock request
            mock_request = MockRequest(method, path, headers, body, query)
            
            # Call the handler
            response = module.handler(mock_request)
            return response
        
        except Exception as e:
            print(f"Error in {api_file}: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'success': False, 'error': f'Handler error: {str(e)}'})
            }
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        
        error_response = {'success': False, 'error': message}
        self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[{self.address_string()}] {format % args}")

def start_api_server(port=3002):
    """Start the local API server"""
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, APIHandler)
    
    print("=" * 60)
    print("Local API Server Started")
    print(f"Server: http://localhost:{port}")
    print(f"API Base: http://localhost:{port}/api")
    print("=" * 60)
    print("Available endpoints:")
    print("  GET  /api/health")
    print("  POST /api/auth/register")
    print("  POST /api/auth/login")
    print("  GET  /api/auth/status")
    print("  POST /api/xiaohongshu/note")
    print("  GET  /api/xiaohongshu/notes")
    print("  POST /api/xiaohongshu/recreate")
    print("  GET  /api/deepseek/config")
    print("  POST /api/deepseek/config")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        httpd.shutdown()

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3002
    start_api_server(port)