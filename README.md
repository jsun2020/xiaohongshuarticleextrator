# 小红书数据研究院

一个完整的小红书笔记数据采集、二创和管理系统，集成了数据采集、AI二创、可视化管理等功能。

**🚀 现已支持 Vercel 部署！** 查看 [Vercel 部署指南](./VERCEL_DEPLOYMENT.md)

## ✨ 功能特性

- 📝 **数据采集**: 输入链接自动提取笔记信息
- 💾 **数据存储**: SQLite数据库持久化存储  
- 📊 **数据管理**: 可视化界面查看和管理笔记
- 🤖 **AI二创**: 基于DeepSeek API的智能笔记重创
- 📋 **历史记录**: 完整的二创历史追踪和管理
- 🔄 **实时同步**: 前后端实时数据交互
- 🔐 **用户认证**: 简洁的登录界面保护数据安全

## 🛠️ 技术栈

### 后端
- **Python Serverless Functions** - Vercel兼容的无服务器函数
- **SQLite/云数据库** - 数据库（支持多种数据库）
- **DeepSeek API** - AI二创服务
- **JWT认证** - 无状态认证系统
- **Requests** - HTTP请求库

### 前端  
- **Next.js 14** - React框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **Radix UI** - 组件库
- **Lucide React** - 图标库

### 部署
- **Vercel** - 全栈部署平台
- **Serverless架构** - 自动扩缩容
- **全球CDN** - 快速访问

## 🚀 快速开始

### 部署选项

#### 选项1：Vercel 部署（推荐）
1. Fork 本仓库到你的 GitHub
2. 在 [Vercel](https://vercel.com) 中导入项目
3. 设置环境变量 `JWT_SECRET`
4. 自动部署完成！

详细步骤请查看 [Vercel 部署指南](./VERCEL_DEPLOYMENT.md)

#### 选项2：本地开发

### 前置要求

- Python 3.7+
- Node.js 16+
- npm 或 yarn

### 启动步骤

#### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装Node.js依赖  
npm install
```

#### 2. 启动开发服务器

```bash
# 启动Next.js开发服务器（包含前端和API）
npm run dev
```

#### 3. 访问应用

- 🎨 应用地址: http://localhost:3000
- 📡 API地址: http://localhost:3000/api
- 📚 健康检查: http://localhost:3000/api/health

## 🔑 登录信息

系统提供以下测试账号：

- **管理员**: `admin` / `admin123`
- **普通用户**: `user` / `user123`

## 📖 使用指南

### 1. 数据采集

1. 登录系统后，进入"数据采集"页面
2. 粘贴小红书笔记链接（支持多种格式）
3. 点击"开始采集"按钮
4. 系统自动提取并保存笔记信息

**支持的链接格式：**
- `https://www.xiaohongshu.com/explore/...`
- `https://www.xiaohongshu.com/discovery/item/...`  
- `http://xhslink.com/...`

### 2. 内容管理

1. 切换到"内容管理"页面
2. 查看所有已采集的笔记卡片
3. 支持删除、复制ID、AI二创等操作
4. 点击"AI二创"按钮进行内容重创

### 3. AI二创功能

1. 首次使用需要配置DeepSeek API
2. 点击右上角"设置"按钮
3. 输入DeepSeek API Key和相关参数
4. 测试连接确保配置正确
5. 在笔记管理页面使用AI二创功能

### 4. 二创历史

1. 切换到"二创历史"页面
2. 查看所有AI二创记录
3. 支持原始内容与二创内容对比
4. 可复制和删除历史记录

## ⚙️ 配置说明

### DeepSeek API配置

1. 访问 [DeepSeek平台](https://platform.deepseek.com) 获取API Key
2. 在系统设置中配置API参数：
   - **API Key**: 您的DeepSeek API密钥
   - **模型**: deepseek-chat 或 deepseek-reasoner
   - **温度**: 控制创造性（0.1-1.0）
   - **最大Token**: 控制生成长度

### 环境变量

创建 `.env.local` 文件自定义配置：

```env
# 后端API地址（可选）
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## 📁 项目结构

```
├── backend/
│   ├── app.py              # Flask后端主应用
│   ├── database.py         # 数据库管理
│   ├── deepseek_api.py     # DeepSeek API集成
│   ├── xhs_v2.py          # 小红书爬虫模块
│   └── config.py          # 配置管理
├── src/
│   ├── app/               # Next.js应用页面
│   ├── components/        # React组件
│   └── lib/              # 工具函数和API
├── config.json           # 应用配置文件
├── start_app.py         # 一键启动脚本
└── README.md           # 项目说明
```

## 🗄️ 数据库结构

系统使用SQLite数据库，包含以下主要表：

- **notes** - 笔记主表
- **authors** - 作者信息
- **note_stats** - 互动数据
- **tags** - 标签管理
- **note_images/videos** - 媒体文件
- **recreate_history** - 二创历史记录

## 🔧 API接口

### 认证接口
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出
- `GET /api/auth/status` - 检查登录状态

### 笔记接口
- `POST /api/xiaohongshu/note` - 采集笔记
- `GET /api/xiaohongshu/notes` - 获取笔记列表
- `DELETE /api/xiaohongshu/notes/{id}` - 删除笔记

### AI二创接口
- `POST /api/xiaohongshu/recreate` - AI二创笔记
- `GET /api/xiaohongshu/recreate/history` - 获取历史记录
- `DELETE /api/xiaohongshu/recreate/history/{id}` - 删除历史

### 配置接口
- `GET/POST /api/deepseek/config` - DeepSeek配置管理
- `POST /api/deepseek/test` - 测试API连接

## 🐛 常见问题

### 1. 前端无法访问后端
- 检查后端服务是否启动（端口5000）
- 确认防火墙设置
- 检查CORS配置

### 2. 数据采集失败
- 检查链接格式是否正确
- 确认网络连接正常
- 查看后端日志错误信息
- 如果显示"数据采集成功但数据库保存失败"，通常是数据格式问题，已在最新版本中修复

### 3. AI二创不工作
- 检查DeepSeek API Key是否正确
- 确认API余额充足
- 测试API连接状态

### 4. 数据库错误
- 删除数据库文件重新初始化
- 检查磁盘空间
- 确认文件权限

## 📞 技术支持

如果遇到问题，请检查：

1. **日志信息**: 查看终端输出的错误信息
2. **网络连接**: 确保能正常访问小红书和DeepSeek API
3. **依赖版本**: 确认所有依赖都正确安装
4. **端口占用**: 确认3000和5000端口未被占用

## 📄 许可证

本项目仅供学习研究使用，请遵守相关法律法规和平台服务条款。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

---

**⚠️ 免责声明**: 本工具仅用于学习和研究目的，请遵守小红书平台的使用条款和相关法律法规。