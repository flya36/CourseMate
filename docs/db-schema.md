# CourseMate 数据库设计（V0.2 现状）

> 补记于 2026-11-16。本文对应**已建成的真实表结构**（DDL 取自 `SHOW CREATE TABLE`，不是设计稿），
> 原计划 11.2 的「设计 Course/Document/Chunk 最小字段 + 写入设计文档」当时未落盘，这里补齐。

## 一、环境与约定

| 项 | 值 | 说明 |
| --- | --- | --- |
| 引擎 / 版本 | MySQL 9.7.2 / InnoDB | 事务与行级锁依赖 InnoDB，不能用 MyISAM |
| 字符集 | `utf8mb4` / `utf8mb4_0900_ai_ci` | 课件中文与 emoji 都要能存 |
| 隔离级别 | `REPEATABLE-READ`（默认） | V0.2 未改；事务相关结论据此推 |
| 主库 | `coursemate` | 开发/演示用 |
| 测试库 | `coursemate_test` | pytest 专用；每条用例前 `create_all`、后 `drop_all` |
| 连接串 | 由 `.env` 拼装（`src/config/settings.py`） | 密码经 `quote_plus` 编码；`.env` 已在 `.gitignore` |
| 表创建方式 | `Base.metadata.create_all(engine)` | **无 Alembic**，改表要手工 `ALTER`，见第六节 |

## 二、表清单

三张表：`course`（课程）→ `document`（文档）→ `chunk`（切分片段），一对多链式引用。

### 2.1 `course`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | `int` | PK, AUTO_INCREMENT | 代理主键，业务不暴露自增规律前先不管 |
| `name` | `varchar(100)` | NOT NULL, **UNIQUE** | 课程名；重名 → 409（DB 唯一约束 + service 预检双保险） |
| `description` | `varchar(255)` | NULL | 可为空；PUT 整体更新时允许传 `null` 清空 |
| `created_at` | `datetime` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 由 DB 生成，不由应用赋值 |

### 2.2 `document`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | `int` | PK, AUTO_INCREMENT | |
| `course_id` | `int` | NOT NULL, **FK → course.id** | 归属课程；索引随 FK 自动创建 |
| `filename` | `varchar(255)` | NOT NULL | **原始文件名，仅作显示元数据**；V0.3 落盘名改用内部 ID |
| `file_type` | `enum('pdf','pptx')` | NOT NULL | 见 2.4 的三层校验说明 |
| `file_path` | `varchar(500)` | NOT NULL | 服务器侧路径（V0.3 起由系统生成，不拼接用户输入） |
| `file_size` | `bigint` | NOT NULL | 字节；V0.3 上传时校验上限 |
| `created_at` | `datetime` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

### 2.3 `chunk`（表已建，**暂无 ORM 模型**）

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | `int` | PK, AUTO_INCREMENT | |
| `document_id` | `int` | NOT NULL, **FK → document.id** | 所属文档 |
| `content` | `text` | NOT NULL | 片段正文 |
| `page_number` | `int` | NOT NULL | **溯源字段**：PPTX 记 slide 序号，PDF 记页码；MVP 红线要求 |
| `chunk_order` | `int` | NOT NULL | 同文档内顺序，保证还原上下文时不错序 |
| `created_at` | `datetime` | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

**为什么先建表不给 ORM**：V0.4 才做解析，解析前没有稳定的切分策略（固定字符数？按页？按标题？）。先按计划把表结构占位，切分口径定了再写模型，避免为了“有模型”而写一个必然要改的模型。这是**有意保留**，不是遗漏。

### 2.4 `file_type` 的三层校验（别在三处写三套值）

| 层 | 实现 | 作用 |
| --- | --- | --- |
| Pydantic | `Literal['pdf','pptx']` | 请求进来就拒（422），错误信息友好 |
| ORM | `String(20)` | 只声明长度，不复制枚举 |
| DB | `enum('pdf','pptx')` | 最后一道闸；非法值写不进去 |

**代价要说清**：DB 是 enum，以后加 `.docx` 必须 `ALTER TABLE` 改枚举，而项目没有 Alembic。所以新增格式前先决定：是放宽为 `varchar` + 应用层 Literal，还是接受一次手工 ALTER。

## 三、真实 DDL（`SHOW CREATE TABLE` 原文）

