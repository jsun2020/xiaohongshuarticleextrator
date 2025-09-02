'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Users, FileText, Bot, Activity, Calendar, TrendingUp, RefreshCw, Home } from 'lucide-react'
import { authAPI } from '@/lib/api'
import { useRouter } from 'next/navigation'

interface AdminStats {
  total_users: number
  new_users_today: number
  active_users_today: number
  total_notes: number
  notes_today: number
  total_recreations: number
  recreations_today: number
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // 使用现有的API，添加admin_stats参数
      const response = await fetch('/api/auth_status?admin_stats=true', {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      const data = await response.json()
      
      if (data.success) {
        setStats(data.data)
      } else {
        setError(data.error || '获取数据失败')
      }
    } catch (err) {
      setError('网络错误，请稍后重试')
      console.error('获取管理员数据失败:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-xiaohongshu-red" />
          <p className="text-gray-600">加载管理数据中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
          <Button onClick={fetchStats} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            重试
          </Button>
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">暂无数据</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 页面标题 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">管理员仪表板</h1>
              <p className="text-gray-600 mt-2">网站运营数据统计</p>
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                onClick={() => router.push('/')} 
                variant="outline" 
                size="sm"
                className="border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                <Home className="h-4 w-4 mr-2" />
                返回首页
              </Button>
              <Button onClick={fetchStats} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                刷新数据
              </Button>
            </div>
          </div>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* 总用户数 */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">总用户数</CardTitle>
              <Users className="h-5 w-5 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900">{stats.total_users}</div>
              <p className="text-xs text-gray-600 mt-1">
                今日新增: <span className="font-semibold text-green-600">{stats.new_users_today}</span>
              </p>
            </CardContent>
          </Card>

          {/* 今日活跃用户 */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">今日活跃用户</CardTitle>
              <Activity className="h-5 w-5 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900">{stats.active_users_today}</div>
              <p className="text-xs text-gray-600 mt-1">
                活跃率: <span className="font-semibold">
                  {stats.total_users > 0 ? Math.round((stats.active_users_today / stats.total_users) * 100) : 0}%
                </span>
              </p>
            </CardContent>
          </Card>

          {/* 总笔记数 */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">总笔记数</CardTitle>
              <FileText className="h-5 w-5 text-xiaohongshu-red" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900">{stats.total_notes}</div>
              <p className="text-xs text-gray-600 mt-1">
                今日新增: <span className="font-semibold text-green-600">{stats.notes_today}</span>
              </p>
            </CardContent>
          </Card>

          {/* 总二创数 */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">AI二创总数</CardTitle>
              <Bot className="h-5 w-5 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900">{stats.total_recreations}</div>
              <p className="text-xs text-gray-600 mt-1">
                今日新增: <span className="font-semibold text-green-600">{stats.recreations_today}</span>
              </p>
            </CardContent>
          </Card>
        </div>

        {/* 详细统计 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 用户统计 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Users className="h-5 w-5 text-blue-600" />
                <span>用户统计</span>
              </CardTitle>
              <CardDescription>用户增长和活跃情况</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">总用户数</span>
                <span className="font-semibold">{stats.total_users}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">今日新增用户</span>
                <span className="font-semibold text-green-600">+{stats.new_users_today}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">今日活跃用户</span>
                <span className="font-semibold text-blue-600">{stats.active_users_today}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">用户活跃率</span>
                <span className="font-semibold">
                  {stats.total_users > 0 ? Math.round((stats.active_users_today / stats.total_users) * 100) : 0}%
                </span>
              </div>
            </CardContent>
          </Card>

          {/* 内容统计 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-xiaohongshu-red" />
                <span>内容统计</span>
              </CardTitle>
              <CardDescription>笔记采集和AI二创情况</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">总笔记数</span>
                <span className="font-semibold">{stats.total_notes}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">今日采集笔记</span>
                <span className="font-semibold text-green-600">+{stats.notes_today}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">AI二创总数</span>
                <span className="font-semibold">{stats.total_recreations}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">今日AI二创</span>
                <span className="font-semibold text-purple-600">+{stats.recreations_today}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">二创转化率</span>
                <span className="font-semibold">
                  {stats.total_notes > 0 ? Math.round((stats.total_recreations / stats.total_notes) * 100) : 0}%
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 页面底部信息 */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>数据更新时间: {new Date().toLocaleString('zh-CN')}</p>
          <p className="mt-1">仅管理员可查看此页面</p>
        </div>
      </div>
    </div>
  )
}