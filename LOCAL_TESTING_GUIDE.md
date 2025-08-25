# Local Testing Guide

This guide explains how to test your Vercel serverless functions locally before deploying.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Vercel CLI (already done)
npm install -g vercel

# Install Python dependencies for testing
pip install requests
```

### 2. Set Environment Variables

Copy the environment template:
```bash
cp .env.local .env
```

Edit `.env.local` with your values:
```bash
JWT_SECRET=xiaohongshu_app_secret_key_2024_local_dev
# DATABASE_URL=sqlite:///xiaohongshu_notes.db  # Optional for local testing
```

### 3. Start Local Development Server

```bash
# Start Vercel development server
vercel dev

# This will start:
# - Frontend on http://localhost:3000
# - API functions on http://localhost:3000/api/*
```

### 4. Test Your API

Run the automated test script:
```bash
python test_local_api.py
```

## 📊 Testing Methods

### Method 1: Automated Testing Script ✅ (Recommended)

Run comprehensive tests for all endpoints:
```bash
python test_local_api.py
```

This script tests:
- ✅ Health check endpoint
- ✅ User registration and login
- ✅ Authentication status
- ✅ DeepSeek configuration
- ✅ Xiaohongshu notes management
- ✅ Recreation history
- ✅ User logout

### Method 2: Manual Testing with curl

Test individual endpoints manually:

#### Health Check
```bash
curl http://localhost:3000/api/health
```

#### Register User
```bash
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "email": "test@example.com",
    "nickname": "Test User"
  }'
```

#### Login User
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

#### Use JWT Token
```bash
# Save token from login response
TOKEN="your_jwt_token_here"

# Test authenticated endpoint
curl http://localhost:3000/api/auth/status \
  -H "Authorization: Bearer $TOKEN"
```

### Method 3: Frontend Integration Testing

1. Start the development server: `vercel dev`
2. Open http://localhost:3000 in your browser
3. Test the complete user flow:
   - Register new account
   - Login with credentials
   - Extract Xiaohongshu notes
   - Use AI recreation features
   - Check settings and configuration

### Method 4: Postman/Insomnia Testing

Import these endpoints into your API testing tool:

**Base URL**: `http://localhost:3000/api`

**Endpoints**:
- `POST /auth/register` - Register user
- `POST /auth/login` - Login user
- `GET /auth/status` - Check login status
- `POST /auth/logout` - Logout user
- `GET /health` - Health check
- `POST /xiaohongshu/note` - Extract note
- `GET /xiaohongshu/notes` - Get notes list
- `DELETE /xiaohongshu/notes/{id}` - Delete note
- `POST /xiaohongshu/recreate` - AI recreation
- `GET /xiaohongshu/recreate/history` - Recreation history
- `GET /deepseek/config` - Get DeepSeek config
- `POST /deepseek/config` - Update DeepSeek config

## 🐛 Troubleshooting

### Common Issues

**1. "Module not found" errors**
```bash
# Make sure you're in the correct directory
cd C:\Users\sr9rfx\.claude\xiaohongshuarticleextrator

# Install missing dependencies
pip install requests PyJWT psycopg2-binary beautifulsoup4
```

**2. "Port already in use" errors**
```bash
# Kill existing processes
taskkill /f /im node.exe
# Or use different port
vercel dev --listen 3001
```

**3. Database connection errors**
- Local testing uses SQLite by default
- Data is stored in temporary directory
- For PostgreSQL testing, set DATABASE_URL in .env.local

**4. Authentication errors**
- Make sure JWT_SECRET is set in environment
- Check that cookies are being sent correctly
- Verify token format in Authorization header

### API Response Examples

**Successful Login Response**:
```json
{
  "success": true,
  "message": "登录成功",
  "user": {
    "id": 1,
    "username": "testuser",
    "nickname": "Test User",
    "email": "test@example.com"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "请先登录"
}
```

## 📈 Performance Testing

### Load Testing with curl

Test multiple concurrent requests:
```bash
# Simple load test
for i in {1..10}; do
  curl http://localhost:3000/api/health &
done
wait
```

### Memory Usage Monitoring

Monitor serverless function performance:
```bash
# Check Node.js processes
tasklist | findstr node

# Monitor memory usage during testing
```

## ✅ Ready for Production

Once local testing passes:

1. ✅ All endpoints return expected responses
2. ✅ Authentication flow works correctly
3. ✅ Database operations succeed
4. ✅ Frontend integrates properly
5. ✅ Error handling works as expected

You're ready to deploy to Vercel! 🚀

```bash
# Deploy to production
vercel --prod
```

## 📝 Notes

- Local SQLite database is temporary (resets on restart)
- Some features may behave differently in serverless environment
- Test with production database URL when possible
- Monitor Vercel function logs during testing