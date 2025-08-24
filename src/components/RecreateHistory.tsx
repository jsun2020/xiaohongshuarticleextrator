'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { recreateAPI } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { Loader2, RefreshCw, Trash2, Copy, History, ArrowRight } from 'lucide-react'

interface RecreateHistoryItem {
  id: number
  original_note_id: string
  original_title: string
  original_content: string
  new_title: string
  new_content: string
  created_at: string
  note_title: string
  author_nickname: string
}

export default function RecreateHistory() {
  const [history, setHistory] = useState<RecreateHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [total, setTotal] = useState(0)
  const [selectedItem, setSelectedItem] = useState<RecreateHistoryItem | null>(null)

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async (offset = 0, append = false) => {
    try {
      if (!append) setLoading(true)
      else setLoadingMore(true)

      const response = await recreateAPI.getHistory(20, offset)
      if (response.data.success) {
        const newHistory = response.data.data.history
        setHistory(append ? [...history, ...newHistory] : newHistory)
        setTotal(response.data.data.total)
        setHasMore(response.data.data.has_more)
        
        // 默认选择第一个项目
        if (!append && newHistory.length > 0 && !selectedItem) {
          setSelectedItem(newHistory[0])
        }
      }
    } catch (error) {
      console.error('加载历史记录失败:', error)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  const handleRefresh = () => {
    setSelectedItem(null)
    loadHistory()
  }

  const handleLoadMore = () => {
    loadHistory(history.length, true)
  }

  const handleDelete = async (historyId: number) => {
    if (!confirm('确定要删除这条历史记录吗？')) return

    try {
      const response = await recreateAPI.deleteHistory(historyId)
      if (response.data.success) {
        const newHistory = history.filter(item => item.id !== historyId)
        setHistory(newHistory)
        setTotal(total - 1)
        
        // 如果删除的是当前选中项，选择下一个
        if (selectedItem?.id === historyId) {
          setSelectedItem(newHistory.length > 0 ? newHistory[0] : null)
        }
      }
    } catch (error) {
      console.error('删除失败:', error)
      alert('删除失败，请重试')
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-xiaohongshu-red" />
          <p className="text-gray-600">加载历史记录中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 统计信息和操作栏 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <History className="h-5 w-5 text-xiaohongshu-red" />
                <span>二创历史</span>
              </CardTitle>
              <CardDescription>
                共 {total} 条二创记录，支持对比查看和管理
              </CardDescription>
            </div>
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={loading}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              刷新
            </Button>
          </div>
        </CardHeader>
      </Card>

      {history.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <History className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-500">暂无二创历史记录</p>
            <p className="text-sm text-gray-400 mt-2">
              请先在"内容管理"页面进行AI二创
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 左侧历史列表 */}
          <div className="lg:col-span-1 space-y-4">
            <h3 className="font-semibold text-lg">历史记录</h3>
            <div className="space-y-2 max-h-[600px] overflow-y-auto custom-scrollbar">
              {history.map((item) => (
                <Card
                  key={item.id}
                  className={`cursor-pointer transition-all hover:shadow-md ${
                    selectedItem?.id === item.id ? 'ring-2 ring-xiaohongshu-red' : ''
                  }`}
                  onClick={() => setSelectedItem(item)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm truncate mb-1">
                          {item.new_title}
                        </h4>
                        <p className="text-xs text-gray-500 mb-2">
                          来源: {item.note_title || '未知笔记'}
                        </p>
                        <p className="text-xs text-gray-400">
                          {formatDate(item.created_at)}
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(item.id)
                        }}
                        className="ml-2 text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
              
              {hasMore && (
                <div className="text-center pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                  >
                    {loadingMore ? (
                      <>
                        <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                        加载中...
                      </>
                    ) : (
                      '加载更多'
                    )}
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* 右侧详情对比 */}
          <div className="lg:col-span-2">
            {selectedItem ? (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-lg">内容对比</h3>
                  <div className="text-sm text-gray-500">
                    创建时间: {formatDate(selectedItem.created_at)}
                  </div>
                </div>

                {/* 标题对比 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">标题对比</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium text-gray-700">原始标题</label>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => copyToClipboard(selectedItem.original_title)}
                          >
                            <Copy className="h-3 w-3 mr-1" />
                            复制
                          </Button>
                        </div>
                        <div className="p-3 bg-gray-50 rounded-lg border">
                          <p className="text-sm">{selectedItem.original_title}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            字符数: {selectedItem.original_title.length}
                          </p>
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium text-gray-700">AI二创标题</label>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => copyToClipboard(selectedItem.new_title)}
                          >
                            <Copy className="h-3 w-3 mr-1" />
                            复制
                          </Button>
                        </div>
                        <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                          <p className="text-sm font-medium">{selectedItem.new_title}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            字符数: {selectedItem.new_title.length}
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* 内容对比 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">内容对比</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium text-gray-700">原始内容</label>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => copyToClipboard(selectedItem.original_content)}
                          >
                            <Copy className="h-3 w-3 mr-1" />
                            复制
                          </Button>
                        </div>
                        <div className="p-3 bg-gray-50 rounded-lg border h-64 overflow-y-auto custom-scrollbar">
                          <p className="text-sm whitespace-pre-wrap">{selectedItem.original_content}</p>
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium text-gray-700">AI二创内容</label>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => copyToClipboard(selectedItem.new_content)}
                          >
                            <Copy className="h-3 w-3 mr-1" />
                            复制
                          </Button>
                        </div>
                        <div className="p-3 bg-green-50 rounded-lg border border-green-200 h-64 overflow-y-auto custom-scrollbar">
                          <p className="text-sm whitespace-pre-wrap">{selectedItem.new_content}</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* 元信息 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">记录信息</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <label className="font-medium text-gray-700">笔记ID</label>
                        <p className="text-gray-600 font-mono text-xs">
                          {selectedItem.original_note_id || '未知'}
                        </p>
                      </div>
                      <div>
                        <label className="font-medium text-gray-700">原笔记标题</label>
                        <p className="text-gray-600 truncate">
                          {selectedItem.note_title || '未知'}
                        </p>
                      </div>
                      <div>
                        <label className="font-medium text-gray-700">原作者</label>
                        <p className="text-gray-600">
                          {selectedItem.author_nickname || '未知'}
                        </p>
                      </div>
                      <div>
                        <label className="font-medium text-gray-700">二创时间</label>
                        <p className="text-gray-600">
                          {formatDate(selectedItem.created_at)}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card>
                <CardContent className="py-12 text-center">
                  <ArrowRight className="h-12 w-12 mx-auto mb-4 text-gray-300 rotate-180" />
                  <p className="text-gray-500">请从左侧选择一条历史记录查看详情</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  )
}