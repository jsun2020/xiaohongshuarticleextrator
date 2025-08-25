'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { authAPI } from '@/lib/api'
import { LogOut, User, Settings } from 'lucide-react'
import DataCollection from '@/components/DataCollection'
import NotesManagement from '@/components/NotesManagement'
import RecreateHistory from '@/components/RecreateHistory'
import DeepSeekConfig from '@/components/DeepSeekConfig'

interface User {
  id: number
  username: string
  nickname: string
  email: string
}

interface MainAppProps {
  user: User
}

export default function MainApp({ user }: MainAppProps) {
  const [activeTab, setActiveTab] = useState('collection')
  const [showConfig, setShowConfig] = useState(false)
  const router = useRouter()

  const handleLogout = async () => {
    try {
      await authAPI.logout()
      router.push('/login')
    } catch (error) {
      console.error('登出失败:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold xhs-text-gradient">
                小红书数据研究院
              </h1>
              <span className="text-sm text-gray-500">
                数据采集 · AI二创 · 智能管理
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowConfig(true)}
              >
                <Settings className="h-4 w-4 mr-2" />
                设置
              </Button>
              
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <User className="h-4 w-4" />
                <span>{user.nickname || user.username}</span>
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4 mr-2" />
                登出
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* 主要内容区域 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
            <TabsTrigger value="collection">数据采集</TabsTrigger>
            <TabsTrigger value="management">内容管理</TabsTrigger>
            <TabsTrigger value="history">二创历史</TabsTrigger>
          </TabsList>

          <TabsContent value="collection" className="space-y-6">
            <DataCollection />
          </TabsContent>

          <TabsContent value="management" className="space-y-6">
            <NotesManagement />
          </TabsContent>

          <TabsContent value="history" className="space-y-6">
            <RecreateHistory />
          </TabsContent>
        </Tabs>
      </main>

      {/* DeepSeek配置弹窗 */}
      <DeepSeekConfig 
        open={showConfig} 
        onOpenChange={setShowConfig} 
      />
    </div>
  )
}