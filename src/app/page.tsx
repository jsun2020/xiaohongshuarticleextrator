'use client'

// Fixed API endpoints - trigger rebuild
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    // Check if we're being accessed directly (not from static homepage)
    // If so, redirect to login
    if (typeof window !== 'undefined' && window.location.pathname === '/') {
      // Small delay to prevent any routing conflicts
      setTimeout(() => {
        router.push('/login')
      }, 100)
    }
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 to-orange-50">
      <div className="text-center">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-xiaohongshu-red mb-4">小红书数据研究院</h1>
          <p className="text-gray-600 text-lg">笔记数据采集、二创和管理系统</p>
        </div>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-xiaohongshu-red mx-auto mb-4"></div>
        <p className="text-gray-600">正在跳转...</p>
      </div>
    </div>
  )
}