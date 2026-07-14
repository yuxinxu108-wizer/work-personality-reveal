# 实习证据向导

这是一个面向产品 / 运营实习准备的 Web 工具。当前正式前端已经切换为 Vite + React 高保真页面，和本地演示地址 `http://127.0.0.1:5174/` 看到的是同一版。

产品主流程：

```text
首页
→ 选择当前求职状态
→ 岗位理解
→ 输入真实经历
→ AI 追问与证据匹配
→ 输出作品集结构、简历 bullet、面试讲述提纲
```

“不知道方向”路径会调用 FastAPI + SQLite 的真实测评接口，拉取 25 道题并提交答案生成方向结果。

## 技术栈

- 前端：Vite、React、Tailwind、Lucide、Recharts
- 后端：FastAPI
- 数据库：SQLite，本地默认 `data/app.db`
- AI：Vite dev middleware 调用 OpenAI 或 DeepSeek，配置在 `.env.local`

## 项目入口

前端入口：

```text
index.html
src/main.tsx
src/app/App.tsx
```

后端入口：

```text
backend/app/main.py
```

旧版静态前端目录已移除，当前仓库只保留高保真 React 前端入口。

## 本地启动

安装前端依赖：

```bash
npm install
```

创建后端 Python 环境并安装依赖：

```bash
npm run setup
```

启动 FastAPI 后端：

```bash
npm run backend
```

另开一个终端启动前端：

```bash
npm run dev
```

打开：

```text
http://127.0.0.1:5174/
```

后端健康检查：

```text
http://127.0.0.1:8000/api/health
```

## AI 配置

复制示例配置：

```bash
cp .env.local.example .env.local
```

如果使用 DeepSeek：

```text
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的 DeepSeek key
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

`.env.local` 已被 git 忽略，不要提交真实 API key。

## 数据库

本地 SQLite 文件是：

```text
data/app.db
```

如果本地没有数据库，可以先运行：

```bash
npm run db:seed
```

当前后端提供的关键接口：

```text
GET  /api/health
GET  /api/questions
POST /api/assessment/submit
GET  /api/evidence/{direction_key}
```

前端方向测评路径会默认请求：

```text
http://127.0.0.1:8000
```

如需改地址，设置：

```text
VITE_ASSESSMENT_API_BASE=http://127.0.0.1:8000
```

## 验证

前端测试：

```bash
npm test
```

前端构建：

```bash
npm run build
```

后端测试：

```bash
npm run backend:test
```

全量验证：

```bash
npm run verify
```

## 说明

- `node_modules/`、`dist/`、`.env.local`、`data/app.db` 不进入 Git。
- 当前产品重点是目标岗位理解、真实经历证据匹配和求职材料生成。
