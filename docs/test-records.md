# CourseMate 接口测试记录

> **归档说明**：以下"V0.1 假数据期"部分（2026-11-01 记录）对应的是旧接口字段（`course_id` / `user_id` / `course_teacher`），现行接口已改为 `id` / `name` / `description`，**该部分仅作历史留档，不代表当前行为**。当前行为见文末"V0.2 自动化测试记录"。

## V0.1 假数据期（2026-11-01，历史归档）

- 来源：10.29 计划补做（2026-11-01 执行）
- 覆盖场景：缺字段 / 无效参数（类型错误）/ 未知资源 / 多余字段 / 正常路径
- 被测接口：`http://127.0.0.1:8000/courses`（本地 uvicorn 服务）

### 有效记录（6 条）

| # | 接口 | 输入 | 实际返回 | 结论 |
|---|---|---|---|---|
| 1 | POST /courses | `{"user_id":1,"course_name":"123","course_teacher":"x"}` | 201；`{"course_id":1,"user_id":1,"course_name":"123","course_teacher":"x"}` | ✅ 正常创建；course_id 由服务端生成 |
| 2 | POST /courses | `{"user_id":1}` | 422；detail 指出 course_name、course_teacher 缺失（Field required） | ✅ 缺字段 → 明确错误（422） |
| 3 | POST /courses | `{"user_id":1,"course_name":123,"course_teacher":"x"}` | 422；course_name 类型错误（string_type） | ✅ 无效参数 → 明确错误（422） |
| 4 | GET /courses/999 | — | 404；`{"detail":"Not Found"}` | ✅ 未知资源 → 404 |
| 5 | GET /courses | — | 200；`[{"course_id":1,"user_id":1,"course_name":"123","course_teacher":"x"}]` | ✅ 列表正常返回 |
| 6 | POST /courses | `{"user_id":1,"course_name":"x","course_teacher":"y","hack":1}` | 201；hack 字段被静默忽略 | ⚠️ 发现：多余字段未被拒绝 |

### 排除记录（客户端命令错误，非接口行为）

- 单引号包裹 JSON：cmd 不识别单引号，body 被整体当作字符串发送，返回 `model_attributes_type`，属命令写法问题
- 命令中第二个 `-d` 引号未闭合：返回 JSON decode error + `curl: (3) URL rejected`，请求未正确发出

以上两条不反映接口行为，不计入测试记录。

### 发现与建议

1. **多余字段被静默接受**（记录 6）：Pydantic 默认 `extra='ignore'`。建议在 `CourseCreate` 增加
   `model_config = ConfigDict(extra='forbid')`，将多余字段改为 422 拒绝（待决定是否修复，可作 10.29"修复一个真实 Bug"项）。
2. **建议固化为 pytest（2 条）**：记录 2（缺字段 → 422）与记录 4（未知资源 → 404），见 `tests/test_courses.py`。

### 已知测试隐患（MySQL 阶段提醒 ⚠️）

- **隐患**：`tests/test_courses.py` 第 2 条用例断言 `course_id == 1`，它依赖两个前提：
  1. `FAKE_COURSES` 从空列表开始；
  2. pytest 按定义顺序执行（422 用例不创建数据，201 用例才创建第一条）。
- **触发时机**：MySQL 阶段（11.3 起）一旦新增"创建课程"用例，第 2 条创建的 `course_id` 会变成 2、3…，此断言必挂。
- **解决方向**（到时选用，先记下）：每个测试用独立数据源 / 每用例前清空表 / 断言改为"course_id 为正整数"而非固定值 1。
- 本条为 11.2 记录，专门留给 MySQL 阶段踩到时提醒用。
- **V0.2 更新**：该隐患已消除——V0.2 起所有用例改为"dynamic 取返回的 id"，不再断言固定值；测试库每条用例前 `create_all`、后 `drop_all`，也不依赖执行顺序。

## V0.2 自动化测试记录（2026-11-15）

- 执行环境：Windows / Python 3.14.6 / pytest 9.2.0 / MySQL 9.7.2（PyMySQL 驱动）
- 测试库：`coursemate_test`（与开发库 `coursemate` 隔离；每条用例前 `create_all`、后 `drop_all`）
- 依赖覆盖：`app.dependency_overrides[get_db]` 指向测试库会话，无需启动服务
- 执行命令：`uv run python -m pytest -v`
- 实测结果：**19 passed, 1 warning, 1.89s**（warning 为 starlette 对 httpx 的弃用提示，不影响用例）

