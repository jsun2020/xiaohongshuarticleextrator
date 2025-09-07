#!/usr/bin/env python3
"""
Simple API Server for Local Testing
Simplified version focusing on stability
"""
import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import importlib.util
import threading

# Setup paths and environment
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))
os.environ['JWT_SECRET'] = 'xiaohongshu_app_secret_key_2024_local_dev'

class SimpleAPIHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[API] {format % args}")
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Length', '0')
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
    
    def _handle_request(self, method):
        """Handle all request types"""
        try:
            # Parse request
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # Read body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b''
            
            print(f"[API] {method} {path}")
            
            # Route the request
            response = self._route_request(method, path, dict(self.headers), body, query_params)
            print(f"[API] Response: {response is not None}")
            
            if response:
                self._send_response(response)
            else:
                self._send_error(404, 'Endpoint not found')
                
        except Exception as e:
            print(f"[API] Error handling request: {str(e)}")
            self._send_error(500, f'Server error: {str(e)}')
    
    def _route_request(self, method, path, headers, body, query):
        """Route request to appropriate handler"""
        
        # Handle root API path
        if path == '/api' or path == '/api/':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': True,
                    'message': 'Xiaohongshu API Server - Simple Version',
                    'endpoints': [
                        'POST /api/auth/login',
                        'POST /api/auth/register', 
                        'GET /api/auth/status',
                        'GET /api/health'
                    ]
                })
            }
        
        # Route mappings
        routes = {
            '/api/health': self._handle_health,
            '/api/auth': self._handle_auth,
            # Legacy auth endpoints (for backward compatibility)
            '/api/auth/login': lambda m, h, b, q: self._handle_auth_legacy(m, h, b, q, 'login'),
            '/api/auth/register': lambda m, h, b, q: self._handle_auth_legacy(m, h, b, q, 'register'),
            '/api/auth/logout': lambda m, h, b, q: self._handle_auth_legacy(m, h, b, q, 'logout'),
            '/api/auth/status': lambda m, h, b, q: self._handle_auth_legacy(m, h, b, q, 'status'),
            '/api/xiaohongshu/note': self._handle_xiaohongshu_note,
            '/api/xiaohongshu/notes': self._handle_xiaohongshu_notes,
            '/api/xiaohongshu/recreate': self._handle_xiaohongshu_recreate,
            '/api/xiaohongshu/recreate/history': self._handle_recreate_history,
            '/api/deepseek/config': self._handle_deepseek_config,
            '/api/deepseek/test': self._handle_deepseek_test,
        }
        
        # Handle delete endpoints with IDs
        if path.startswith('/api/xiaohongshu/notes/') and method == 'DELETE':
            return self._handle_xiaohongshu_notes_delete(method, headers, body, query, path)
        elif path.startswith('/api/xiaohongshu/recreate/history/') and method == 'DELETE':
            return self._handle_recreate_history_delete(method, headers, body, query, path)
        
        handler_func = routes.get(path)
        if handler_func:
            return handler_func(method, headers, body, query)
        
        return None
    
    def _handle_health(self, method, headers, body, query):
        """Handle health check"""
        if method != 'GET':
            return {'statusCode': 405, 'headers': {'Content-Type': 'application/json'}, 'body': '{"error": "Method not allowed"}'}
        
        try:
            from health import handler
            mock_request = self._create_mock_request(method, headers, body, query)
            return handler(mock_request)
        except Exception as e:
            return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': f'{{"error": "{str(e)}"}}'}
    
    def _handle_auth(self, method, headers, body, query):
        """Handle consolidated auth endpoint"""
        try:
            from auth import handler
            mock_request = self._create_mock_request(method, headers, body, query)
            return handler(mock_request)
        except Exception as e:
            print(f"[API] Auth error: {str(e)}")
            return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': f'{{"error": "{str(e)}"}}'}
    
    def _handle_auth_legacy(self, method, headers, body, query, action):
        """Handle legacy auth endpoints by routing to consolidated auth with action"""
        try:
            # Add action to query parameters
            query['action'] = [action]
            from auth import handler
            mock_request = self._create_mock_request(method, headers, body, query)
            return handler(mock_request)
        except Exception as e:
            print(f"[API] Auth legacy error: {str(e)}")
            return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': f'{{"error": "{str(e)}"}}'}
    
    def _handle_xiaohongshu_note(self, method, headers, body, query):
        """Handle xiaohongshu note collection"""
        if method != 'POST':
            return {'statusCode': 405, 'headers': {'Content-Type': 'application/json'}, 'body': '{"error": "Method not allowed"}'}
        
        try:
            from xiaohongshu_note import handler
            mock_request = self._create_mock_request(method, headers, body, query)
            return handler(mock_request)
        except Exception as e:
            return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': f'{{"error": "{str(e)}"}}'}
    
    def _handle_xiaohongshu_notes(self, method, headers, body, query):
        """Handle xiaohongshu notes list"""
        if method != 'GET':
            return {'statusCode': 405, 'headers': {'Content-Type': 'application/json'}, 'body': '{"error": "Method not allowed"}'}
        
        try:
            from xiaohongshu_notes import handler
            mock_request = self._create_mock_request(method, headers, body, query)
            return handler(mock_request)
        except Exception as e:
            return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': f'{{"error": "{str(e)}"}}'}
    
    def _handle_xiaohongshu_recreate(self, method, headers, body, query):
        """Handle xiaohongshu recreate"""
        if method != 'POST':
            return {'statusCode': 405, 'headers': {'Content-Type': 'application/json'}, 'body': '{"error": "Method not allowed"}'}
        
        try:
            from xiaohongshu_recreate import handler
            mock_request = self._create_mock_request(method, headers, body, query)
            return handler(mock_request)
        except Exception as e:
            return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': f'{{"error": "{str(e)}"}}'}
    
    def _handle_recreate_history(self, method, headers, body, query):
        """Handle recreate history"""
        if method != 'GET':
            return {'statusCode': 405, 'headers': {'Content-Type': 'application/json'}, 'body': '{"error": "Method not allowed"}'}
        
        try:
            from recreate_history import handler
            mock_request = self._create_mock_request(method, headers, body, query)
            return handler(mock_request)
        except Exception as e:
            return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': f'{{"error": "{str(e)}"}}'}
    
    def _handle_deepseek_config(self, method, headers, body, query):
        """Handle deepseek config"""
        if method not in ['GET', 'POST']:
            return {'statusCode': 405, 'headers': {'Content-Type': 'application/json'}, 'body': '{"error": "Method not allowed"}'}
        
        try:
            from deepseek_config import handler
            mock_request = self._create_mock_request(method, headers, body, query)
            return handler(mock_request)
        except Exception as e:
            return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': f'{{"error": "{str(e)}"}}'}
    
    def _handle_deepseek_test(self, method, headers, body, query):
        """Handle deepseek test"""
        if method != 'POST':
            return {'statusCode': 405, 'headers': {'Content-Type': 'application/json'}, 'body': '{"error": "Method not allowed"}'}
        
        try:
            from deepseek_test import handler
            mock_request = self._create_mock_request(method, headers, body, query)
            return handler(mock_request)
        except Exception as e:
            return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': f'{{"error": "{str(e)}"}}'}
    
    def _handle_xiaohongshu_notes_delete(self, method, headers, body, query, path):
        """Handle xiaohongshu notes delete"""
        try:
            from xiaohongshu_notes_delete import handler
            mock_request = self._create_mock_request(method, headers, body, query)
            mock_request.url = path  # Update URL to include the ID
            return handler(mock_request)
        except Exception as e:
            return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': f'{{"error": "{str(e)}"}}'}
    
    def _handle_recreate_history_delete(self, method, headers, body, query, path):
        """Handle recreate history delete"""
        try:
            from recreate_history_delete import handler
            mock_request = self._create_mock_request(method, headers, body, query)
            mock_request.url = path  # Update URL to include the ID
            return handler(mock_request)
        except Exception as e:
            return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': f'{{"error": "{str(e)}"}}'}
    
    def _create_mock_request(self, method, headers, body, query):
        """Create mock request object for handlers"""
        class MockRequest:
            def __init__(self, method, headers, body, query):
                self.method = method
                self.headers = headers
                self.body = body
                self.query = query
                self.url = 'http://localhost:3001/api/test'
        
        return MockRequest(method, headers, body, query)
    
    def _send_response(self, response_data):
        """Send HTTP response"""
        try:
            status_code = response_data.get('statusCode', 200)
            headers = response_data.get('headers', {})
            body = response_data.get('body', '{}')
            
            self.send_response(status_code)
            
            # Set default headers
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            
            # Set custom headers (except duplicates)
            for key, value in headers.items():
                if key.lower() not in ['content-type', 'access-control-allow-origin', 
                                     'access-control-allow-methods', 'access-control-allow-headers']:
                    if isinstance(value, list):
                        for v in value:
                            self.send_header(key, v)
                    else:
                        self.send_header(key, value)
            
            self.end_headers()
            self.wfile.write(body.encode('utf-8'))
            
        except Exception as e:
            print(f"[API] Error sending response: {str(e)}")
            self._send_error(500, "Response error")
    
    def _send_error(self, status_code, message):
        """Send error response"""
        try:
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_body = json.dumps({'success': False, 'error': message})
            self.wfile.write(error_body.encode('utf-8'))
        except:
            pass

def start_simple_api_server(port=3002):
    """Start the simple API server"""
    try:
        print(f"[DEBUG] Starting server on port {port}...")
        server = HTTPServer(('localhost', port), SimpleAPIHandler)
        print("=" * 50)
        print(f"Simple API Server Started")
        print(f"URL: http://localhost:{port}")
        print("Endpoints:")
        print("  POST /api/auth/login")
        print("  POST /api/auth/register") 
        print("  GET /api/auth/status")
        print("  GET /api/health")
        print("=" * 50)
        print("Press Ctrl+C to stop")
        
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.shutdown()
    except Exception as e:
        print(f"Server error: {str(e)}")

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3002
    start_simple_api_server(port)