# CourseMate 安全说明（V0.3）

> 记录于 2026-11-24，对应 V0.3「认证 + 资源归属隔离 + 安全文件上传」。
> 原则：只写已实现并有测试覆盖的结论；没做的写进「已知局限」，不写成「已解决」。

## 一、认证与授权

| 场景 | 状态码 | 含义 | 实现位置 |
| --- | --- | --- | --- |
| 没带 token / token 无效或过期 | 401 | 不知道你是谁 | `src/app/deps.py`（`HTTPBearer(auto_error=False)` + `decode_token`） |
| 带 token 但资源不属于你 | 403 | 知道你是谁，但你不能 | `service/course.py` 的 `_ensure_owner`，被 course/document 两侧复用 |
| 资源 id 不存在 | 404 | 先判存在，再判归属 | `get_course` / `get_document` 中 404 在 403 之前 |

- 密码只存 Argon2id PHC 串（`String(255)`），登录失败统一文案「用户名或口令错误」，不区分“用户不存在”与“密码错”。
- JWT：HS256，claims `sub`(str)/`iat`/`exp`，密钥来自 `.env` 的 `SECRET_KEY`，代码中无明文。
- 归属过滤一律在 **service** 层用 `WHERE owner_id = ?` 完成，不在 router 里 `if` 判断；service 函数签名强制带 `current_user` 且不给默认值，漏传即报错而不是静默放行。

## 二、文件上传

三层校验，任一层不过即拒，顺序固定：

| 层 | 判据 | 挡什么 | 失败码 |
| --- | --- | --- | --- |
| 1 后缀 | `ALLOWED_EXT = {.pdf, .pptx}` | `.exe`、`.php`、无后缀 | 415 |
| 2 体积 | `read(MAX_SIZE + 1)`，上限 20MB | 超大文件，且内存占用被钉在 20MB+1 | 413 |
| 3 真实类型 | PDF 找 `%PDF-`；PPTX 须是 zip 且含 `ppt/presentation.xml` | 改后缀的 exe、纯 zip 冒充 pptx | 415 |

- **`Content-Type` 不作为判据**，客户端可随意伪造；最多用于日志。
- 校验失败时磁盘上不留任何文件：课程归属（404/403）在落盘**之前**判断，写库失败则回删已落盘文件。
- 不执行上传内容：不 import、不 eval、不打开；`uploads/` 中的文件按数据对待。

## 三、路径安全

- 落盘名由服务端生成：`uploads/<uuid4().hex>.<ext>`，与用户输入零关系，因此路径穿越在结构上不成立。
- 用户提供的 `filename` 只做展示：取 basename（同时处理 `\` 与 `/`）、去控制字符、截 255，写入 `filename` 列，绝不参与路径拼接。
- `file_path` 入库前校验：非绝对路径、首段必须是 `uploads`、不得含 `..`（三条同时满足），防止绕过上传接口直接写一条指向任意路径的元信息。
- 删除文档：先提交 DB 再删文件（避免“文件没了、行还在”）；路径经 `resolve_path` 解析，要求仍位于 `uploads/` 之内。

## 四、已知局限（未修，写清而不是遮掩）

1. `DocumentCreate.file_size` 仍由客户端自报，未与落盘文件 `stat().st_size` 核对；V0.4 解析前必须改为服务端计算。
2. `read(MAX_SIZE + 1)` 只限**单请求**内存；并发 N 个 20MB 上传，内存最坏 N×20MB。治本方案是分块读到磁盘（1MB 一块），V0.4 一并改。
3. 未做上传并发/竞态压测；同名课程并发创建的 409 依赖 DB 唯一约束，未单独验证。
4. 附件内容未做恶意文件扫描（如 PDF 内嵌 JS）；V0.3 范围外，若对外开放需前置扫描。
5. 审计日志未做：目前只记录业务异常，没有独立的“谁在什么时候上传/删除了什么”的日志表。

## 五、待办（按 V0.3 → V0.4 顺序）

- [x] `owner_id` 收紧为 `NOT NULL`（模型 + 两库 ALTER 已完成，DB 实测 `NO`）
- [x] `scripts/init_db.py` 纳入 README 的首次启动步骤（README「4. 建表」已改为 `uv run python scripts/init_db.py`）
- [ ] 上传元信息（`file_size`）改由服务端计算
- [ ] 分块写盘替代一次性 `read()`
- [ ] 删除课程前必须先删文档（DB `RESTRICT` 已保证），删除联动目前只覆盖 document 层
