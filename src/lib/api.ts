import axios from 'axios'

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api'  // Vercel部署时使用相对路径
  : '/api'  // 开发环境通过Next.js代理

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 增加到60秒
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
    // 不发送Authorization header，让backend使用cookies认证
    // withCredentials: true 确保cookies被发送（包括HttpOnly的session_token）
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
    const response = await api.post('/auth_login', { username, password })
    if (response.data.success && response.data.token) {
      setToken(response.data.token)
    }
    return response
  },
  
  logout: async () => {
    try {
      const response = await api.post('/auth_logout', {})
      removeToken()
      return response
    } catch (error) {
      removeToken()
      return { data: { success: true, message: '登出成功' } }
    }
  },
  
  getStatus: () =>
    api.get('/auth_status'),
  
  register: (username: string, password: string, email?: string, nickname?: string) =>
    api.post('/auth_register', { username, password, email, nickname }),
}

// 笔记相关API
export const notesAPI = {
  collect: (url: string, cookies?: string) =>
    api.post('/xiaohongshu_notes_list', { url, cookies }),
  
  getList: (limit = 20, offset = 0) =>
    api.get(`/xiaohongshu_notes_list?limit=${limit}&offset=${offset}&_t=${Date.now()}`),
  
  delete: (noteId: string) =>
    api.delete(`/xiaohongshu/notes/${noteId}`),
  
  recreate: (title: string, content: string, noteId?: string) =>
    api.post('/xiaohongshu_recreate', { title, content, note_id: noteId }),
}

// 二创历史API
export const recreateAPI = {
  getHistory: (limit = 20, offset = 0) =>
    api.get(`/xiaohongshu_recreate_history?limit=${limit}&offset=${offset}`),
  
  deleteHistory: (historyId: number) =>
    api.delete(`/xiaohongshu/recreate/history/${historyId}`),
}

// DeepSeek配置API
export const deepseekAPI = {
  getConfig: () =>
    api.get('/deepseek/config'),
  
  updateConfig: (config: any) =>
    api.post('/deepseek/config', config),
  
  testConnection: () =>
    api.post('/deepseek/test'),
}

// 健康检查API
export const healthAPI = {
  check: () =>
    api.get('/health'),
}

export default api
// 导出token管理函数
export { getToken, setToken, removeToken }