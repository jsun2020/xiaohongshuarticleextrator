'use client'

import { useState } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { notesAPI } from '@/lib/api'
import { Loader2, Bot, Copy, CheckCircle, AlertCircle } from 'lucide-react'

interface Note {
  note_id: string
  title: string
  content: string
  type: string
  author: {
    nickname: string
    user_id: string
    avatar: string
  }
}

interface RecreateDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  note: Note | null
}

export default function RecreateDialog({ open, onOpenChange, note }: RecreateDialogProps) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  const handleRecreate = async () => {
    if (!note) return

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await notesAPI.recreate(note.title, note.content, note.note_id)
      if (response.data.success) {
        setResult(response.data.data)
      } else {
        setError(response.data.error || 'AI二创失败')
      }
    } catch (error: any) {
      setError(error.response?.data?.error || 'AI二创失败，请检查DeepSeek配置')
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const handleClose = () => {
    setResult(null)
    setError('')
    onOpenChange(false)
  }

  if (!note) return null

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Bot className="h-5 w-5 text-xiaohongshu-red" />
            <span>AI笔记二创</span>
          </DialogTitle>
          <DialogDescription>
            基于DeepSeek AI对笔记内容进行创意改写和优化
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* 原始内容 */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">原始内容</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700">原标题</label>
                <div className="mt-1 p-3 bg-gray-50 rounded-lg border">
                  <p className="text-sm">{note.title}</p>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-700">作者信息</label>
                <div className="mt-1 p-3 bg-gray-50 rounded-lg border flex items-center space-x-2">
                  {note.author.avatar && (
                    <img
                      src={note.author.avatar}
                      alt={note.author.nickname}
                      className="w-6 h-6 rounded-full"
                    />
                  )}
                  <span className="text-sm">{note.author.nickname}</span>
                  <span className="text-xs text-gray-500">({note.type})</span>
                </div>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">原内容</label>
              <div className="mt-1 p-3 bg-gray-50 rounded-lg border max-h-32 overflow-y-auto custom-scrollbar">
                <p className="text-sm whitespace-pre-wrap">{note.content}</p>
              </div>
            </div>
          </div>

          {/* 二创操作 */}
          <div className="border-t pt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">AI二创结果</h3>
              <Button
                onClick={handleRecreate}
                disabled={loading}
                variant="xiaohongshu"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    AI创作中...
                  </>
                ) : (
                  <>
                    <Bot className="mr-2 h-4 w-4" />
                    开始二创
                  </>
                )}
              </Button>
            </div>

            {error && (
              <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-lg mb-4">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            {result && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2 text-green-600 bg-green-50 p-3 rounded-lg">
                  <CheckCircle className="h-4 w-4" />
                  <span className="text-sm">AI二创完成！内容已自动保存到历史记录</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-gray-700">新标题</label>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => copyToClipboard(result.new_title)}
                      >
                        <Copy className="h-3 w-3 mr-1" />
                        复制
                      </Button>
                    </div>
                    <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                      <p className="text-sm font-medium">{result.new_title}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        字符数: {result.new_title.length}
                      </p>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-gray-700">原标题对比</label>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg border">
                      <p className="text-sm">{note.title}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        字符数: {note.title.length}
                      </p>
                    </div>
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">新内容</label>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => copyToClipboard(result.new_content)}
                    >
                      <Copy className="h-3 w-3 mr-1" />
                      复制
                    </Button>
                  </div>
                  <div className="p-3 bg-green-50 rounded-lg border border-green-200 max-h-40 overflow-y-auto custom-scrollbar">
                    <p className="text-sm whitespace-pre-wrap">{result.new_content}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t">
                  <span className="text-xs text-gray-500">
                    💡 提示：可以在"二创历史"页面查看所有历史记录
                  </span>
                  <div className="space-x-2">
                    <Button
                      variant="outline"
                      onClick={handleRecreate}
                      disabled={loading}
                    >
                      重新生成
                    </Button>
                    <Button onClick={handleClose}>
                      完成
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {!result && !error && !loading && (
              <div className="text-center py-8 text-gray-500">
                <Bot className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>点击"开始二创"按钮，让AI为您重新创作内容</p>
                <p className="text-sm mt-2">请确保已正确配置DeepSeek API</p>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}