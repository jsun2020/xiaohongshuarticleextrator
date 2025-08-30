'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { authAPI } from '@/lib/api'

export default function HomePage() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const response = await authAPI.getStatus()
      if (response.data.logged_in) {
        setIsAuthenticated(true)
        // User is authenticated, load the main app
      } else {
        setIsAuthenticated(false)
        // User is not authenticated, redirect to login
        router.push('/login')
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      setIsAuthenticated(false)
      router.push('/login')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 to-orange-50">
        <div className="text-center">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-xiaohongshu-red mb-4">小红书数据研究院</h1>
            <p className="text-gray-600 text-lg">笔记数据采集、二创和管理系统</p>
          </div>
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-xiaohongshu-red mx-auto mb-4"></div>
          <p className="text-gray-600">检查登录状态...</p>
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    // User is authenticated, show main dashboard or import the main app component
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 to-orange-50">
        <div className="text-center">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-xiaohongshu-red mb-4">小红书数据研究院</h1>
            <p className="text-gray-600 text-lg">笔记数据采集、二创和管理系统</p>
          </div>
          <p className="text-green-600 mb-4">✅ 登录成功</p>
          <button 
            onClick={() => {
              // Clear auth and redirect to login
              localStorage.removeItem('session_token')
              router.push('/login')
            }}
            className="px-6 py-2 bg-xiaohongshu-red text-white rounded-lg hover:bg-red-600"
          >
            退出登录
          </button>
        </div>
      </div>
    )
  }

  // This should not be reached as we redirect on !isAuthenticated
  return null
}