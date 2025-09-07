'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { deepseekAPI } from '@/lib/api'
import { Loader2, Settings, CheckCircle, AlertCircle, Eye, EyeOff, Sparkles } from 'lucide-react'

interface DeepSeekConfigProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function DeepSeekConfig({ open, onOpenChange }: DeepSeekConfigProps) {
  // DeepSeek configuration
  const [config, setConfig] = useState<{
    api_key?: string
    model: string
    temperature: number
    max_tokens: number
  }>({
    api_key: '',
    model: 'deepseek-chat',
    temperature: 0.7,
    max_tokens: 1000
  })
  
  // Gemini configuration
  const [geminiConfig, setGeminiConfig] = useState<{
    api_key?: string
    model: string
    temperature: number
    max_tokens: number
  }>({
    api_key: '',
    model: 'gemini-2.0-flash-exp',
    temperature: 0.7,
    max_tokens: 1000
  })
  
  // Shared UI state
  const [activeTab, setActiveTab] = useState('deepseek')
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [showApiKey, setShowApiKey] = useState(false)
  const [showGeminiApiKey, setShowGeminiApiKey] = useState(false)
  const [error, setError] = useState('')
  const [originalApiKey, setOriginalApiKey] = useState('')
  const [originalGeminiApiKey, setOriginalGeminiApiKey] = useState('')
  const [apiKeyChanged, setApiKeyChanged] = useState(false)
  const [geminiApiKeyChanged, setGeminiApiKeyChanged] = useState(false)

  useEffect(() => {
    if (open) {
      loadConfig()
    }
  }, [open])

