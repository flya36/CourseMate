# CourseMate

AI 课程资料智能学习与复习助手（RAG 架构）

> 状态：开发中（V0.1 骨架已落地：/health + /courses 假数据接口、四层目录分层、2 条 pytest 通过）。安装 / 启动 / 测试章节已按当前代码核对，数据库接入后继续更新。

## 项目简介

CourseMate 是一个基于 RAG（检索增强生成）架构的课程资料智能学习与复习助手：上传 PPTX / PDF 课件后，系统保留页码 / 幻灯片溯源，支持带来源的资料问答（无资料时明确拒答，不编造）、例题 / 练习提取和复习要点整理。

核心链路：上传 → 解析（保留页码/幻灯片）→ 切分 → 向量化 → 检索 → 生成（带来源）→ 拒答兜底。

## 功能范围（MVP）

| 模块 | 说明 |
| --- | --- |
| 资料管理 | 上传 PPTX 与可提取文本的 PDF；保留文件名、课程、页码 / 幻灯片编号 |
| 资料问答 | 按课程/文档检索相关片段并生成答案，返回来源；资料不足时明确拒答 |
| 例题/练习提取 | 将课件中明确出现的例题、练习整理为固定字段，保留源幻灯片 / 页码 |
| 复习要点整理 | 按课程/课次汇总核心概念、来源证据与自测问题（辅助整理，非预测老师提问） |
| 工程化与安全 | 文件格式/大小校验、JWT 认证、资源访问控制、密钥不入库、异常可追踪、pytest 可重复运行 |
| 效果评估 | 20—30 条评测集；指标：Top-5 来源命中率、引用准确率、有依据回答率、无依据正确拒答率（核心 4 项），结构化输出通过率、端到端成功率（附加）；未测指标不预填 |

**明确不做（防失速红线）**：模型微调、多智能体 / LangGraph、MCP、OCR 全覆盖、完整前端开发、云部署付费项、第二个大型个人项目。

## 技术栈

| 层 | 选型 |
| --- | --- |
| 语言 | Python 3.14 |
| Web 框架 | FastAPI |
| 数据库 | MySQL + SQLAlchemy（ORM） |
| 向量库 | Chroma |
| LLM API | 服务商待定（计划 11 月底接入） |
| 测试 | pytest |
| 依赖管理 | uv（pyproject.toml + uv.lock） |
| 部署（后期） | Docker Compose（本地可重复启动） |

## 里程碑

| 节点 | 版本 | 验收要点 |
| --- | --- | --- |
| 11.8 | V0.1 / V0.2 | FastAPI 骨架 + 课程/文档元信息 CRUD 可持久化 |
| 11.15 | V0.3 | 认证 / 资源权限 / 文件上传，越权与非法文件有明确测试 |
| 11.22 | V0.4 | PPTX / PDF 解析，文本与页码 / 幻灯片可追溯 |
| 11.29 | V0.5 | LLM 结构化输出与例题提取，至少 10 条样例人工核验 |
| 12.6 | V0.6 | RAG 闭环：检索 → 生成 → 来源，上传后可问答 |
| 12.13 | V0.7 | 20 条评测集与真实评测记录 |
| 12.20 | V0.8 | 安全与可靠性：至少 10 条安全测试 |
| 12.27 | V1.0 | MVP 冻结：上传 / 问答 / 来源 / 例题 / 复习要点 / 基本评测 |

## 目录结构（当前实际）

```
CourseMate/
├── docs/
│   └── test-records.md          # 接口手工测试记录（6 条有效 + 2 条排除）
├── src/
│   ├── __init__.py
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py              # 应用入口：创建 FastAPI 实例并注册路由
│   ├── config/                  # 配置层（当前为空，DB / JWT 配置后续放此）
│   ├── router/                  # 路由层：只做请求转发，不含业务逻辑
│   │   ├── __init__.py
│   │   ├── course.py            # /courses 创建与列表
│   │   └── health.py            # /health 健康检查
│   ├── schema/                  # Pydantic 模型层：请求/响应校验
│   │   ├── __init__.py
│   │   └── course.py            # CourseCreate / CourseRead（extra='forbid'）
│   └── service/                 # 业务逻辑层：数据与规则
│       ├── __init__.py
│       └── course.py            # FAKE_COURSES + create/list 逻辑（id 生成在此）
├── tests/
│   └── test_courses.py          # pytest：422 缺字段 + 201 创建（2 passed）
├── .python-version
├── pyproject.toml
├── uv.lock
└── README.md
```

**分层约定**：app（组装）→ router（转发）→ service（业务）/ schema（校验）；config（配置）。目标是"改一处逻辑不需动所有文件"，例如 id 生成规则变更只改 `service/course.py`。

规划中（后续新增）：`parser/`（PPTX / PDF 解析）、`rag/`（切分 / 向量化 / 检索 / 生成）、`data/`（向量库持久化，不入库）、`.env.example`（骨架完成后生成）。

## 当前接口（V0.1，假数据）

