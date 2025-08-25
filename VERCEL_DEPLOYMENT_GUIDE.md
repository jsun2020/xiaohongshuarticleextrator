# 🚀 Vercel部署指南

本指南将帮助你将小红书笔记管理系统部署到Vercel平台。

## 📋 部署前准备

### 1. 项目结构调整

项目已重构为Vercel兼容的Serverless架构：

```
/
├── api/                          # Serverless API函数
│   ├── _utils.py                # 工具函数
│   ├── _database.py             # 数据库管理
│   ├── _xhs_crawler.py          # 小红书爬虫
│   ├── _deepseek_api.py         # DeepSeek API
│   ├── auth_register.py         # 用户注册
│   ├── auth_login.py            # 用户登录
│   ├── auth_logout.py           # 用户登出
│   ├── auth_status.py           # 登录状态
│   ├── xiaohongshu_note.py      # 获取笔记
│   ├── xiaohongshu_notes.py     # 笔记列表
│   ├── xiaohongshu_notes_delete.py # 删除笔记
│   ├── xiaohongshu_recreate.py  # 笔记二创
│   ├── deepseek_config.py       # DeepSeek配置
│   ├── deepseek_test.py         # 测试连接
│   ├── recreate_history.py      # 二创历史
│   ├── recreate_history_delete.py # 删除历史
│   ├── health.py                # 健康检查
│   └── requirements.txt         # Python依赖
├── src/                         # Next.js前端
├── vercel.json                  # Vercel配置
└── package.json                 # 项目配置
```

### 2. 数据库准备

由于Vercel不支持SQLite持久化，需要使用外部数据库：

**推荐选项：**
- **Vercel Postgres**（推荐）：Vercel官方数据库服务
- **Supabase**：免费PostgreSQL服务
- **PlanetScale**：MySQL兼容的数据库
- **MongoDB Atlas**：NoSQL数据库

## 🔧 Vercel部署步骤

### 1. 准备代码仓库

```bash
# 初始化Git仓库（如果还没有）
git init
git add .
git commit -m \"Initial commit for Vercel deployment\"

# 推送到GitHub/GitLab/Bitbucket
git remote add origin <your-repo-url>
git push -u origin main
```

### 2. 创建Vercel项目

1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 点击 \"New Project\"
3. 导入你的Git仓库
4. 选择框架：**Next.js**
5. 配置项目设置

### 3. 配置环境变量

在Vercel项目设置中添加以下环境变量：

```bash
# 数据库配置
DATABASE_URL=postgresql://username:password@host:port/database

# 可选：其他配置
NODE_ENV=production
```

**获取DATABASE_URL的方法：**

#### 使用Vercel Postgres：
1. 在Vercel项目中点击 \"Storage\" 标签
2. 创建 \"Postgres\" 数据库
3. 复制连接字符串到 `DATABASE_URL`