  const loadConfig = async () => {
    try {
      setLoading(true)
      const response = await deepseekAPI.getConfig()
      if (response.data.success && response.data.data && response.data.data.config) {
        const configData = response.data.data.config
        
        // DeepSeek config
        setConfig({
          api_key: configData.deepseek_api_key || '',
          model: configData.deepseek_model || 'deepseek-chat',
          temperature: parseFloat(configData.deepseek_temperature) || 0.7,
          max_tokens: parseInt(configData.deepseek_max_tokens) || 1000
        })
        setOriginalApiKey(configData.deepseek_api_key || '')
        setApiKeyChanged(false)
        
        // Gemini config
        setGeminiConfig({
          api_key: configData.gemini_api_key || '',
          model: configData.gemini_model || 'gemini-2.0-flash-exp',
          temperature: parseFloat(configData.gemini_temperature) || 0.7,
          max_tokens: parseInt(configData.gemini_max_tokens) || 1000
        })
        setOriginalGeminiApiKey(configData.gemini_api_key || '')
        setGeminiApiKeyChanged(false)
      }
    } catch (error) {
      console.error('加载配置失败:', error)
      setError('加载配置失败，请刷新页面重试')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setLoading(true)
      setError('')
      
      // 准备要保存的配置 - 包含DeepSeek和Gemini
      const configToSave: any = {
        deepseek_model: config.model,
        deepseek_temperature: config.temperature.toString(),
        deepseek_max_tokens: config.max_tokens.toString(),
        gemini_model: geminiConfig.model,
        gemini_temperature: geminiConfig.temperature.toString(),
        gemini_max_tokens: geminiConfig.max_tokens.toString()
      }
      
      // DeepSeek API Key处理
      if (!apiKeyChanged && originalApiKey && originalApiKey.includes('***')) {
        // 不发送API Key
      } else if (config.api_key) {
        configToSave.deepseek_api_key = config.api_key
      }
      
      // Gemini API Key处理
      if (!geminiApiKeyChanged && originalGeminiApiKey && originalGeminiApiKey.includes('***')) {
        // 不发送API Key
      } else if (geminiConfig.api_key) {
        configToSave.gemini_api_key = geminiConfig.api_key
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
          setError('DeepSeek API Key应以"sk-"开头')
        } else if (value.length < 20) {
          setError('API Key长度不足，请检查是否完整')
        }
      }
    }
  }

  const handleGeminiInputChange = (field: string, value: any) => {
    setGeminiConfig(prev => ({
      ...prev,
      [field]: value
    }))
    setTestResult(null)
    setError('')
    
    // 跟踪Gemini API Key是否被修改
    if (field === 'api_key') {
      setGeminiApiKeyChanged(value !== originalGeminiApiKey)
      
      // Gemini API Key格式验证
      if (value && !value.includes('***')) {
        if (!value.startsWith('AIza')) {
          setError('Gemini API Key应以"AIza"开头')
        } else if (value.length < 30) {
          setError('Gemini API Key长度不足，请检查是否完整')
        }
      }
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5 text-xiaohongshu-red" />
            <span>API 配置中心</span>
          </DialogTitle>
          <DialogDescription>
            配置DeepSeek和Gemini API以启用AI二创和视觉故事功能
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="deepseek" className="flex items-center space-x-2">
              <Settings className="h-4 w-4" />
              <span>DeepSeek</span>
            </TabsTrigger>
            <TabsTrigger value="gemini" className="flex items-center space-x-2">
              <Sparkles className="h-4 w-4" />
              <span>Gemini</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="deepseek" className="space-y-6 mt-6">
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
                      placeholder={(config.api_key && config.api_key.includes('***')) ? "已保存 (点击修改)" : "sk-xxxxxxxxxxxxxxxx"}
                      value={config.api_key || ''}
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
                  {typeof (testResult.message || testResult.error) === 'string' 
                    ? (testResult.message || testResult.error)
                    : JSON.stringify(testResult.message || testResult.error)}
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
                <p className="text-sm mt-1 text-red-600">
                  {typeof error === 'string' ? error : JSON.stringify(error)}
                </p>
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

          {/* 免费试用说明 */}
          <Card className="bg-green-50 border-green-200">
            <CardContent className="pt-6">
              <h4 className="font-medium text-green-900 mb-2">🎉 免费试用</h4>
              <p className="text-sm text-green-800 mb-2">
                新用户可以免费体验AI二创功能<strong> 3 次</strong>，无需配置API Key！
              </p>
              <p className="text-sm text-green-700">
                试用次数用完后，请配置您自己的DeepSeek API Key继续使用。
              </p>
            </CardContent>
          </Card>

          {/* 使用说明 */}
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="pt-6">
              <h4 className="font-medium text-blue-900 mb-2">使用说明</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• 新用户享有3次免费AI二创机会</li>
                <li>• 免费试用后需要配置您自己的API Key</li>
                <li>• 请确保API Key有效且有足够的余额</li>
                <li>• 温度值越高，生成内容越有创意但可能偏离原意</li>
                <li>• 建议先测试连接确保配置正确</li>
              </ul>
            </CardContent>
          </Card>
          </TabsContent>

          <TabsContent value="gemini" className="space-y-6 mt-6">
            {/* Gemini API Key配置 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Gemini API密钥</CardTitle>
                <CardDescription>
                  请输入您的Gemini API Key，可在 
                  <a 
                    href="https://ai.google.dev/" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-purple-600 hover:underline ml-1"
                  >
                    Google AI Studio
                  </a> 
                  获取，用于生成视觉故事
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Gemini API Key</label>
                    <div className="relative mt-1">
                      <Input
                        type={showGeminiApiKey ? 'text' : 'password'}
                        placeholder={(geminiConfig.api_key && geminiConfig.api_key.includes('***')) ? "已保存 (点击修改)" : "AIzaxxxxxxxxxxxxxxxx"}
                        value={geminiConfig.api_key || ''}
                        onChange={(e) => handleGeminiInputChange('api_key', e.target.value)}
                        className="pr-10"
                      />
                      <button
                        type="button"
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                        onClick={() => setShowGeminiApiKey(!showGeminiApiKey)}
                      >
                        {showGeminiApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Gemini 模型参数配置 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Gemini模型参数</CardTitle>
                <CardDescription>
                  调整Gemini生成参数以获得最佳视觉故事效果
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">模型</label>
                    <select
                      className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-600"
                      value={geminiConfig.model}
                      onChange={(e) => handleGeminiInputChange('model', e.target.value)}
                    >
                      <option value="gemini-2.0-flash-exp">gemini-2.0-flash-exp</option>
                      <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                      <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-sm font-medium">最大Token数</label>
                    <Input
                      type="number"
                      min="100"
                      max="4000"
                      value={geminiConfig.max_tokens}
                      onChange={(e) => handleGeminiInputChange('max_tokens', parseInt(e.target.value))}
                      className="mt-1"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="text-sm font-medium">
                      创造性温度: {geminiConfig.temperature}
                    </label>
                    <input
                      type="range"
                      min="0.1"
                      max="1.0"
                      step="0.1"
                      value={geminiConfig.temperature}
                      onChange={(e) => handleGeminiInputChange('temperature', parseFloat(e.target.value))}
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

            {/* Gemini 免费试用说明 */}
            <Card className="bg-purple-50 border-purple-200">
              <CardContent className="pt-6">
                <h4 className="font-medium text-purple-900 mb-2">🌟 视觉故事功能</h4>
                <p className="text-sm text-purple-800 mb-2">
                  新用户可以免费体验视觉故事生成功能<strong> 10 次</strong>！
                </p>
                <p className="text-sm text-purple-700">
                  试用次数用完后，请配置您自己的Gemini API Key继续使用。
                </p>
              </CardContent>
            </Card>

            {/* Gemini 使用说明 */}
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-6">
                <h4 className="font-medium text-blue-900 mb-2">使用说明</h4>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• 用于将文字内容转化为精美的视觉故事卡片</li>
                  <li>• 生成包含封面和内容卡片的完整HTML文件</li>
                  <li>• 支持多种布局样式和自动下载功能</li>
                  <li>• 建议配置自己的API Key以获得最佳体验</li>
                  <li>• API Key在Google AI Studio免费申请</li>
                </ul>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 共享的测试结果和错误信息 */}
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
                  {typeof (testResult.message || testResult.error) === 'string' 
                    ? (testResult.message || testResult.error)
                    : JSON.stringify(testResult.message || testResult.error)}
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
                <p className="text-sm mt-1 text-red-600">
                  {typeof error === 'string' ? error : JSON.stringify(error)}
                </p>
              </CardContent>
            </Card>
          )}

          {/* 操作按钮 */}
          <div className="flex justify-between pt-4 border-t">
            <Button
              variant="outline"
              onClick={handleTest}
              disabled={testing || (!config.api_key && !geminiConfig.api_key)}
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
                disabled={loading}
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
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}