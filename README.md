# 清网同行 THUCourt

清华大学网球社区课程大作业。项目把场地时段交换、约球、比赛记录、球友反馈和私有 AI 训练建议放在一个移动端友好的网站中。预约转让和付款由用户在线下完成；平台只提供信息展示与站内联系。

## 已实现

- **身份与隐私**：Django Session + CSRF；真实姓名、学号提交后必须由管理员手动审核；未审核账号不能访问社区；公开资料不返回身份材料。
- **场地与约球**：紫荆 14 片、北馆 4 片；上海时区今天及未来三天；08:00–22:00 共 14 个一小时格；列表/网格、买场、转场、换场、约球、筛选、需求状态和创建者删除。
- **社区**：搜索认证球友、好友申请、任意认证学生之间的站内消息、拉黑、匿名 1–5 星行为评分、仅目标本人可见的技术反馈。
- **比赛与排名**：单打/双打、逐盘比分、7:6 抢七、决胜抢十、对手确认；全部确认后事务性更新对应积分，胜 +10、负 −10、和局 0，幂等且已确认记录不可修改。
- **私有 AI 教练**：证据只从当前用户读取，汇总自报水平、匿名反馈、确认比赛、媒体观察和历史计划；图片校验、视频 60 秒/100 MB 限制、最多 8 帧抽取、额度、失败重试、结构化计划保存和删除。
- **两种模型模式**：默认 `AI_PROVIDER=demo` 是明确标注的离线规则演示，不声称理解图片；配置 `remote`、模型名和 API Key 后才向 HTTPS 模型服务发请求。
- **后台**：Django Admin 审核、配置场地、查看只读比赛；过期需求和私有媒体清理命令。

## 从零运行

要求 Python 3.12+、Node.js 20+、npm。默认使用 SQLite，不需要 PostgreSQL/Redis；生产部署建议使用 PostgreSQL、Redis 和 HTTPS。

```bash
git clone git@github.com:paulinxu/thucourt.git
cd thucourt
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.lock.txt
cp .env.example .env
python backend/manage.py migrate
python backend/manage.py seed_demo
python backend/manage.py runserver 8000
```

另开终端构建并启动网页：

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 <http://127.0.0.1:5173>。演示账号 `alice`、`bob`、`carol`、`dave`，默认密码为 `court-demo-2026`；管理员账号为 `admin`，密码读取 `ADMIN_PASSWORD`。演示数据是合成数据，不代表真实学籍审核。

也可以只验证生产构建：

```bash
cd frontend && npm run build
```

## 配置模型和微信

复制 `.env.example`，生产至少修改 `SECRET_KEY`、关闭 `DEBUG`/`DEMO_MODE`、设置 `ALLOWED_HOSTS` 和安全 Cookie。`DATABASE_URL` 接受 PostgreSQL URL。微信网站登录需要开放平台网站应用的 `WECHAT_APP_ID`、`WECHAT_APP_SECRET` 和回调地址；未配置时，登录页会明确提示，不会伪装成已接入。

远程 AI 需要：

```dotenv
AI_PROVIDER=remote
AI_API_KEY=...
AI_MODEL=...
AI_BASE_URL=https://api.openai.com/v1
```

用户必须在个人中心明确同意。服务端会限制每日用户额度、全局调用次数、超时和重试；模型不能写数据库或保存训练计划，只有用户点击保存后才持久化。

## 测试和质量检查

```bash
python -m pytest --junitxml=artifacts/backend-tests.xml
ruff check backend
ruff format --check backend
cd frontend && npm run build && npm audit
```

当前验收覆盖 73 个后端测试：权限、CSRF、微信 state、防重复学号、时区日期、场地网格、需求生命周期、消息幂等、拉黑、反馈私有性、比分规则、确认竞态、积分幂等、上传边界、AI 证据和额度。SQLite 会跳过一个仅 PostgreSQL 行锁可验证的并发测试；部署到 PostgreSQL 后应运行该测试。

## 目录

```text
backend/                 Django + DRF API、模型、服务、迁移、测试
frontend/                React + TypeScript + Vite 移动端网页
docs/zh/                 课程方案英文说明的中文整理版
deploy/                  Docker Compose 与生产容器配置
scripts/                 本地检查脚本
objective.md ...         原始英文设计材料（保留原文）
```

API 文档仅对管理员开放：`/api/docs/`；健康检查：`/api/health/`。生产部署和数据清理见 [docs/zh/部署与验收.md](docs/zh/部署与验收.md)。

## 课程材料与范围说明

课程 PDF 要求 10 月 30 日提交设计方案、11 月 13 日初步实现、12 月 25 日最终展示；本仓库保留原始方案，并在 [docs/zh/课程方案总览.md](docs/zh/课程方案总览.md) 整理实现对应关系。微信小程序不是本次网站交付范围，使用同一 API 的后续客户端可以另行开发。
