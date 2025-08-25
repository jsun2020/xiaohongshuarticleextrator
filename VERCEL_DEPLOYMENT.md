# Vercel Deployment Guide / Vercel 部署指南

This document explains how to deploy the Xiaohongshu Article Extractor application to Vercel.
本文档说明如何将小红书笔记采集应用部署到 Vercel。

## Project Structure / 项目结构

The project has been refactored to a Vercel-compatible Serverless architecture:
项目已重构为 Vercel 兼容的 Serverless 架构：

```
/
├── api/                             # Serverless API functions / API 函数
│   ├── auth_login.py                # /api/auth/login - User login
│   ├── auth_register.py             # /api/auth/register - User registration
│   ├── auth_logout.py               # /api/auth/logout - User logout
│   ├── auth_status.py               # /api/auth/status - Login status
│   ├── xiaohongshu_note.py          # /api/xiaohongshu/note - Get note
│   ├── xiaohongshu_notes.py         # /api/xiaohongshu/notes - Get notes list
│   ├── xiaohongshu_notes_delete.py  # Delete notes
│   ├── xiaohongshu_recreate.py      # /api/xiaohongshu/recreate - AI recreation
│   ├── recreate_history.py          # /api/xiaohongshu/recreate/history
│   ├── recreate_history_delete.py   # Delete recreation history
│   ├── deepseek_config.py           # /api/deepseek/config - DeepSeek settings
│   ├── deepseek_test.py             # /api/deepseek/test - Test connection
│   ├── health.py                    # /api/health - Health check
│   ├── _utils.py                    # Shared utilities / 共享工具
│   ├── _database.py                 # Database manager / 数据库管理
│   ├── _xhs_crawler.py              # Xiaohongshu crawler / 爬虫
│   ├── _deepseek_api.py             # DeepSeek API integration
│   └── requirements.txt             # Python dependencies / Python 依赖
├── src/                             # Next.js frontend / Next.js 前端
├── vercel.json                      # Vercel configuration / Vercel 配置
├── package.json                     # Node.js dependencies / Node.js 依赖
└── ...
```

## 主要变更

### 1. 后端架构变更
- 从 Flask 应用重构为独立的 Serverless 函数
- 每个 API 路由对应一个独立的 Python 文件
- 使用 JWT 替代 Flask Session 进行用户认证
- 数据库适配 Serverless 环境（使用临时目录）

### 2. 认证系统变更
- 前端使用 JWT Token 进行认证
- Token 存储在 localStorage 中
- 每个请求通过 Authorization Header 发送 Token

### 3. 数据库注意事项
**重要：** SQLite 数据库文件在 Serverless 环境中无法持久化。每次函数执行都会重新开始。

**建议的解决方案：**
1. 使用 Vercel Postgres 数据库
2. 使用 MongoDB Atlas
3. 使用 Supabase
4. 使用 PlanetScale

## 部署步骤

### 1. 准备 Vercel 账户
1. 注册 [Vercel](https://vercel.com) 账户
2. 安装 Vercel CLI：`npm i -g vercel`

### 2. 配置环境变量
在 Vercel 项目设置中添加以下环境变量：

```bash
JWT_SECRET=your_jwt_secret_key_here
```

### 3. 部署到 Vercel

#### 方法一：通过 Git 自动部署
1. 将代码推送到 GitHub/GitLab/Bitbucket
2. 在 Vercel 中连接你的 Git 仓库
3. Vercel 会自动检测配置并部署

#### 方法二：通过 CLI 部署
```bash
# 在项目根目录执行
vercel

# 首次部署时会询问项目配置
# 后续部署只需要执行
vercel --prod
```

### 4. 验证部署
部署完成后，访问以下端点验证：

- 健康检查：`https://your-app.vercel.app/api/health`
- 前端应用：`https://your-app.vercel.app`

## 数据库迁移方案

### 选项1：Vercel Postgres（推荐）
```bash
# 安装 Vercel Postgres
npm i @vercel/postgres

# 在 Vercel 项目中启用 Postgres
vercel env add POSTGRES_URL
```

### 选项2：Supabase
1. 注册 [Supabase](https://supabase.com) 账户
2. 创建新项目
3. 获取数据库连接字符串
4. 在 Vercel 中设置环境变量：
   ```bash
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

### 选项3：MongoDB Atlas
1. 注册 [MongoDB Atlas](https://www.mongodb.com/atlas) 账户
2. 创建集群
3. 获取连接字符串
4. 修改 `database.py` 以使用 MongoDB

## 配置文件说明

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    },
    {
      "src": "api/*.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    // API 路由映射
  ]
}
```

### api/requirements.txt
```
requests==2.31.0
PyJWT==2.8.0
```

## 常见问题

### 1. 数据库连接问题
- 确保数据库 URL 正确配置
- 检查网络连接和防火墙设置
- 验证数据库凭据

### 2. 认证问题
- 确保 JWT_SECRET 环境变量已设置
- 检查前端 Token 存储和发送逻辑
- 验证 CORS 配置

### 3. 冷启动问题
- Serverless 函数可能有冷启动延迟
- 考虑使用 Vercel Pro 计划减少冷启动时间

### 4. 文件上传限制
- Vercel 有请求大小限制（默认 4.5MB）
- 大文件需要使用外部存储服务

## 监控和日志

### 查看部署日志
```bash
vercel logs your-deployment-url
```

### 实时日志
```bash
vercel logs --follow
```

## 性能优化

1. **启用缓存**：为静态资源配置适当的缓存头
2. **压缩响应**：Vercel 自动启用 gzip 压缩
3. **CDN 优化**：利用 Vercel 的全球 CDN
4. **数据库优化**：使用连接池和查询优化

## 安全考虑

1. **环境变量**：敏感信息存储在环境变量中
2. **CORS 配置**：正确配置跨域请求
3. **JWT 安全**：使用强密钥和适当的过期时间
4. **输入验证**：对所有用户输入进行验证

## 成本估算

- **Hobby 计划**：免费，适合个人项目
- **Pro 计划**：$20/月，提供更好的性能和功能
- **数据库成本**：根据选择的数据库服务而定

## 支持和帮助

- [Vercel 文档](https://vercel.com/docs)
- [Next.js 文档](https://nextjs.org/docs)
- [Vercel 社区](https://github.com/vercel/vercel/discussions)