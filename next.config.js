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
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5000/api/:path*'
      }
    ]
  }
}

module.exports = nextConfig