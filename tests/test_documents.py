# 文档元信息 CRUD 测试
# 覆盖：创建成功 / 非法 file_type 422 / 课程不存在 404 / 查不到文档 404 / 更新+删除 / 按课程过滤


def _create_course(client, name: str) -> int:
    """辅助函数：先建一门课程，返回 id（文档必须挂在真实课程下，否则撞外键）。"""
    resp = client.post('/courses', json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


def _doc_payload(course_id: int, filename: str = "进程调度.pdf", file_type: str = "pdf") -> dict:
    """辅助函数：造一份合法的文档请求体。"""
    return {
        "course_id": course_id,
        "filename": filename,
        "file_type": file_type,
        "file_path": f"/uploads/{filename}",
        "file_size": 1024,
    }


def test_create_document_returns_201(client):
    """① 创建成功：201 + 自增 id + 自动时间戳。"""
    cid = _create_course(client, "操作系统")
    resp = client.post('/documents', json=_doc_payload(cid))
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None                  # 不写死 id
    assert data["course_id"] == cid                # 归属正确
    assert data["filename"] == "进程调度.pdf"
    assert data["created_at"] is not None          # 验证 created_at 字段拼写已修好


def test_create_document_invalid_file_type_returns_422(client):
    """② file_type 传 docx：Literal 校验拦下 → 422。"""
    cid = _create_course(client, "操作系统")
    resp = client.post('/documents', json=_doc_payload(cid, filename="坏文件.docx", file_type="docx"))
    assert resp.status_code == 422


def test_create_document_unknown_course_returns_404(client):
    """③ course_id 不存在：先校验课程 → 404，而不是撞外键报 500。"""
    resp = client.post('/documents', json=_doc_payload(99999))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "课程不存在"


def test_get_unknown_document_returns_404(client):
    """④ 查不存在的文档 id：404 + 业务文案。"""
    resp = client.get('/documents/99999')
    assert resp.status_code == 404
    assert resp.json()["detail"] == "文件不存在"


def test_update_and_delete_document(client):
    """⑤ 更新可回读 → 删除 204 → 再查 404。"""
    cid = _create_course(client, "操作系统")
    did = client.post('/documents', json=_doc_payload(cid)).json()["id"]   # 动态取 id

    # 更新 filename
    resp = client.put(f'/documents/{did}', json=_doc_payload(cid, filename="新名字.pdf"))
    assert resp.status_code == 200
    assert resp.json()["filename"] == "新名字.pdf"

    # 删除 → 204（无响应体，别调 .json()）
    assert client.delete(f'/documents/{did}').status_code == 204
    # 再查 → 404
    assert client.get(f'/documents/{did}').status_code == 404


def test_list_documents_by_course(client):
    """⑥ 回归测试：按课程过滤只能返回该课程下的文档（专门盯 Bug3）。"""
    cid_a = _create_course(client, "课程A")
    cid_b = _create_course(client, "课程B")
    client.post('/documents', json=_doc_payload(cid_a, filename="A的讲义.pdf"))
    client.post('/documents', json=_doc_payload(cid_b, filename="B的讲义.pdf"))

    resp = client.get(f'/courses/{cid_a}/documents')
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1                            # 只能有 A 的 1 条
    assert data[0]["course_id"] == cid_a             # 归属正确


def test_list_documents_pagination(client):
    """文档列表分页：建 3 份文档，每页 2 条 → 第 1 页 2 条、第 2 页 1 条。"""
    cid = _create_course(client, "分页课")
    for i in range(3):
        assert client.post('/documents', json=_doc_payload(cid, filename=f"讲义{i}.pdf")).status_code == 201

    p1 = client.get('/documents?page=1&limit=2')
    assert p1.status_code == 200
    assert len(p1.json()) == 2                     # 第 1 页满 2 条

    p2 = client.get('/documents?page=2&limit=2')
    assert p2.status_code == 200
    assert len(p2.json()) == 1                     # 最后一页只剩 1 条


def test_list_documents_out_of_range_page_returns_empty(client):
    """页码越界：返回空列表 + 200，不是 404/500。"""
    resp = client.get('/documents?page=99&limit=10')
    assert resp.status_code == 200
    assert resp.json() == []