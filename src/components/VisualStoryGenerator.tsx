'use client'

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Download, Eye, Wand2, AlertTriangle, CheckCircle } from 'lucide-react'
import { visualStoryAPI } from '@/lib/api'

interface VisualStoryGeneratorProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  historyItem: {
    id: number
    new_title: string
    new_content: string
  } | null
}

interface CardData {
  title: string
  content?: string
  layout: 'a' | 'b' | 'c'
  image_url: string
}

interface VisualStoryData {
  cover_card: CardData
  content_cards: CardData[]
  html: string
}

export default function VisualStoryGenerator({ open, onOpenChange, historyItem }: VisualStoryGeneratorProps) {
  const [generating, setGenerating] = useState(false)
  const [progress, setProgress] = useState(0)
  const [visualStory, setVisualStory] = useState<VisualStoryData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'preview' | 'html'>('preview')

  const handleGenerate = async () => {
    if (!historyItem) return

    setGenerating(true)
    setProgress(0)
    setError(null)
    setVisualStory(null)

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + Math.random() * 20, 85))
      }, 500)

      const response = await visualStoryAPI.generate({
        history_id: historyItem.id,
        title: historyItem.new_title,
        content: historyItem.new_content,
        model: 'gemini-2.5-flash-image-preview'
      })

      clearInterval(progressInterval)
      setProgress(100)

      if (response.data.success) {
        // Handle new structured visual story response
        const visualStoryData = response.data.data?.visual_story
        
        if (visualStoryData) {
          // Use structured data directly from API
          setVisualStory(visualStoryData)
        } else {
          // Fallback for old format
          const htmlContent = response.data.data?.html_content || '生成的视觉故事内容'
          setVisualStory({
            cover_card: {
              title: historyItem.new_title,
              layout: 'c' as const,
              image_url: 'https://via.placeholder.com/600x800/f0f0f0/333?text=Generated+Cover'
            },
            content_cards: [
              {
                title: '生成的内容',
                content: htmlContent.length > 200 ? htmlContent.substring(0, 200) + '...' : htmlContent,
                layout: 'a' as const,
                image_url: 'https://via.placeholder.com/600x800/f0f0f0/333?text=Generated+Content'
              }
            ],
            html: htmlContent
          })
        }
      } else {
        throw new Error(response.data.error || '生成失败')
      }
    } catch (err: any) {
      setError(err.message || '生成视觉故事失败')
    } finally {
      setGenerating(false)
      setProgress(0)
    }
  }

  const handleDownloadHTML = () => {
    if (!visualStory?.html) return
    
    const blob = new Blob([visualStory.html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `visual-story-${historyItem?.new_title || 'untitled'}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handlePreviewHTML = () => {
    if (!visualStory?.html) return
    
    const newWindow = window.open('', '_blank')
    if (newWindow) {
      newWindow.document.write(visualStory.html)
      newWindow.document.close()
    }
  }

  const handleClose = () => {
    setVisualStory(null)
    setError(null)
    setGenerating(false)
    setProgress(0)
    onOpenChange(false)
  }

  // Reset state when dialog opens/closes or historyItem changes
  useEffect(() => {
    if (open) {
      setVisualStory(null)
      setError(null)
      setGenerating(false)
      setProgress(0)
      setActiveTab('preview')
    }
  }, [open, historyItem])

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Wand2 className="h-5 w-5 text-purple-600" />
            <span>AI图文故事生成器</span>
          </DialogTitle>
          <DialogDescription>
            将您的文字内容转化为精美的视觉故事卡片，支持多种布局和一键下载
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Source Content Display */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">源内容</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <label className="text-sm font-medium text-gray-700">标题</label>
                  <p className="text-sm text-gray-800 bg-gray-50 p-2 rounded">
                    {historyItem?.new_title || '无标题'}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">内容预览</label>
                  <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded max-h-24 overflow-y-auto">
                    {historyItem?.new_content 
                      ? historyItem.new_content.length > 200 
                        ? historyItem.new_content.substring(0, 200) + '...'
                        : historyItem.new_content
                      : '无内容'
                    }
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Generation Controls */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="font-medium mb-2">生成控制</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    点击生成按钮将内容转化为1张封面卡片和3-9张内容卡片
                  </p>
                  
                  {generating && (
                    <div className="mb-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                        <span className="text-sm text-blue-600">
                          正在生成视觉故事... {Math.round(progress)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {error && (
                    <Alert className="mb-4">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        {error}
                      </AlertDescription>
                    </Alert>
                  )}

                  {visualStory && !generating && (
                    <Alert className="mb-4">
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription>
                        视觉故事生成成功！包含1张封面卡片和{visualStory.content_cards?.length || 0}张内容卡片。
                      </AlertDescription>
                    </Alert>
                  )}
                </div>

                <div className="ml-4 space-x-2">
                  <Button
                    onClick={handleGenerate}
                    disabled={generating || !historyItem}
                    className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                  >
                    {generating ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        生成中...
                      </>
                    ) : (
                      <>
                        <Wand2 className="h-4 w-4 mr-2" />
                        生成视觉故事
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Results Display */}
          {visualStory && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">生成结果</CardTitle>
                  <div className="flex space-x-2">
                    <Button
                      variant={activeTab === 'preview' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setActiveTab('preview')}
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      预览
                    </Button>
                    <Button
                      variant={activeTab === 'html' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setActiveTab('html')}
                    >
                      HTML
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {activeTab === 'preview' ? (
                  <div className="space-y-4">
                    {/* Preview Cards */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {/* Cover Card */}
                      <div className="col-span-1">
                        <div className="bg-white rounded-lg shadow-md overflow-hidden aspect-[3/4]">
                          <div 
                            className="h-full bg-cover bg-center relative"
                            style={{ backgroundImage: `url(${visualStory.cover_card.image_url})` }}
                          >
                            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3">
                              <h3 className="text-white text-sm font-bold">
                                {visualStory.cover_card.title}
                              </h3>
                            </div>
                          </div>
                        </div>
                        <p className="text-xs text-center text-gray-500 mt-1">封面卡片</p>
                      </div>

                      {/* Content Cards */}
                      {visualStory.content_cards?.slice(0, 5).map((card, index) => (
                        <div key={index} className="col-span-1">
                          <div className="bg-white rounded-lg shadow-md overflow-hidden aspect-[3/4]">
                            {card.layout === 'c' ? (
                              // Overlay layout
                              <div 
                                className="h-full bg-cover bg-center relative"
                                style={{ backgroundImage: `url(${card.image_url})` }}
                              >
                                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
                                  <h4 className="text-white text-xs font-bold mb-1">
                                    {card.title}
                                  </h4>
                                  <p className="text-white text-xs opacity-90 line-clamp-2">
                                    {card.content}
                                  </p>
                                </div>
                              </div>
                            ) : card.layout === 'a' ? (
                              // Image top, text bottom
                              <div className="h-full flex flex-col">
                                <div 
                                  className="flex-1 bg-cover bg-center"
                                  style={{ backgroundImage: `url(${card.image_url})` }}
                                />
                                <div className="p-2 bg-white">
                                  <h4 className="text-xs font-bold mb-1">{card.title}</h4>
                                  <p className="text-xs text-gray-600 line-clamp-2">
                                    {card.content}
                                  </p>
                                </div>
                              </div>
                            ) : (
                              // Text top, image bottom
                              <div className="h-full flex flex-col">
                                <div className="p-2 bg-white">
                                  <h4 className="text-xs font-bold mb-1">{card.title}</h4>
                                  <p className="text-xs text-gray-600 line-clamp-2">
                                    {card.content}
                                  </p>
                                </div>
                                <div 
                                  className="flex-1 bg-cover bg-center"
                                  style={{ backgroundImage: `url(${card.image_url})` }}
                                />
                              </div>
                            )}
                          </div>
                          <p className="text-xs text-center text-gray-500 mt-1">
                            内容卡片 {index + 1}
                          </p>
                        </div>
                      ))}

                      {(visualStory.content_cards?.length || 0) > 5 && (
                        <div className="col-span-1">
                          <div className="bg-gray-100 rounded-lg aspect-[3/4] flex items-center justify-center">
                            <div className="text-center">
                              <p className="text-sm font-medium text-gray-600">
                                +{(visualStory.content_cards?.length || 0) - 5}
                              </p>
                              <p className="text-xs text-gray-500">更多卡片</p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="flex space-x-2 pt-4 border-t">
                      <Button onClick={handlePreviewHTML} variant="outline">
                        <Eye className="h-4 w-4 mr-2" />
                        全屏预览
                      </Button>
                      <Button onClick={handleDownloadHTML}>
                        <Download className="h-4 w-4 mr-2" />
                        下载HTML
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <pre className="text-xs text-gray-800 overflow-x-auto whitespace-pre-wrap max-h-60">
                        {visualStory.html}
                      </pre>
                    </div>
                    <div className="flex space-x-2">
                      <Button onClick={handleDownloadHTML}>
                        <Download className="h-4 w-4 mr-2" />
                        下载HTML文件
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}