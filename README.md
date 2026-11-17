# CourseMate

AI 课程资料智能学习与复习助手（RAG 架构）

> 状态：V0.2 已落地（MySQL 持久化：课程 / 文档元信息 CRUD 共 11 个业务接口，course↔document 一对多关系，删除受外键保护返回 409，pytest 19 条全绿）。下一步 V0.3：认证 + 文件上传。

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
│   ├── test-records.md          # 接口测试记录（V0.1 历史归档 + V0.2 自动化用例）
│   └── demo/                    # Demo 截图
├── src/
│   ├── __init__.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # 应用入口：创建 FastAPI 实例、注册路由与异常处理
│   │   └── exception_handlers.py# 异常映射：业务错误 / 422 校验 / 409 冲突 / 500 兜底
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # pydantic-settings 读取 .env，拼装数据库连接串
│   ├── models/                  # ORM 模型层：表结构映射
│   │   ├── __init__.py
│   │   ├── course.py            # course 表 + documents 关系（一对多）
│   │   └── document.py          # document 表 + course 反向关系
│   ├── router/                  # 路由层：只做请求转发与参数声明，不含业务逻辑
│   │   ├── __init__.py
│   │   ├── health.py            # /health 健康检查
│   │   ├── course.py            # /courses 5 个接口
│   │   └── document.py          # /documents 6 个接口
│   ├── schema/                  # Pydantic 模型层：请求/响应校验
│   │   ├── __init__.py
│   │   ├── course.py            # CourseCreate / CourseRead（extra='forbid'）
│   │   └── document.py          # DocumentCreate / DocumentRead
│   ├── service/                 # 业务逻辑层：数据与规则
│   │   ├── __init__.py
│   │   ├── course.py            # 课程 CRUD（分页、删除保护）
│   │   └── document.py          # 文档元信息 CRUD（分页、按课程查询）
│   └── db.py                    # engine / SessionLocal / Base / get_db 依赖
├── tests/
│   ├── conftest.py              # 测试库 coursemate_test 建表清表 + client 夹具
│   ├── test_courses.py          # 课程 CRUD / 分页 / 409（11 条）
│   └── test_documents.py        # 文档 CRUD / 校验 / 分页 / 归属过滤（8 条）
├── .env.example
├── .python-version
├── pyproject.toml
├── README.md
└── uv.lock
```

**分层约定**：app（组装）→ router（转发）→ service（业务）/ schema（校验）/ models（映射）；config（配置）、db（连接）。目标是"改一处逻辑不需动所有文件"，例如分页默认条数变更只改 `service/`。

规划中（后续新增）：`parser/`（PPTX / PDF 解析）、`rag/`（切分 / 向量化 / 检索 / 生成）、`data/`（向量库持久化，不入库）。

## 当前接口（V0.2，MySQL 持久化）

| 方法 | 路径 | 说明 | 成功 | 失败 |
| --- | --- | --- | --- | --- |
| GET | /health | 健康检查 | 200 `{"status":"ok"}` | — |
| POST | /courses | 创建课程 | 201 + CourseRead | 422 校验失败；409 课程名重复 |
| GET | /courses | 课程列表（分页） | 200 + `list[CourseRead]`，参数 `page`（≥1）/ `limit`（1—100） | 422 参数越界 |
| GET | /courses/{course_id} | 查单门课程 | 200 + CourseRead | 404 课程不存在 |
| PUT | /courses/{course_id} | 整体更新课程 | 200 + CourseRead | 404；409 课程名重复 |
| DELETE | /courses/{course_id} | 删除课程 | 204 | 404；409 该课程下还有文档 |
| POST | /documents | 创建文档元信息 | 201 + DocumentRead | 422；404 课程不存在 |
| GET | /documents | 文档列表（分页） | 200 + `list[DocumentRead]`，参数 `page` / `limit` | 422 参数越界 |
| GET | /documents/{document_id} | 查单份文档 | 200 + DocumentRead | 404 文件不存在 |
| GET | /courses/{course_id}/documents | 按课程查文档 | 200 + `list[DocumentRead]` | 404 课程不存在 |
| PUT | /documents/{document_id} | 整体更新文档 | 200 + DocumentRead | 404 文档不存在；404 课程不存在 |
| DELETE | /documents/{document_id} | 删除文档 | 204 | 404 文件不存在 |

接口文档（Swagger）：启动后访问 `http://127.0.0.1:8000/docs`。

