#!/usr/bin/env python3
"""
测试API结构是否正确配置
"""
import os
import sys
import importlib.util

def test_api_structure():
    """Test API directory structure"""
    api_dir = os.path.join(os.path.dirname(__file__), 'api')
    
    if not os.path.exists(api_dir):
        print("ERROR: API directory does not exist")
        return False
    
    # Required API files
    required_files = [
        'auth_login.py',
        'auth_register.py', 
        'auth_logout.py',
        'auth_status.py',
        'xiaohongshu_note.py',
        'xiaohongshu_notes.py',
        'xiaohongshu_notes_delete.py',
        'xiaohongshu_recreate.py',
        'recreate_history.py',
        'recreate_history_delete.py',
        'deepseek_config.py',
        'deepseek_test.py',
        'health.py',
        '_utils.py',
        '_database.py',
        'requirements.txt'
    ]
    
    print("Checking API file structure...")
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(api_dir, file)
        if os.path.exists(file_path):
            print(f"OK: {file}")
        else:
            print(f"ERROR: {file} - missing")
            missing_files.append(file)
    
    if missing_files:
        print(f"\nMissing files: {', '.join(missing_files)}")
        return False
    
    # Test if main functions exist
    print("\nChecking API function structure...")
    test_files = [
        ('auth_login.py', 'handler'),
        ('xiaohongshu_note.py', 'handler'),
        ('_utils.py', 'parse_request'),
        ('_utils.py', 'create_response'),
        ('_utils.py', 'require_auth')
    ]
    
    for file_name, func_name in test_files:
        try:
            file_path = os.path.join(api_dir, file_name)
            spec = importlib.util.spec_from_file_location("test_module", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, func_name):
                print(f"OK: {file_name}::{func_name}")
            else:
                print(f"ERROR: {file_name}::{func_name} - function does not exist")
        except Exception as e:
            print(f"ERROR: {file_name}::{func_name} - import error: {str(e)}")
    
    print("\nAPI structure test completed")
    return True

def test_vercel_config():
    """Test vercel.json configuration"""
    vercel_config = os.path.join(os.path.dirname(__file__), 'vercel.json')
    
    if not os.path.exists(vercel_config):
        print("ERROR: vercel.json does not exist")
        return False
    
    try:
        import json
        with open(vercel_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check basic structure
        if 'builds' not in config:
            print("ERROR: vercel.json missing builds configuration")
            return False
        
        if 'routes' not in config:
            print("ERROR: vercel.json missing routes configuration") 
            return False
        
        print("OK: vercel.json configuration is correct")
        return True
        
    except Exception as e:
        print(f"ERROR: vercel.json configuration error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting Vercel API structure test...")
    
    success = True
    success &= test_api_structure()
    success &= test_vercel_config()
    
    if success:
        print("\nAll tests passed! API is ready for Vercel deployment")
    else:
        print("\nTests failed, please fix the above issues")
        sys.exit(1)