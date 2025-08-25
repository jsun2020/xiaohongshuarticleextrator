#!/usr/bin/env python3
"""
Direct Function Testing
Test serverless functions directly without Vercel dev server
"""
import sys
import os
import json
from typing import Dict

# Add project paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

# Mock request object for testing
class MockRequest:
    def __init__(self, method: str = "GET", body: bytes = b"", headers: Dict = None, query: Dict = None):
        self.method = method
        self.body = body
        self.headers = headers or {}
        self.query = query or {}
        self.url = "http://localhost:3000/api/test"

def test_health_endpoint():
    """Test health endpoint directly"""
    print("Testing health endpoint...")
    
    try:
        # Import the health function
        from api.health import handler
        
        # Create mock request
        request = MockRequest("GET")
        
        # Call the handler
        response = handler(request)
        
        if isinstance(response, dict):
            print("OK: Health endpoint response:", json.dumps(response, indent=2, ensure_ascii=False))
            return True
        else:
            print("ERROR: Invalid response format")
            return False
    except Exception as e:
        print(f"ERROR: Health endpoint error: {str(e)}")
        return False

def test_auth_register():
    """Test user registration directly"""
    print("\nTesting user registration...")
    
    try:
        from api.auth_register import handler
        
        # Mock registration data
        user_data = {
            "username": "testuser123",
            "password": "testpass123",
            "email": "test@example.com",
            "nickname": "Test User"
        }
        
        request = MockRequest(
            "POST", 
            json.dumps(user_data).encode('utf-8')
        )
        
        response = handler(request)
        
        if isinstance(response, dict):
            print("OK: Registration response:", json.dumps(response, indent=2, ensure_ascii=False))
            return True
        else:
            print("ERROR: Invalid response format")
            return False
    except Exception as e:
        print(f"ERROR: Registration error: {str(e)}")
        return False

def test_utils_functions():
    """Test utility functions"""
    print("\nTesting utility functions...")
    
    try:
        from api._utils import parse_request, create_response, create_session_token
        
        # Test parse_request
        mock_req = MockRequest("POST", b'{"test": "data"}')
        parsed = parse_request(mock_req)
        print("OK: parse_request works:", parsed)
        
        # Test create_response
        response = create_response({"status": "ok"}, 200)
        print("OK: create_response works:", response)
        
        # Test create_session_token
        token = create_session_token(123)
        print("OK: create_session_token works, token length:", len(token))
        
        return True
    except Exception as e:
        print(f"ERROR: Utils error: {str(e)}")
        return False

def test_database_connection():
    """Test database initialization"""
    print("\nTesting database connection...")
    
    try:
        from api._database import db
        
        # Try to initialize database
        result = db.init_database()
        print(f"OK: Database initialization: {result}")
        
        # Try to get connection
        conn = db.get_connection()
        if conn:
            print("OK: Database connection successful")
            conn.close()
            return True
        else:
            print("ERROR: No database connection")
            return False
    except Exception as e:
        print(f"ERROR: Database error: {str(e)}")
        return False

def main():
    """Run all direct tests"""
    print("=" * 60)
    print("Direct Function Testing (No Vercel Dev Server Required)")
    print("=" * 60)
    
    # Set environment variables for testing
    os.environ['JWT_SECRET'] = 'test_secret_key_123'
    
    tests = [
        ("Utils Functions", test_utils_functions),
        ("Database Connection", test_database_connection),  
        ("Health Endpoint", test_health_endpoint),
        ("User Registration", test_auth_register),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"ERROR: Test {test_name} crashed: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("All direct tests passed! Functions are working correctly.")
        print("\nNext steps:")
        print("1. Run 'vercel login' to authenticate with Vercel")
        print("2. Run 'vercel dev' to start local development server")
        print("3. Test the full API with the test script")
    else:
        print("Some tests failed. Please check the errors above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()