## 安装步骤

> 依赖清单见 `pyproject.toml`（fastapi / uvicorn / sqlalchemy / pymysql / pydantic-settings；dev 组 pytest + httpx），已用 uv 锁定。

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

前置依赖：本地 MySQL（已安装）。数据库需先建库并配好连接信息，见下节。

## 数据库初始化

> 首次运行或换机器时按本节执行一次。表结构由 ORM 模型定义，但**建库不能省**。

**1. 建库**（开发库 + 测试库两个；测试库给 pytest 用，避免污染开发数据）

```sql
-- Windows 下登录 MySQL 客户端：E:\MySQL\bin\mysql.exe -u root -p
create database if not exists coursemate
    default character set utf8mb4 collate utf8mb4_general_ci;

create database if not exists coursemate_test
    default character set utf8mb4 collate utf8mb4_general_ci;
```

**2. 配连接信息**

复制 `.env.example` 为 `.env`，填写 `DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME`（变量说明见下节）。密码只存在于 `.env`，`.gitignore` 已忽略该文件。

**3. 验证连通性（可选）**

```powershell
uv run python verify_db.py
```

**4. 建表**

`course` 与 `document` 两表由 ORM 模型定义：跑 pytest 时会在 `coursemate_test` 里自动 `create_all` / `drop_all`；开发库 `coursemate` 可执行一次下面的命令建表。

```powershell
uv run python -c "from src.db import Base, engine; import src.models.course, src.models.document; Base.metadata.create_all(engine); print('tables created')"
```

> 外键 `document.course_id → course.id` 为 `RESTRICT`：删除课程前必须先删其文档，否则接口返回 409。`chunk` 表属 V0.4 解析阶段，届时补 ORM 映射。

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

> 变量名随开发推进可能调整；当前 `.env.example` 只包含数据库 5 项（`DB_*`），V0.3 加入 JWT 后同步补齐。

## 测试方法

- 框架：pytest；运行命令：`uv run python -m pytest -v`（项目根目录执行）
  - 注：若 `pytest.exe` 被应用控制策略拦截（os error 4551），`python -m pytest` 可绕开（与 uvicorn 同理）
- 测试库：`coursemate_test`（与开发库 `coursemate` 隔离）；每条用例前 `create_all`、后 `drop_all`，互不污染
- 依赖覆盖：`conftest.py` 用 `app.dependency_overrides[get_db]` 把真实库换成测试库，不需要启动服务
- 约定：从第 0 周起，每个新功能同步补最小 pytest 用例（随功能累积），1 月只做集成与回归完善
- 当前状态：**19 条全部通过**（约 1.9s）

| 文件 | 条数 | 覆盖 |
| --- | --- | --- |
| `tests/test_courses.py` | 11 | 创建 201 / 缺字段 422 / 未知 id 404 / 更新可回读 / 删除后 404 / 分页两页 / 越界返空 / 重名 409 / 更新可清空描述 / 删除有文档 409 / 先删子再删父 204 |
| `tests/test_documents.py` | 8 | 创建 201 / 非法 file_type 422 / 课程不存在 404 / 未知文档 404 / 更新+删除 / 按课程过滤回归 / 分页两页 / 越界返空 |

- 手工接口记录（含 V0.1 历史归档）见 `docs/test-records.md`

## Demo 与评测

- Demo 截图：已入仓库（`docs/demo/`，7 张：V0.1 接口总览、POST 201、GET 200、422 校验失败；V0.2 手工联调 12 接口清单、GET /courses 200、DELETE 有文档课程 409）；12 月底用 AI 辅助生成简单演示页
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

- 当前：V0.2 完成——MySQL 持久化 + 课程/文档 CRUD 11 个业务接口 + course↔document 一对多关系 + 删除受外键保护（409）+ 19 条 pytest（**11.15 收口**，提交 `9365661`；11.16 周复盘验收）
- 11 月：认证 / 上传 / 解析（V0.3 / V0.4）
- 12 月：LLM 结构化输出、RAG 闭环、评测、安全加固（V0.5—V0.8）
- 12.27：MVP V1.0 冻结
