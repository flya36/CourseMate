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
