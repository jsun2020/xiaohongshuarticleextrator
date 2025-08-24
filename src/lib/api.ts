import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true, // 支持session
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
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
  login: (username: string, password: string) =>
    api.post('/api/auth/login', { username, password }),
  
  logout: () =>
    api.post('/api/auth/logout'),
  
  getStatus: () =>
    api.get('/api/auth/status'),
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