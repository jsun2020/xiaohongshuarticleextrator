#!/usr/bin/env python3
"""
Local API Testing Script
Tests all Vercel serverless functions locally
"""
import requests
import json
import time
import os
from typing import Dict, Optional

# Configuration
BASE_URL = "http://localhost:3001/api"
TEST_USER = {
    "username": "testuser123",
    "password": "testpass123",
    "email": "test@example.com",
    "nickname": "Test User"
}

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.user_id = None
    
    def log(self, message: str, status: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> requests.Response:
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        
        # Default headers
        req_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add auth header if token available
        if self.token:
            req_headers["Authorization"] = f"Bearer {self.token}"
        
        # Add custom headers
        if headers:
            req_headers.update(headers)
        
        try:
            if method.upper() == "GET":
                return self.session.get(url, headers=req_headers)
            elif method.upper() == "POST":
                return self.session.post(url, json=data, headers=req_headers)
            elif method.upper() == "DELETE":
                return self.session.delete(url, headers=req_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            return None
    
    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        self.log("Testing health check endpoint...")
        
        response = self.make_request("GET", "/health")
        if not response:
            return False
        
        if response.status_code == 200:
            self.log("Health check passed", "SUCCESS")
            return True
        else:
            self.log(f"Health check failed: {response.status_code}", "ERROR")
            return False
    
    def test_user_registration(self) -> bool:
        """Test user registration"""
        self.log("Testing user registration...")
        
        response = self.make_request("POST", "/auth/register", TEST_USER)
        if not response:
            return False
        
        if response.status_code in [200, 201]:
            data = response.json()
            if data.get('success'):
                self.log("User registration successful", "SUCCESS")
                return True
            else:
                self.log(f"Registration failed: {data.get('error')}", "ERROR")
                return False
        else:
            self.log(f"Registration failed: {response.status_code}", "ERROR")
            return False
    
    def test_user_login(self) -> bool:
        """Test user login and get token"""
        self.log("Testing user login...")
        
        login_data = {
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if not response:
            return False
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.token = data.get('token')
                self.user_id = data.get('user', {}).get('id')
                self.log("User login successful", "SUCCESS")
                return True
            else:
                self.log(f"Login failed: {data.get('error')}", "ERROR")
                return False
        else:
            self.log(f"Login failed: {response.status_code}", "ERROR")
            return False
    
    def test_auth_status(self) -> bool:
        """Test authentication status check"""
        self.log("Testing auth status check...")
        
        response = self.make_request("GET", "/auth/status")
        if not response:
            return False
        
        if response.status_code == 200:
            data = response.json()
            if data.get('logged_in'):
                self.log("Auth status check passed", "SUCCESS")
                return True
            else:
                self.log("User not logged in according to status", "WARNING")
                return True  # This is still a valid response
        else:
            self.log(f"Auth status check failed: {response.status_code}", "ERROR")
            return False
    
    def test_deepseek_config(self) -> bool:
        """Test DeepSeek configuration endpoints"""
        self.log("Testing DeepSeek configuration...")
        
        # Test GET config
        response = self.make_request("GET", "/deepseek/config")
        if not response:
            return False
        
        if response.status_code == 200:
            self.log("DeepSeek config GET successful", "SUCCESS")
        else:
            self.log(f"DeepSeek config GET failed: {response.status_code}", "ERROR")
            return False
        
        # Test POST config (update)
        config_data = {
            "api_key": "test_api_key_123",
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = self.make_request("POST", "/deepseek/config", config_data)
        if not response:
            return False
        
        if response.status_code == 200:
            self.log("DeepSeek config POST successful", "SUCCESS")
            return True
        else:
            self.log(f"DeepSeek config POST failed: {response.status_code}", "ERROR")
            return False
    
    def test_xiaohongshu_endpoints(self) -> bool:
        """Test Xiaohongshu-related endpoints"""
        self.log("Testing Xiaohongshu endpoints...")
        
        # Test getting notes list (should be empty initially)
        response = self.make_request("GET", "/xiaohongshu/notes")
        if not response:
            return False
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.log("Notes list retrieval successful", "SUCCESS")
                return True
            else:
                self.log(f"Notes list failed: {data.get('error')}", "ERROR")
                return False
        else:
            self.log(f"Notes list failed: {response.status_code}", "ERROR")
            return False
    
    def test_recreation_history(self) -> bool:
        """Test recreation history endpoints"""
        self.log("Testing recreation history...")
        
        response = self.make_request("GET", "/xiaohongshu/recreate/history")
        if not response:
            return False
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.log("Recreation history retrieval successful", "SUCCESS")
                return True
            else:
                self.log(f"Recreation history failed: {data.get('error')}", "ERROR")
                return False
        else:
            self.log(f"Recreation history failed: {response.status_code}", "ERROR")
            return False
    
    def test_user_logout(self) -> bool:
        """Test user logout"""
        self.log("Testing user logout...")
        
        response = self.make_request("POST", "/auth/logout")
        if not response:
            return False
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.token = None
                self.user_id = None
                self.log("User logout successful", "SUCCESS")
                return True
            else:
                self.log(f"Logout failed: {data.get('error')}", "ERROR")
                return False
        else:
            self.log(f"Logout failed: {response.status_code}", "ERROR")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all API tests"""
        self.log("Starting comprehensive API tests...", "INFO")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Auth Status", self.test_auth_status),
            ("DeepSeek Config", self.test_deepseek_config),
            ("Xiaohongshu Endpoints", self.test_xiaohongshu_endpoints),
            ("Recreation History", self.test_recreation_history),
            ("User Logout", self.test_user_logout)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"Running test: {test_name}")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"Test {test_name} crashed: {str(e)}", "ERROR")
                failed += 1
            
            time.sleep(1)  # Small delay between tests
        
        self.log(f"Tests completed: {passed} passed, {failed} failed", "INFO")
        return failed == 0

def main():
    """Main test function"""
    print("=" * 60)
    print("Local API Testing Script")
    print("=" * 60)
    
    # Check if local server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print("OK: Local server is running")
    except requests.exceptions.RequestException:
        print("ERROR: Local server is not running!")
        print("Please start the development server with: vercel dev")
        return
    
    # Run tests
    tester = APITester(BASE_URL)
    success = tester.run_all_tests()
    
    print("=" * 60)
    if success:
        print("All tests passed! Your API is ready for deployment.")
    else:
        print("Some tests failed. Please check the errors above.")
    print("=" * 60)

if __name__ == "__main__":
    main()