### 用例清单（19 条）

| 文件 | 条数 | 用例（函数名） | 覆盖点 |
| --- | --- | --- | --- |
| tests/test_courses.py | 11 | test_create_course_returns_201 | 创建成功 201、id 回填、created_at 有值 |
| | | test_create_course_missing_name_returns_422 | 缺必填字段 422 |
| | | test_get_unknown_course_returns_404 | 未知 id 404 + 文案"课程不存在" |
| | | test_update_course_then_get | 更新可回读；更新未知 id 404 |
| | | test_delete_course_then_get_404 | 删除 204；再查 404 |
| | | test_list_courses_pagination | 分页 page1/limit2 → 2 条；page2 → 1 条 |
| | | test_list_courses_out_of_range_page_returns_empty | 越界页 200 + `[]` |
| | | test_create_duplicate_course_name_returns_409 | 课程名重复 → 409（全局 IntegrityError handler） |
| | | test_update_course_can_clear_description | 整体更新传 null 可清空 description |
| | | test_delete_course_with_documents_returns_409 | 删除仍有文档的课程 409，且课程与文档都在 |
| | | test_delete_course_after_documents_removed | 先删文档再删课程 204 |
| tests/test_documents.py | 8 | test_create_document_returns_201 | 创建 201、归属正确、created_at 有值 |
| | | test_create_document_invalid_file_type_returns_422 | `file_type=docx` → 422（Literal 校验） |
| | | test_create_document_unknown_course_returns_404 | 挂到不存在课程 → 404（不是撞外键 500） |
| | | test_get_unknown_document_returns_404 | 未知文档 404 + 文案"文件不存在" |
| | | test_update_and_delete_document | 更新回读 → 删除 204 → 再查 404 |
| | | test_list_documents_by_course | 按课程过滤只返回该课程文档（回归） |
| | | test_list_documents_pagination | 文档列表分页 page1/limit2 → 2 条；page2 → 1 条 |
| | | test_list_documents_out_of_range_page_returns_empty | 文档分页越界 200 + `[]` |

### 覆盖的状态码分布

| 状态码 | 用例数 | 含义 |
| --- | --- | --- |
| 200 | 6 | 正常读取 / 更新 / 分页 / 越界返空 |
| 201 | 2 | 创建成功 |
| 204 | 3 | 删除成功（含先删子再删父的完整链路） |
| 404 | 5 | 课程 / 文档 / 更新目标不存在 |
| 409 | 2 | 课程名重复、删除仍有文档的课程 |
| 422 | 2 | 缺必填字段、非法 file_type |

### 手工联调（Swagger）

- 状态：**部分执行**（有截图证据的 2 个接口 + 1 张接口清单；其余 10 个接口未留证，按"数据真实"原则不预填）
- 执行环境：本机启动 `python -m uvicorn src.app.main:app --reload`，Swagger UI `/docs`

| 接口 | 请求 | 实测响应 | 结论 | 截图 |
| --- | --- | --- | --- | --- |
| （文档页） | `/docs` | 12 条路径全部注册：`/health` 1 + `courses` 5 + `documents` 6 | 接口清单与代码一致，无幽灵接口 | `docs/demo/swagger-manual-endpoints.png` |
| GET /courses | `?page=1&limit=10` | 200；返回 5 条课程（id 2—6，字段 `id/name/description/created_at`） | 分页参数生效，返回结构稳定 | `docs/demo/swagger-manual-get-200.png` |
| DELETE /courses/{course_id} | `/courses/2` | 409；`{"detail":"该课程下还有文档，无法删除，请先删除文档"}` | 外键冲突被翻译成可行动的 409，未退化为 500 | `docs/demo/swagger-manual-delete-409.png` |

- 时间说明：DELETE 409 那张的响应头为 `date: Mon, 10 Nov 2026 12:50:50 GMT`，说明该接口 11.10 已手工调过；接口清单页与 GET /courses 为 11.16 补截
- **未留证的接口（10 个）**：POST /courses、GET /courses/{id}、PUT /courses/{id}、DELETE 空课程 204、POST /documents、GET /documents、GET /documents/{id}、GET /courses/{id}/documents、PUT /documents/{id}、DELETE /documents/{id} —— 同路径已被 pytest 19 条覆盖，但手工联调无截图，记为「未留证」，不写「已验证」

