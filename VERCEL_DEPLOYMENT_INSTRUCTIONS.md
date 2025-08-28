# Vercel Deployment Instructions

## Prerequisites
1. Vercel account
2. Neon PostgreSQL database account
3. GitHub repository with your code

## Step 1: Setup Neon Database
1. Go to https://neon.tech and create an account
2. Create a new project
3. Copy the connection string (should look like):
   ```
   postgresql://username:password@ep-hostname.region.neon.tech/database?sslmode=require
   ```

## Step 2: Deploy to Vercel

### Method 1: Via Vercel Dashboard (Recommended)
1. Go to https://vercel.com/dashboard
2. Click "New Project"
3. Connect your GitHub repository
4. Configure Project:
   - Framework Preset: Next.js
   - Root Directory: `.` (leave blank)
   - Build Command: `npm run build`
   - Output Directory: `.next` (auto-detected)

### Method 2: Via Vercel CLI
```bash
npm install -g vercel
vercel --prod
```

## Step 3: Configure Environment Variables in Vercel
1. In your Vercel project dashboard, go to "Settings" → "Environment Variables"
2. Add these variables:

### Required Variables:
```
DATABASE_URL = postgresql://username:password@ep-hostname.region.neon.tech/database?sslmode=require
JWT_SECRET = your_random_jwt_secret_string_here
```

### Optional Variables:
```
DEEPSEEK_API_KEY = your_deepseek_api_key
DEEPSEEK_BASE_URL = https://api.deepseek.com
```

## Step 4: Verify Deployment
1. Check that all API endpoints are working:
   - `/api/health` - Should return health status
   - `/api/auth/status` - Authentication check
   - `/api/xiaohongshu_notes_list` - Notes listing

2. Common issues and solutions:
   - **Database connection errors**: Verify DATABASE_URL is correct and Neon database is active
   - **Build errors**: Check that all dependencies are in requirements.txt
   - **Import errors**: Ensure Python modules are compatible with Vercel's Python 3.9 runtime

## Step 5: Test the Application
1. Visit your Vercel deployment URL
2. Test user registration/login
3. Test data collection and content management features
4. Check that recreate history displays correctly

## Troubleshooting

### Common Error: "psycopg2 import error"
- Solution: Already fixed in requirements.txt with `psycopg2-binary==2.9.9`

### Common Error: "Database connection refused"
- Check DATABASE_URL format
- Ensure Neon database is active (not hibernated)
- Verify SSL connection settings

### Common Error: "Function timeout"
- Increase timeout in vercel.json (already configured)
- Optimize database queries
- Consider using connection pooling

### Common Error: "Module not found"
- Verify all dependencies are in requirements.txt
- Check Python path configuration in vercel.json

## Files Modified for Vercel Compatibility
1. `vercel.json` - Runtime configuration
2. `api/requirements.txt` - Python dependencies
3. `api/_database.py` - Database connection handling
4. `.env.example` - Environment variable examples

## Database Schema
The application will automatically create the required tables on first run:
- `users` - User accounts
- `notes` - Collected xiaohongshu notes
- `recreate_history` - AI recreate history

## Performance Optimization
- Database queries are optimized for serverless functions
- Connection pooling is handled by Neon
- API responses are cached where appropriate

## Security
- All database connections use SSL
- JWT tokens for authentication
- Environment variables for sensitive data
- CORS configured for production domain