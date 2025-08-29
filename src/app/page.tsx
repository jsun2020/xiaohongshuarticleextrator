'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { authAPI } from '@/lib/api'
import { Loader2 } from 'lucide-react'
import MainApp from '@/components/MainApp'

interface User {
  id: number
  username: string
  nickname: string
  email: string
}

export default function HomePage() {
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<User | null>(null)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      console.log('Checking auth status...')
      const response = await fetch('/api/auth/status', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      console.log('Response status:', response.status)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('Auth response data:', data)
      
      if (data.logged_in && data.user) {
        setUser(data.user)
      } else {
        console.log('Not logged in, redirecting to login')
        router.push('/login')
      }
    } catch (error) {
      console.error('Auth check error:', error)
      setError('认证检查失败，正在跳转到登录页...')
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-xiaohongshu-red" />
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button 
            onClick={() => router.push('/login')}
            className="px-4 py-2 bg-xiaohongshu-red text-white rounded hover:bg-xiaohongshu-red/90"
          >
            前往登录
          </button>
        </div>
      </div>
    )
  }

  if (!user) {
    return null // 会被重定向到登录页
  }

  return <MainApp user={user} />
}