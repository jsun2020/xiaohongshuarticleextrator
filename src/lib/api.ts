import axios from 'axios'

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api'  // Vercel部署时使用相对路径
  : 'http://localhost:5000/api'  // 开发环境Flask服务器

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true, // 支持cookies
})

// Token管理
const getToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('session_token')
  }
  return null
}

const setToken = (token: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('session_token', token)
  }
}

const removeToken = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('session_token')
  }
}

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // 未授权，跳转到登录页
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 认证相关API
export const authAPI = {
  login: async (username: string, password: string) => {
    const response = await api.post('/api/auth/login', { username, password })
    if (response.data.success && response.data.token) {
      setToken(response.data.token)
    }
    return response
  },
  
  logout: () => {
    removeToken()
    return Promise.resolve({ data: { success: true, message: '登出成功' } })
  },
  
  getStatus: () =>
    api.get('/api/auth/status'),
  
  register: (username: string, password: string, email?: string, nickname?: string) =>
    api.post('/api/auth/register', { username, password, email, nickname }),
}

// 笔记相关API
export const notesAPI = {
  collect: (url: string, cookies?: string) =>
    api.post('/api/xiaohongshu/note', { url, cookies }),
  
  getList: (limit = 20, offset = 0) =>
    api.get(`/api/xiaohongshu/notes?limit=${limit}&offset=${offset}`),
  
  delete: (noteId: string) =>
    api.delete(`/api/xiaohongshu/notes/${noteId}`),
  
  recreate: (title: string, content: string, noteId?: string) =>
    api.post('/api/xiaohongshu/recreate', { title, content, note_id: noteId }),
}

// 二创历史API
export const recreateAPI = {
  getHistory: (limit = 20, offset = 0) =>
    api.get(`/api/xiaohongshu/recreate/history?limit=${limit}&offset=${offset}`),
  
  deleteHistory: (historyId: number) =>
    api.delete(`/api/xiaohongshu/recreate/history/${historyId}`),
}

// DeepSeek配置API
export const deepseekAPI = {
  getConfig: () =>
    api.get('/api/deepseek/config'),
  
  updateConfig: (config: any) =>
    api.post('/api/deepseek/config', config),
  
  testConnection: () =>
    api.post('/api/deepseek/test'),
}

// 健康检查API
export const healthAPI = {
  check: () =>
    api.get('/api/health'),
}

export default api
// 导出token管理函数
export { getToken, setToken, removeToken }