## V0.3 自动化测试记录（2026-11-24）

- 执行环境：Windows / Python 3.14 / pytest 9.2 / MySQL 9.7.2（PyMySQL）
- 测试库：`coursemate_test`；`tests/conftest.py` 提供三件套：`db_session`、`client`（注册 `tester` 并注入 Bearer，默认已登录）、`raw_client`（独立 TestClient、不带 token）
- 执行命令：`uv run pytest -q`
- 实测结果：**35 passed, 1 warning, 6.51s**（warning 仍是 starlette 对 httpx 的弃用提示）

### 用例分布（35 条）

| 文件 | 条数 | 覆盖点 |
| --- | --- | --- |
| `tests/test_auth.py` | 5 | 注册落库为 Argon2id PHC 串；重复用户名 409 且库内计数为 1；登录返回 token；密码错与用户不存在同一文案；`/auth/me` 无 token 401 |
| `tests/test_courses.py` | 12 | 课程 CRUD / 分页 / 409 / 422；**B 删 A 的课程 → 403，同用例再断言不带 token → 401，最后确认课程仍在** |
| `tests/test_documents.py` | 18 | 文档 CRUD / 分页 / 422 / 404；B 删 A 的文档 403 + 列表互不可见；上传 8 条（见下）；全链路 1 条 |

### 上传与归属相关用例（9 条）

| 用例 | 输入 | 期望 | 覆盖点 |
| --- | --- | --- | --- |
| `test_upload_exe_renamed_pdf_rejected` | `evil.pdf`，内容 `MZ\x90...` | 415 | 后缀过、魔数不过 |
| `test_upload_fake_pdf_rejected` | `note.pdf`，纯文本 | 415 | 缺 `%PDF-` 头 |
| `test_upload_wrong_ext_rejected` | `script.exe` | 415 | 后缀白名单 |
| `test_upload_too_large_rejected` | `%PDF-` + 30 字节（把上限压到 10） | 413 | `read(MAX_SIZE+1)` 截断生效 |
| `test_upload_ok_path_is_uuid` | filename 传 `../../etc/讲义.pdf`，合法 PDF | 201 | 落盘名 uuid、`parent == uploads`、不含 `..` |
| `test_upload_pptx_ok_and_zip_not_pptx_rejected` | 真 pptx / 普通 zip 改名 | 201 / 415 | zip 不等于 pptx，须含 `ppt/presentation.xml` |
| `test_upload_requires_token` | 无 token | 401 | 上传接口不裸奔 |
| `test_upload_to_others_course_403` | B 往 A 的课程上传 | 403 | 课程归属校验，且装满前后 `uploads/` 文件集合不变 |
| `test_full_chain_login_upload_query_delete` | 建课→上传→列表→详情→删 | 201/200/204/404 | 删除后**磁盘文件同步消失**（`assert not path.exists()`） |

### 状态码分布（V0.3 新增部分）

| 状态码 | 代表用例 | 含义 |
| --- | --- | --- |
| 401 | `/auth/me` 无 token、上传无 token、B 裸删 A 的资源 | 不知道你是谁 |
| 403 | B 删 A 的课程、B 删 A 的文档、B 往 A 的课程上传 | 知道你是谁但不能 |
| 404 | 未知课程/文档 id、上传到不存在课程 | 先判存在，再判归属 |
| 413 | 超 20MB | 体积层 |
| 415 | `.exe`、伪装 pdf、普通 zip 伪装 pptx | 后缀/魔数层 |

### 未覆盖与已知局限

1. `DocumentCreate.file_size` 仍由客户端自报，未与落盘文件 `stat().st_size` 核对
2. `read(MAX_SIZE + 1)` 只限**单请求**内存；并发 N 个 20MB 上传，内存最坏 N×20MB
3. 未做并发/竞态用例（同名课程并发创建的 409 依赖 DB 唯一约束，未被单独压测）
4. `owner_id` 当前仍是 `nullable=True`，NOT NULL 收紧未做，测试库靠 `create_all` 无法验证 ALTER 结果
5. 上传接口的 Swagger 手工联调尚未留证（本轮只有 pytest）
