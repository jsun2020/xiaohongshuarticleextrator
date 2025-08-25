/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: [
      'sns-avatar-qc.xhscdn.com',
      'sns-webpic-qc.xhscdn.com',
      'ci.xiaohongshu.com',
      'sns-img-bd.xhscdn.com',
      'sns-img-qc.xhscdn.com'
    ],
    unoptimized: true
  },
  async rewrites() {
    // 只在开发环境中重定向到Flask服务器
    if (process.env.NODE_ENV === 'development' && process.env.USE_FLASK_API === 'true') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:5000/api/:path*'
        }
      ]
    }
    // 生产环境和Vercel环境不需要重定向
    return []
  }
}

module.exports = nextConfig