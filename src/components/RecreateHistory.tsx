'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { recreateAPI } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import { Loader2, RefreshCw, Trash2, Copy, History, ArrowRight, Wand2 } from 'lucide-react'
import VisualStoryGenerator from '@/components/VisualStoryGenerator'

// 已修正类型定义
interface RecreateHistoryItem {
  id: number
  note_id: string | number
  original_title: string
  original_content: string
  new_title: string
  new_content: string
  created_at: string
  note_title: string
  original_url?: string
}

export default function RecreateHistory() {
  
  const [history, setHistory] = useState<RecreateHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [total, setTotal] = useState(0)
  const [selectedItem, setSelectedItem] = useState<RecreateHistoryItem | null>(null)
  const [showVisualStoryGenerator, setShowVisualStoryGenerator] = useState(false)
  const [visualStoryItem, setVisualStoryItem] = useState<RecreateHistoryItem | null>(null)

  useEffect(() => {
    loadHistory()
  }, [])

  useEffect(() => {
    console.log('[FRONTEND DEBUG] History state changed, length:', history.length)
    if (history.length > 0) {
      console.log('[FRONTEND DEBUG] First history item:', history[0])
    }
  }, [history])

  const loadHistory = async (offset = 0, append = false) => {
    try {
      if (!append) setLoading(true)
      else setLoadingMore(true)

      console.log('[FRONTEND DEBUG] Loading history with offset:', offset, 'append:', append)
      const response = await recreateAPI.getHistory(20, offset)
      console.log('[FRONTEND DEBUG] API response:', response.data)
      
      if (response.data.success) {
        const newHistory = response.data.data || []
        const pagination = response.data.pagination || {}
        
        console.log('[FRONTEND DEBUG] New history length:', newHistory.length)
        console.log('[FRONTEND DEBUG] Pagination:', pagination)
        console.log('[FRONTEND DEBUG] First record:', newHistory[0])
        
        setHistory(append ? [...history, ...newHistory] : newHistory)
        setTotal(pagination.total || newHistory.length)
        setHasMore((pagination.offset + pagination.limit) < pagination.total)
        
        if (!append && newHistory.length > 0 && !selectedItem) {
          setSelectedItem(newHistory[0])
        }
        
        console.log('[FRONTEND DEBUG] History state should be updated with', newHistory.length, 'records')
      } else {
        console.error('[FRONTEND DEBUG] API returned success=false:', response.data)
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

  const handleGenerateVisualStory = (item: RecreateHistoryItem) => {
    setVisualStoryItem(item)
    setShowVisualStoryGenerator(true)
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
            {/* Debug info for empty state */}
            <div className="mt-4 p-2 bg-gray-100 rounded text-xs text-left font-mono">
              <p>Debug: history.length = {history.length}</p>
              <p>Debug: total = {total}</p>
              <p>Debug: loading = {loading.toString()}</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                          {/* 已修正 */}
                          {item.new_title}
                        </h4>
                        <p className="text-xs text-gray-500 mb-2">
                          来源: {item.note_title || '未知笔记'}
                        </p>
                        <p className="text-xs text-gray-400">
                          {formatDate(item.created_at)}
                        </p>
                      </div>
                      <div className="flex space-x-1 ml-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleGenerateVisualStory(item)
                          }}
                          className="text-purple-600 hover:text-purple-700"
                          title="生成图文故事"
                        >
                          <Wand2 className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(item.id)
                          }}
                          className="text-red-500 hover:text-red-700"
                          title="删除记录"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
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

          <div className="lg:col-span-2">
            {selectedItem ? (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-lg">内容对比</h3>
                  <div className="flex items-center space-x-4">
                    <Button
                      onClick={() => handleGenerateVisualStory(selectedItem)}
                      className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white"
                      size="sm"
                    >
                      <Wand2 className="h-4 w-4 mr-2" />
                      生成图文故事
                    </Button>
                    <div className="text-sm text-gray-500">
                      创建时间: {formatDate(selectedItem.created_at)}
                    </div>
                  </div>
                </div>

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
                          {/* 已修正 */}
                          <p className="text-sm font-medium">{selectedItem.new_title}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {/* 已修正 */}
                            字符数: {selectedItem.new_title.length}
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

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
                          {/* 已修正 */}
                          <p className="text-sm whitespace-pre-wrap">{selectedItem.new_content}</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">记录信息</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <label className="font-medium text-gray-700">笔记ID</label>
                        <p className="text-gray-600 font-mono text-xs">
                          {selectedItem.note_id || '未知'}
                        </p>
                      </div>
                      <div>
                        <label className="font-medium text-gray-700">原笔记标题</label>
                        <p className="text-gray-600 truncate">
                          {selectedItem.note_title || '未知'}
                        </p>
                      </div>
                      <div>
                        <label className="font-medium text-gray-700">原链接</label>
                        <p className="text-gray-600 truncate font-mono text-xs">
                          {selectedItem.original_url || '未知'}
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
      
      {/* Visual Story Generator Dialog */}
      <VisualStoryGenerator
        open={showVisualStoryGenerator}
        onOpenChange={setShowVisualStoryGenerator}
        historyItem={visualStoryItem}
      />
    </div>
  )
}