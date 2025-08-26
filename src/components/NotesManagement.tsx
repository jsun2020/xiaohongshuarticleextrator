'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { notesAPI } from '@/lib/api'
import { formatNumber, formatDate, truncateText } from '@/lib/utils'
import { Loader2, RefreshCw, Trash2, Bot, Copy, Image, Video, MapPin, Calendar, User } from 'lucide-react'
import RecreateDialog from '@/components/RecreateDialog'

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
  stats: {
    likes: number
    collects: number
    comments: number
    shares: number
  }
  publish_time: string
  location: string
  tags: string[]
  images: string[]
  videos: string[]
  created_at: string
}

export default function NotesManagement() {
  const [notes, setNotes] = useState<Note[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [total, setTotal] = useState(0)
  const [selectedNote, setSelectedNote] = useState<Note | null>(null)
  const [showRecreateDialog, setShowRecreateDialog] = useState(false)

  useEffect(() => {
    loadNotes()
  }, [])

  const loadNotes = async (offset = 0, append = false) => {
    try {
      if (!append) setLoading(true)
      else setLoadingMore(true)

      const response = await notesAPI.getList(20, offset)
      console.log('Notes API response:', response.data)
      if (response.data.success) {
        const newNotes = response.data.data || []
        console.log('New notes:', newNotes)
        setNotes(append ? [...(notes || []), ...newNotes] : newNotes)
        setTotal(response.data.pagination?.total || newNotes.length)
        setHasMore(response.data.pagination?.total > (offset + newNotes.length))
      } else {
        console.error('API returned error:', response.data.error)
      }
    } catch (error) {
      console.error('加载笔记失败:', error)
      if (!append) setNotes([])
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  const handleRefresh = () => {
    loadNotes()
  }

  const handleLoadMore = () => {
    loadNotes(notes?.length || 0, true)
  }

  const handleDelete = async (noteId: string) => {
    if (!confirm('确定要删除这条笔记吗？')) return

    try {
      const response = await notesAPI.delete(noteId)
      if (response.data.success) {
        setNotes(notes.filter(note => note.note_id !== noteId))
        setTotal(total - 1)
      }
    } catch (error) {
      console.error('删除失败:', error)
      alert('删除失败，请重试')
    }
  }

  const handleRecreate = (note: Note) => {
    setSelectedNote(note)
    setShowRecreateDialog(true)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-xiaohongshu-red" />
          <p className="text-gray-600">加载笔记中...</p>
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
              <CardTitle>笔记管理</CardTitle>
              <CardDescription>
                共 {total} 条笔记，支持查看、删除和AI二创
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

      {/* 笔记列表 */}
      {notes?.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500">暂无笔记数据</p>
            <p className="text-sm text-gray-400 mt-2">
              请先在"数据采集"页面采集一些笔记
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {notes?.map((note) => (
            <Card key={note.note_id} className="overflow-hidden hover:shadow-lg transition-shadow">
              {/* 封面图片 */}
              {note.images.length > 0 && (
                <div className="relative h-48 bg-gray-100">
                  <img
                    src={note.images[0]}
                    alt={note.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-2 right-2 flex space-x-1">
                    {note.type === '视频' && (
                      <span className="bg-black/70 text-white px-2 py-1 rounded text-xs flex items-center">
                        <Video className="h-3 w-3 mr-1" />
                        视频
                      </span>
                    )}
                    {note.images.length > 1 && (
                      <span className="bg-black/70 text-white px-2 py-1 rounded text-xs flex items-center">
                        <Image className="h-3 w-3 mr-1" />
                        {note.images.length}
                      </span>
                    )}
                  </div>
                </div>
              )}

              <CardContent className="p-4">
                {/* 标题 */}
                <h3 className="font-semibold text-lg mb-2 line-clamp-2">
                  {note.title}
                </h3>

                {/* 内容预览 */}
                {note.content && (
                  <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                    {truncateText(note.content, 100)}
                  </p>
                )}

                {/* 作者信息 */}
                <div className="flex items-center space-x-2 mb-3">
                  {note.author?.avatar && (
                    <img
                      src={note.author.avatar}
                      alt={note.author.nickname || '作者'}
                      className="w-6 h-6 rounded-full"
                    />
                  )}
                  <span className="text-sm text-gray-700">{note.author?.nickname || '未知作者'}</span>
                </div>

                {/* 互动数据 */}
                <div className="grid grid-cols-4 gap-2 mb-3">
                  <div className="text-center">
                    <div className="text-sm font-semibold text-red-500">
                      {formatNumber(note.stats?.likes)}
                    </div>
                    <div className="text-xs text-gray-500">点赞</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-semibold text-yellow-500">
                      {formatNumber(note.stats?.collects)}
                    </div>
                    <div className="text-xs text-gray-500">收藏</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-semibold text-blue-500">
                      {formatNumber(note.stats?.comments)}
                    </div>
                    <div className="text-xs text-gray-500">评论</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm font-semibold text-green-500">
                      {formatNumber(note.stats?.shares)}
                    </div>
                    <div className="text-xs text-gray-500">分享</div>
                  </div>
                </div>

                {/* 标签 */}
                {note.tags && note.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {note.tags.slice(0, 3).map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 text-xs bg-xiaohongshu-pink/10 text-xiaohongshu-red rounded-full"
                      >
                        #{tag}
                      </span>
                    ))}
                    {note.tags.length > 3 && (
                      <span className="px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded-full">
                        +{note.tags.length - 3}
                      </span>
                    )}
                  </div>
                )}

                {/* 元信息 */}
                <div className="space-y-1 text-xs text-gray-500 mb-4">
                  {note.location && (
                    <div className="flex items-center">
                      <MapPin className="h-3 w-3 mr-1" />
                      {note.location}
                    </div>
                  )}
                  {note.publish_time && (
                    <div className="flex items-center">
                      <Calendar className="h-3 w-3 mr-1" />
                      {note.publish_time}
                    </div>
                  )}
                  <div className="flex items-center">
                    <User className="h-3 w-3 mr-1" />
                    采集于 {formatDate(note.created_at)}
                  </div>
                </div>

                {/* 操作按钮 */}
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => copyToClipboard(note.note_id)}
                    className="flex-1"
                  >
                    <Copy className="h-3 w-3 mr-1" />
                    复制ID
                  </Button>
                  <Button
                    size="sm"
                    variant="xiaohongshu"
                    onClick={() => handleRecreate(note)}
                    className="flex-1"
                  >
                    <Bot className="h-3 w-3 mr-1" />
                    AI二创
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDelete(note.note_id)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* 加载更多 */}
      {hasMore && notes.length > 0 && (
        <div className="text-center">
          <Button
            variant="outline"
            onClick={handleLoadMore}
            disabled={loadingMore}
          >
            {loadingMore ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                加载中...
              </>
            ) : (
              '加载更多'
            )}
          </Button>
        </div>
      )}

      {/* AI二创对话框 */}
      <RecreateDialog
        open={showRecreateDialog}
        onOpenChange={setShowRecreateDialog}
        note={selectedNote}
      />
    </div>
  )
}