```sql
CREATE TABLE `course` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `document` (
  `id` int NOT NULL AUTO_INCREMENT,
  `course_id` int NOT NULL,
  `filename` varchar(255) NOT NULL,
  `file_type` enum('pdf','pptx') NOT NULL,
  `file_path` varchar(500) NOT NULL,
  `file_size` bigint NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `course_id` (`course_id`),
  CONSTRAINT `document_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `course` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `chunk` (
  `id` int NOT NULL AUTO_INCREMENT,
  `document_id` int NOT NULL,
  `content` text NOT NULL,
  `page_number` int NOT NULL,
  `chunk_order` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `document_id` (`document_id`),
  CONSTRAINT `chunk_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

> 注：FK 未显式写 `ON DELETE`，即默认 `RESTRICT`。这正是「删除有文档的课程 → Error 1451 → 409」的来源。

## 四、外键策略：为什么是 RESTRICT，不是 CASCADE

| 策略 | 后果 | 本项目取舍 |
| --- | --- | --- |
| `CASCADE` | 删课程连带删掉文档与片段，一条 SQL 静默清空数据 | ❌ 用户只是点“删除课程”，不该顺带毁掉资料 |
| `SET NULL` | 文档变成 `course_id = NULL`，查询要处理孤儿 | ❌ 文档失去归属，溯源链断裂 |
| `RESTRICT` | 有子记录就拒绝，报 Error 1451 | ✅ 采用：数据库层拒绝，service 层翻译成 409 并给出可行动文案「请先删除文档」 |

配套约定：**先删子、再删父**（`test_delete_course_after_documents_removed` 就是这条链路的回归用例）。

## 五、索引现状与缺口

| 现状 | 来源 |
| --- | --- |
| `course`：PK(`id`)、UNIQUE(`name`) | 建表语句 |
| `document`：PK(`id`)、KEY(`course_id`) | FK 自动创建 |
| `chunk`：PK(`id`)、KEY(`document_id`) | FK 自动创建 |

**缺口（预留建议，未建，等有数据量再说）**：

- `document(course_id, created_at)`：按课程列文档并按时间排序时可避免回表排序；现在的 `KEY(course_id)` 只够等值过滤
- `chunk(document_id, chunk_order)`：V0.4 按文档取片段并保序时用；当前数据量（文档 1 条）没必要建

判断标准：先用 `EXPLAIN` 看是否出现 `Using filesort` / `Using temporary`，出现了再建，不凭感觉加索引（索引也是写放大）。

## 六、改表流程（没有 Alembic 时的纪律）

1. 先改 `src/models/*.py`
2. 手工在 `coursemate` 执行 `ALTER TABLE ...`
3. 同一句 `ALTER` 在 `coursemate_test` 也执行（测试库靠 `create_all`，但已有表的字段不会自动同步）
4. 跑 `pytest`，全绿才算改完
5. 在本文「真实 DDL」一节同步更新（否则文档第二天就是假的）

> 上 Alembic 的时机：V0.4 加解析状态字段时。届时 `create_all` 的“建表不建迁移”局限会第一次真正咬人。

## 七、V0.3 / V0.4 预留（还没建，先想清楚再动手）

| 变更 | 目的 | 注意点 |
| --- | --- | --- |
| 新表 `user`：`id` / `username` UNIQUE / `password_hash` / `created_at` | V0.3 认证 | 只存哈希（Argon2id PHC 串，`String(255)`），**不存明文**；不要加 `password` 列 |
| `document.owner_id`、`course.owner_id` → FK `user.id` | V0.3 资源归属隔离 | 唯一能验证越权的字段；不加这一列，403 无从谈起 |
| `document.parse_status`（`pending/parsed/failed`）、`page_count`、`error_reason` | V0.4 解析状态 | 失败原因要能展示给用户，别只写日志 |
| `document.original_name` 与落盘名分离 | V0.3 上传 | 落盘用 UUID，原名只作显示，避免路径穿越 |

## 八、当前数据快照（2026-11-16）

- `course`：5 条（id 2—6，含“数据结构 / 计算机网络 / 数据库系统 / 信息安全导论 / SQLAlchemy连接测试”）
- `document`：1 条（挂在 course 2 下，也是「DELETE /courses/2 → 409」的证据来源）
- `chunk`：0 条（V0.4 解析后才有）