| 方法 | 路径 | 说明 | 行为 |
| --- | --- | --- | --- |
| GET | /health | 健康检查 | 200 `{"status":"ok"}` |
| POST | /courses | 创建课程 | 201 + CourseRead（course_id 服务端生成）；缺字段 / 类型错 / 多余字段 → 422 |
| GET | /courses | 课程列表 | 200 + `list[CourseRead]`；未定义路径返回框架默认 404 |

接口文档（Swagger）：启动后访问 `http://127.0.0.1:8000/docs`。

## 安装步骤

> 依赖清单（pyproject.toml）已建立（fastapi + uvicorn），安装命令已核对可用；后续新增依赖随开发更新。

```
# 1. 克隆仓库
git clone https://github.com/flya36/CourseMate.git
cd CourseMate

# 2. 创建虚拟环境并安装依赖
uv venv
uv sync

# 3. 配置环境变量（复制模板并填写）
copy .env.example .env     # Windows
# 或：cp .env.example .env

# 4. 启动开发服务
uv run python -m uvicorn src.app.main:app --reload

# 5. 打开交互文档
# http://127.0.0.1:8000/docs
```

> **Windows 环境提示**：应用控制策略可能拦截 `uvicorn.exe` / `pytest.exe`（os error 4551），统一用 `python -m` 形式启动 / 测试（本 README 命令已采用）；不要用 VS Code 播放键直接运行 `src/app/main.py`（脚本式启动与包式导入不兼容）。

前置依赖：本地 MySQL（已安装）。需提前创建数据库（如 `coursemate`），建库 SQL 与初始化说明将随 V0.2 补充。

## 环境变量配置

复制 `.env.example` 为 `.env` 后填写。**所有密钥与密码只通过环境变量读取，不写入代码或仓库**（`.gitignore` 已忽略 `.env`）。

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| DB_HOST | MySQL 地址 | 127.0.0.1 |
| DB_PORT | MySQL 端口 | 3306 |
| DB_USER | MySQL 用户名 | `<你的用户名>` |
| DB_PASSWORD | MySQL 密码 | `<你的密码>` |
| DB_NAME | 数据库名 | coursemate |
| JWT_SECRET | JWT 签名密钥（V0.3 起使用） | `<随机长字符串>` |
| JWT_EXPIRE_MINUTES | Token 有效期（分钟） | 1440 |
| LLM_API_KEY | LLM API Key（待接入） | `<API Key>` |
| LLM_BASE_URL | LLM 服务商 Base URL（待定） | `<待填>` |
| LLM_MODEL | 模型名（待定） | `<待填>` |
| CHROMA_PERSIST_DIR | Chroma 持久化目录 | ./data/chroma |

> 变量名随开发推进可能调整；`.env.example` 会在骨架建立后同步生成并核对。

## 测试方法

- 框架：pytest；运行命令：`uv run python -m pytest -v`（项目根目录执行）
  - 注：若 `pytest.exe` 被应用控制策略拦截（os error 4551），`python -m pytest` 可绕开（与 uvicorn 同理）
- 约定：从第 0 周起，每个新功能同步补最小 pytest 用例（随功能累积），1 月只做集成与回归完善
- 当前状态：2 条用例已建立并通过（2 passed）：缺字段 → 422、正常创建 → 201；手工接口测试记录见 `docs/test-records.md`（6 条有效 + 2 条排除，含"多余字段被静默忽略"发现，已通过 `extra='forbid'` 修复）

## Demo 与评测

- Demo 截图：已入仓库（`docs/demo/`，4 张：接口总览、POST 201、GET 200、422 校验失败）；12 月底用 AI 辅助生成简单演示页
- 评测数据：**未测**。计划建立 20—30 条评测集，口径为 Top-5 来源命中率、引用准确率、有依据回答率、无依据正确拒答率（核心 4 项），及结构化输出通过率、端到端成功率（附加）。指标全部真实测得，未测标未测，不预填。

## 已知局限与安全说明

已知局限（当前阶段）：

- 仅支持 PPTX 与可提取文本的 PDF，不支持扫描件 OCR
- LLM 服务商未定；前端为简化演示页，非完整产品前端
- 性能与评测指标尚未测得

安全设计（红线，随开发落实并提供测试证据）：

- 密钥/密码仅从 `.env` 读取，仓库已忽略 `.env`
- Pydantic 输入校验启用 `extra='forbid'`，多余字段直接 422 拒绝（已落地于 CourseCreate）
- 文件上传带格式与大小校验，不执行上传内容
- 资源按用户/课程归属隔离，含越权访问测试
- Prompt 注入防护：课件文本视为待分析内容，不当作系统指令，含注入测试
- 日志不打印 Token / 密钥等敏感信息，异常返回不泄露内部堆栈

## Roadmap（简版）

- 当前：FastAPI 骨架 + /health + /courses 假数据接口 + 四层目录分层 + 2 条 pytest（10.28—10.30 已落地；V0.2 接入 MySQL 持久化，11.8）
- 11 月：认证 / 上传 / 解析（V0.3 / V0.4）
- 12 月：LLM 结构化输出、RAG 闭环、评测、安全加固（V0.5—V0.8）
- 12.27：MVP V1.0 冻结
