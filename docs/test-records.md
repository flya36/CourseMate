# CourseMate 接口测试记录

- 来源：10.29 计划补做（2026-11-01 执行）
- 覆盖场景：缺字段 / 无效参数（类型错误）/ 未知资源 / 多余字段 / 正常路径
- 被测接口：`http://127.0.0.1:8000/courses`（本地 uvicorn 服务）

## 有效记录（6 条）

| # | 接口 | 输入 | 实际返回 | 结论 |
|---|---|---|---|---|
| 1 | POST /courses | `{"user_id":1,"course_name":"123","course_teacher":"x"}` | 201；`{"course_id":1,"user_id":1,"course_name":"123","course_teacher":"x"}` | ✅ 正常创建；course_id 由服务端生成 |
| 2 | POST /courses | `{"user_id":1}` | 422；detail 指出 course_name、course_teacher 缺失（Field required） | ✅ 缺字段 → 明确错误（422） |
| 3 | POST /courses | `{"user_id":1,"course_name":123,"course_teacher":"x"}` | 422；course_name 类型错误（string_type） | ✅ 无效参数 → 明确错误（422） |
| 4 | GET /courses/999 | — | 404；`{"detail":"Not Found"}` | ✅ 未知资源 → 404 |
| 5 | GET /courses | — | 200；`[{"course_id":1,"user_id":1,"course_name":"123","course_teacher":"x"}]` | ✅ 列表正常返回 |
| 6 | POST /courses | `{"user_id":1,"course_name":"x","course_teacher":"y","hack":1}` | 201；hack 字段被静默忽略 | ⚠️ 发现：多余字段未被拒绝 |

## 排除记录（客户端命令错误，非接口行为）

- 单引号包裹 JSON：cmd 不识别单引号，body 被整体当作字符串发送，返回 `model_attributes_type`，属命令写法问题
- 命令中第二个 `-d` 引号未闭合：返回 JSON decode error + `curl: (3) URL rejected`，请求未正确发出

以上两条不反映接口行为，不计入测试记录。

## 发现与建议

1. **多余字段被静默接受**（记录 6）：Pydantic 默认 `extra='ignore'`。建议在 `CourseCreate` 增加
   `model_config = ConfigDict(extra='forbid')`，将多余字段改为 422 拒绝（待决定是否修复，可作 10.29"修复一个真实 Bug"项）。
2. **建议固化为 pytest（2 条）**：记录 2（缺字段 → 422）与记录 4（未知资源 → 404），见 `tests/test_courses.py`。