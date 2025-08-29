'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { authAPI } from '@/lib/api'
import { Eye, EyeOff, Loader2, LogIn, UserPlus, User, Mail } from 'lucide-react'

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [email, setEmail] = useState('')
  const [nickname, setNickname] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const router = useRouter()

  useEffect(() => {
    // 检查是否已登录
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('/api/auth_status', {
        method: 'GET',
        credentials: 'include',
      })
      const data = await response.json()
      if (data.logged_in) {
        router.push('/')
      }
    } catch (error) {
      // 未登录，继续显示登录页面
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await authAPI.login(username.trim(), password)
      
      if (response.data.success) {
        router.push('/')
      } else {
        setError(response.data.error || '登录失败')
      }
    } catch (error: any) {
      if (error.response?.data?.error) {
        setError(error.response.data.error)
      } else {
        setError('登录失败，请检查网络连接')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess('')

    // 表单验证
    if (!username.trim()) {
      setError('用户名不能为空')
      setLoading(false)
      return
    }
    if (username.length < 3 || username.length > 20) {
      setError('用户名长度应在3-20个字符之间')
      setLoading(false)
      return
    }
    if (!password) {
      setError('密码不能为空')
      setLoading(false)
      return
    }
    if (password.length < 6) {
      setError('密码长度至少6个字符')
      setLoading(false)
      return
    }
    if (password !== confirmPassword) {
      setError('两次输入的密码不一致')
      setLoading(false)
      return
    }
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('邮箱格式不正确')
      setLoading(false)
      return
    }

    try {
      const response = await authAPI.register(
        username.trim(),
        password,
        email.trim() || undefined,
        nickname.trim() || undefined
      )

      if (response.data.success) {
        setSuccess('注册成功！请使用您的账户登录。')
        setIsLogin(true)
        // 清空表单
        setPassword('')
        setConfirmPassword('')
        setEmail('')
        setNickname('')
      } else {
        setError(response.data.error || '注册失败')
      }
    } catch (error: any) {
      if (error.response?.data?.error) {
        setError(error.response.data.error)
      } else {
        setError('网络错误，请重试')
      }
    } finally {
      setLoading(false)
    }
  }

  const switchMode = () => {
    setIsLogin(!isLogin)
    setError('')
    setSuccess('')
    setPassword('')
    setConfirmPassword('')
    setEmail('')
    setNickname('')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 to-orange-50">
      <div className="w-full max-w-md p-6">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold xhs-text-gradient mb-2">
            小红书数据研究院
          </h1>
          <p className="text-gray-600">
            笔记数据采集、二创和管理系统
          </p>
        </div>

        <Card className="shadow-lg">
          <CardHeader className="space-y-1">
            <div className="flex justify-center mb-4">
              <div className="p-3 bg-xiaohongshu-red/10 rounded-full">
                {isLogin ? <LogIn className="h-8 w-8 text-xiaohongshu-red" /> : <UserPlus className="h-8 w-8 text-xiaohongshu-red" />}
              </div>
            </div>
            <CardTitle className="text-2xl text-center">
              {isLogin ? '登录' : '注册'}
            </CardTitle>
            <CardDescription className="text-center">
              {isLogin ? '请输入您的账号信息' : '创建您的账户'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {success && (
              <Alert className="mb-4 border-green-200 bg-green-50">
                <AlertDescription className="text-green-800">
                  {success}
                </AlertDescription>
              </Alert>
            )}

            {error && (
              <Alert className="mb-4 border-red-200 bg-red-50">
                <AlertDescription className="text-red-800">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            <form onSubmit={isLogin ? handleLogin : handleRegister} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="username" className="text-sm font-medium text-gray-700">
                  用户名 *
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    id="username"
                    type="text"
                    placeholder={isLogin ? "请输入用户名" : "请输入用户名（3-20个字符）"}
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    disabled={loading}
                    className="pl-10"
                    maxLength={20}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium text-gray-700">
                  密码 *
                </label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder={isLogin ? "请输入密码" : "请输入密码（至少6个字符）"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={loading}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={loading}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {!isLogin && (
                <>
                  <div className="space-y-2">
                    <label htmlFor="confirmPassword" className="text-sm font-medium text-gray-700">
                      确认密码 *
                    </label>
                    <div className="relative">
                      <Input
                        id="confirmPassword"
                        type={showConfirmPassword ? 'text' : 'password'}
                        placeholder="请再次输入密码"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        disabled={loading}
                        className="pr-10"
                      />
                      <button
                        type="button"
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        disabled={loading}
                      >
                        {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="email" className="text-sm font-medium text-gray-700">
                      邮箱（可选）
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="email"
                        type="email"
                        placeholder="请输入邮箱地址"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        disabled={loading}
                        className="pl-10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="nickname" className="text-sm font-medium text-gray-700">
                      昵称（可选）
                    </label>
                    <Input
                      id="nickname"
                      type="text"
                      placeholder="请输入昵称"
                      value={nickname}
                      onChange={(e) => setNickname(e.target.value)}
                      disabled={loading}
                      maxLength={50}
                    />
                  </div>
                </>
              )}

              <Button
                type="submit"
                className="w-full bg-xiaohongshu-red hover:bg-xiaohongshu-red/90"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {isLogin ? '登录中...' : '注册中...'}
                  </>
                ) : (
                  isLogin ? '登录' : '注册'
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                {isLogin ? '还没有账户？' : '已有账户？'}
                <button
                  onClick={switchMode}
                  className="ml-1 text-xiaohongshu-red hover:underline font-medium"
                  disabled={loading}
                >
                  {isLogin ? '立即注册' : '立即登录'}
                </button>
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="mt-8 text-center text-xs text-gray-500">
          <p>© 2024 小红书数据研究院. 仅供学习研究使用</p>
        </div>
      </div>
    </div>
  )
}