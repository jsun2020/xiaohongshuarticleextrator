'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { deepseekAPI } from '@/lib/api'
import { Loader2, Settings, CheckCircle, AlertCircle, Eye, EyeOff } from 'lucide-react'

interface DeepSeekConfigProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function DeepSeekConfig({ open, onOpenChange }: DeepSeekConfigProps) {
  const [config, setConfig] = useState({
    api_key: '',
    model: 'deepseek-chat',
    temperature: 0.7,
    max_tokens: 1000
  })
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [showApiKey, setShowApiKey] = useState(false)
  const [error, setError] = useState('')
  const [originalApiKey, setOriginalApiKey] = useState('')
  const [apiKeyChanged, setApiKeyChanged] = useState(false)

  useEffect(() => {
    if (open) {
      loadConfig()
    }
  }, [open])

  const loadConfig = async () => {
    try {
      setLoading(true)
      const response = await deepseekAPI.getConfig()
      if (response.data.success) {
        setConfig(response.data.config)
        setOriginalApiKey(response.data.config.api_key)
        setApiKeyChanged(false)
      }
    } catch (error) {
      console.error('加载配置失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setLoading(true)
      setError('')
      
      // 准备要保存的配置
      const configToSave = { ...config }
      
      // 如果API Key没有改变且是掩码格式，不发送API Key
      if (!apiKeyChanged && originalApiKey.includes('***')) {
        delete configToSave.api_key
      }
      
      const response = await deepseekAPI.updateConfig(configToSave)
      if (response.data.success) {
        setTestResult({ success: true, message: '配置保存成功' })
        // 重新加载配置以获取最新的掩码显示
        await loadConfig()
      } else {
        setError(response.data.error || '保存失败')
      }
    } catch (error: any) {
      setError(error.response?.data?.error || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async () => {
    try {
      setTesting(true)
      setTestResult(null)
      setError('')
      
      const response = await deepseekAPI.testConnection()
      setTestResult(response.data)
    } catch (error: any) {
      setTestResult({
        success: false,
        error: error.response?.data?.error || '连接测试失败'
      })
    } finally {
      setTesting(false)
    }
  }

  const handleInputChange = (field: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }))
    setTestResult(null)
    setError('')
    
    // 跟踪API Key是否被修改
    if (field === 'api_key') {
      setApiKeyChanged(value !== originalApiKey)
      
      // API Key格式验证（只对新输入的API Key进行验证）
      if (value && !value.includes('***')) {
        if (!value.startsWith('sk-')) {
          setError('API Key应以"sk-"开头')
        } else if (value.length < 20) {
          setError('API Key长度不足，请检查是否完整')
        }
      }
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5 text-xiaohongshu-red" />
            <span>DeepSeek API 配置</span>
          </DialogTitle>
          <DialogDescription>
            配置DeepSeek API以启用AI二创功能
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* API Key配置 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">API密钥</CardTitle>
              <CardDescription>
                请输入您的DeepSeek API Key，可在 
                <a 
                  href="https://platform.deepseek.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-xiaohongshu-red hover:underline ml-1"
                >
                  DeepSeek平台
                </a> 
                获取
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">API Key</label>
                  <div className="relative mt-1">
                    <Input
                      type={showApiKey ? 'text' : 'password'}
                      placeholder={config.api_key.includes('***') ? "已保存 (点击修改)" : "sk-xxxxxxxxxxxxxxxx"}
                      value={config.api_key}
                      onChange={(e) => handleInputChange('api_key', e.target.value)}
                      className="pr-10"
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                      onClick={() => setShowApiKey(!showApiKey)}
                    >
                      {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 模型参数配置 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">模型参数</CardTitle>
              <CardDescription>
                调整AI生成参数以获得最佳效果
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">模型</label>
                  <select
                    className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-xiaohongshu-red"
                    value={config.model}
                    onChange={(e) => handleInputChange('model', e.target.value)}
                  >
                    <option value="deepseek-chat">deepseek-chat</option>
                    <option value="deepseek-reasoner">deepseek-reasoner</option>
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium">最大Token数</label>
                  <Input
                    type="number"
                    min="100"
                    max="4000"
                    value={config.max_tokens}
                    onChange={(e) => handleInputChange('max_tokens', parseInt(e.target.value))}
                    className="mt-1"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="text-sm font-medium">
                    创造性温度: {config.temperature}
                  </label>
                  <input
                    type="range"
                    min="0.1"
                    max="1.0"
                    step="0.1"
                    value={config.temperature}
                    onChange={(e) => handleInputChange('temperature', parseFloat(e.target.value))}
                    className="w-full mt-2"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>保守 (0.1)</span>
                    <span>平衡 (0.7)</span>
                    <span>创新 (1.0)</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 测试结果 */}
          {testResult && (
            <Card className={testResult.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
              <CardContent className="pt-6">
                <div className={`flex items-center space-x-2 ${testResult.success ? 'text-green-700' : 'text-red-700'}`}>
                  {testResult.success ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <AlertCircle className="h-4 w-4" />
                  )}
                  <span className="text-sm font-medium">
                    {testResult.success ? '连接测试成功' : '连接测试失败'}
                  </span>
                </div>
                <p className="text-sm mt-1 text-gray-600">
                  {testResult.message || testResult.error}
                </p>
              </CardContent>
            </Card>
          )}

          {/* 错误信息 */}
          {error && (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="pt-6">
                <div className="flex items-center space-x-2 text-red-700">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">配置错误</span>
                </div>
                <p className="text-sm mt-1 text-red-600">{error}</p>
              </CardContent>
            </Card>
          )}

          {/* 操作按钮 */}
          <div className="flex justify-between pt-4 border-t">
            <Button
              variant="outline"
              onClick={handleTest}
              disabled={testing || !config.api_key}
            >
              {testing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  测试中...
                </>
              ) : (
                '测试连接'
              )}
            </Button>

            <div className="space-x-2">
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <Button
                variant="xiaohongshu"
                onClick={handleSave}
                disabled={loading || !config.api_key}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    保存中...
                  </>
                ) : (
                  '保存设置'
                )}
              </Button>
            </div>
          </div>

          {/* 使用说明 */}
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="pt-6">
              <h4 className="font-medium text-blue-900 mb-2">使用说明</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• 请确保API Key有效且有足够的余额</li>
                <li>• 温度值越高，生成内容越有创意但可能偏离原意</li>
                <li>• 建议先测试连接确保配置正确</li>
                <li>• 配置保存后即可在笔记管理中使用AI二创功能</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  )
}