#### 使用Supabase：
1. 访问 [Supabase](https://supabase.com)
2. 创建新项目
3. 在 Settings > Database 中找到连接字符串
4. 格式：`postgresql://postgres:[password]@[host]:5432/postgres`

### 4. 部署项目

```bash
# 方法1：通过Vercel CLI
npm i -g vercel
vercel --prod

# 方法2：通过Git推送（推荐）
git push origin main  # Vercel会自动部署
```

## 📝 部署后配置

### 1. 数据库初始化

部署成功后，需要初始化数据库表。可以通过以下方式：

**方法1：使用数据库管理工具**
```sql
-- 在你的PostgreSQL数据库中执行以下SQL

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    nickname VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, config_key)
);

CREATE TABLE notes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    note_id VARCHAR(100) NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    note_type VARCHAR(50),
    publish_time VARCHAR(100),
    location VARCHAR(200),
    original_url TEXT,
    author_data TEXT,
    stats_data TEXT,
    images_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE recreate_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    note_id INTEGER NOT NULL,
    original_title TEXT,
    original_content TEXT,
    recreated_title TEXT,
    recreated_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (note_id) REFERENCES notes (id)
);
```

**方法2：访问健康检查端点**
访问 `https://your-app.vercel.app/api/health` 会自动初始化数据库表。

### 2. 创建管理员用户

由于没有初始化脚本，需要手动创建管理员用户：

```sql
-- 插入管理员用户（密码：admin123）
INSERT INTO users (username, password_hash, email, nickname) 
VALUES ('admin', '4a8b9c2d1e3f4a5b:8f7e6d5c4b3a2918f7e6d5c4b3a2918f7e6d5c4b3a2918f7e6d5c4b3a2918f7e6d5c', 'admin@example.com', '管理员');

-- 获取用户ID并设置默认配置
INSERT INTO user_configs (user_id, config_key, config_value) VALUES 
(1, 'deepseek_base_url', 'https://api.deepseek.com'),
(1, 'deepseek_model', 'deepseek-chat'),
(1, 'deepseek_temperature', '0.7'),
(1, 'deepseek_max_tokens', '1000');
```

## 🔍 验证部署

### 1. 检查API端点

访问以下URL验证API是否正常工作：

- `https://your-app.vercel.app/api/health` - 健康检查
- `https://your-app.vercel.app/api/auth/status` - 认证状态
- `https://your-app.vercel.app` - 前端应用

### 2. 测试功能

1. **用户注册/登录**：测试用户系统
2. **笔记采集**：测试小红书链接解析
3. **DeepSeek配置**：配置并测试AI二创功能
4. **数据管理**：测试笔记列表和删除功能

## 🛠️ 故障排除

### 常见问题

**1. API调用失败**
- 检查 `vercel.json` 路由配置
- 确认API函数没有语法错误
- 查看Vercel函数日志

**2. 数据库连接失败**
- 验证 `DATABASE_URL` 环境变量
- 确认数据库服务器可访问
- 检查连接字符串格式

**3. 前端无法访问API**
- 确认API路径配置正确
- 检查CORS设置
- 验证环境变量配置

**4. Python依赖问题**
- 确认 `api/requirements.txt` 包含所有依赖
- 检查依赖版本兼容性
- 查看构建日志

### 调试方法

**1. 查看函数日志**
```bash
vercel logs <deployment-url>
```

**2. 本地测试API**
```bash
# 安装Vercel CLI
npm i -g vercel

# 本地运行
vercel dev
```

**3. 检查环境变量**
```bash
vercel env ls
```

## 📊 性能优化

### 1. 数据库优化

```sql
-- 添加索引提升查询性能
CREATE INDEX idx_notes_user_id ON notes(user_id);
CREATE INDEX idx_notes_created_at ON notes(created_at);
CREATE INDEX idx_user_configs_user_id ON user_configs(user_id);
CREATE INDEX idx_recreate_history_user_id ON recreate_history(user_id);
```

### 2. API优化

- 使用连接池管理数据库连接
- 实现API响应缓存
- 优化SQL查询语句
- 添加请求限流

### 3. 前端优化

- 启用Next.js静态生成
- 使用CDN加速静态资源
- 实现客户端缓存
- 优化图片加载

## 🔒 安全考虑

### 1. 环境变量安全

- 不要在代码中硬编码敏感信息
- 使用Vercel环境变量管理
- 定期轮换API密钥

### 2. 数据库安全

- 使用强密码
- 启用SSL连接
- 限制数据库访问IP
- 定期备份数据

### 3. API安全

- 实现请求限流
- 添加输入验证
- 使用HTTPS
- 监控异常访问

## 📈 监控和维护

### 1. 监控指标

- API响应时间
- 错误率统计
- 数据库连接状态
- 用户活跃度

### 2. 日志管理

- 配置结构化日志
- 设置错误告警
- 定期清理日志
- 分析访问模式

### 3. 备份策略

- 定期数据库备份
- 代码版本管理
- 配置文件备份
- 灾难恢复计划

## 🎯 后续优化

### 1. 功能扩展

- 添加用户权限管理
- 实现数据导出功能
- 支持批量操作
- 添加数据统计

### 2. 技术升级

- 升级到最新框架版本
- 优化数据库架构
- 实现微服务架构
- 添加缓存层

### 3. 用户体验

- 优化界面设计
- 添加移动端适配
- 实现离线功能
- 提升加载速度

---

**部署成功后，你的应用将具备：**
- ✅ 全球CDN加速
- ✅ 自动HTTPS
- ✅ 无服务器扩展
- ✅ 持续部署
- ✅ 监控和分析

**技术支持：**
- [Vercel文档](https://vercel.com/docs)
- [Next.js文档](https://nextjs.org/docs)
- [PostgreSQL文档](https://www.postgresql.org/docs/)

祝你部署成功！🎉