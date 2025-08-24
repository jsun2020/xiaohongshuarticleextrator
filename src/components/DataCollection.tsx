'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { notesAPI } from '@/lib/api'
import { isValidXhsUrl } from '@/lib/utils'
import { Loader2, Link, CheckCircle, AlertCircle, Copy } from 'lucide-react'

export default function DataCollection() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!url.trim()) {
      setError('请输入小红书笔记链接')
      return
    }

    if (!isValidXhsUrl(url)) {
      setError('请输入有效的小红书笔记链接')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await notesAPI.collect(url.trim())
      if (response.data.success) {
        setResult(response.data)
        setUrl('') // 清空输入框
      } else {
        setError(response.data.error || '采集失败')
      }
    } catch (error: any) {
      setError(error.response?.data?.error || '采集失败，请检查网络连接')
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <div className="space-y-6">
      {/* 采集表单 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Link className="h-5 w-5 text-xiaohongshu-red" />
            <span>笔记链接采集</span>
          </CardTitle>
          <CardDescription>
            支持标准链接和短链接格式，自动提取笔记详细信息
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex space-x-2">
              <Input
                type="url"
                placeholder="请粘贴小红书笔记链接..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading}
                className="flex-1"
              />
              <Button
                type="submit"
                variant="xiaohongshu"
                disabled={loading || !url.trim()}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    采集中
                  </>
                ) : (
                  '开始采集'
                )}
              </Button>
            </div>

            {error && (
              <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-lg">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm">{error}</span>
              </div>
            )}

            <div className="text-xs text-gray-500 space-y-1">
              <p>支持的链接格式：</p>
              <p>• https://www.xiaohongshu.com/explore/...</p>
              <p>• https://www.xiaohongshu.com/discovery/item/...</p>
              <p>• http://xhslink.com/...</p>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* 采集结果 */}
      {result && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-green-700">
              <CheckCircle className="h-5 w-5" />
              <span>采集成功</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* 基本信息 */}
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium text-gray-700">笔记ID</label>
                  <div className="flex items-center space-x-2 mt-1">
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                      {result.data.note_id}
                    </code>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => copyToClipboard(result.data.note_id)}
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700">标题</label>
                  <p className="text-sm mt-1 p-2 bg-white rounded border">
                    {result.data.title}
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700">类型</label>
                  <span className={`inline-block mt-1 px-2 py-1 text-xs rounded ${
                    result.data.type === '视频' 
                      ? 'bg-purple-100 text-purple-700' 
                      : 'bg-blue-100 text-blue-700'
                  }`}>
                    {result.data.type}
                  </span>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700">作者</label>
                  <div className="flex items-center space-x-2 mt-1">
                    {result.data.author.avatar && (
                      <img
                        src={result.data.author.avatar}
                        alt="头像"
                        className="w-6 h-6 rounded-full"
                      />
                    )}
                    <span className="text-sm">{result.data.author.nickname}</span>
                  </div>
                </div>
              </div>

              {/* 互动数据 */}
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium text-gray-700">互动数据</label>
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <div className="bg-white p-2 rounded border text-center">
                      <div className="text-lg font-semibold text-red-500">
                        {result.data.stats.likes}
                      </div>
                      <div className="text-xs text-gray-500">点赞</div>
                    </div>
                    <div className="bg-white p-2 rounded border text-center">
                      <div className="text-lg font-semibold text-yellow-500">
                        {result.data.stats.collects}
                      </div>
                      <div className="text-xs text-gray-500">收藏</div>
                    </div>
                    <div className="bg-white p-2 rounded border text-center">
                      <div className="text-lg font-semibold text-blue-500">
                        {result.data.stats.comments}
                      </div>
                      <div className="text-xs text-gray-500">评论</div>
                    </div>
                    <div className="bg-white p-2 rounded border text-center">
                      <div className="text-lg font-semibold text-green-500">
                        {result.data.stats.shares}
                      </div>
                      <div className="text-xs text-gray-500">分享</div>
                    </div>
                  </div>
                </div>

                {result.data.tags && result.data.tags.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">标签</label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {result.data.tags.map((tag: string, index: number) => (
                        <span
                          key={index}
                          className="px-2 py-1 text-xs bg-xiaohongshu-pink/10 text-xiaohongshu-red rounded-full"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {result.data.location && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">位置</label>
                    <p className="text-sm mt-1">{result.data.location}</p>
                  </div>
                )}

                {result.data.publish_time && (
                  <div>
                    <label className="text-sm font-medium text-gray-700">发布时间</label>
                    <p className="text-sm mt-1">{result.data.publish_time}</p>
                  </div>
                )}
              </div>
            </div>

            {/* 内容预览 */}
            {result.data.content && (
              <div>
                <label className="text-sm font-medium text-gray-700">内容预览</label>
                <div className="mt-1 p-3 bg-white rounded border max-h-32 overflow-y-auto custom-scrollbar">
                  <p className="text-sm whitespace-pre-wrap">{result.data.content}</p>
                </div>
              </div>
            )}

            {/* 图片预览 */}
            {result.data.images && result.data.images.length > 0 && (
              <div>
                <label className="text-sm font-medium text-gray-700">
                  图片 ({result.data.images.length}张)
                </label>
                <div className="grid grid-cols-4 gap-2 mt-1">
                  {result.data.images.slice(0, 8).map((image: string, index: number) => (
                    <img
                      key={index}
                      src={image}
                      alt={`图片${index + 1}`}
                      className="w-full h-20 object-cover rounded border"
                    />
                  ))}
                  {result.data.images.length > 8 && (
                    <div className="w-full h-20 bg-gray-100 rounded border flex items-center justify-center text-xs text-gray-500">
                      +{result.data.images.length - 8}
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="flex items-center justify-between pt-2 border-t">
              <span className="text-xs text-gray-500">
                {result.saved_to_db ? '✅ 已保存到数据库' : '⚠️ 数据库保存失败'}
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setResult(null)}
              >
                关闭
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}