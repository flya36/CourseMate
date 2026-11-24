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
        "file_path": f"uploads/{filename}",
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

    # 更新 filename（PUT 只接受 DocumentUpdate：仅 filename）
    resp = client.put(f'/documents/{did}', json={"filename": "新名字.pdf"})
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


def test_user_b_cannot_touch_user_a_document(client, raw_client):
    """A 的文档：B 删 → 403、B 不带 token → 401；别人的文档列表为空。"""
    cid = _create_course(client, "A的课")
    did = client.post('/documents', json=_doc_payload(cid)).json()["id"]

    raw_client.post('/auth/register', json={'username': 'userb', 'password': 'Passw0rd!'})
    tb = raw_client.post('/auth/login', json={'username': 'userb', 'password': 'Passw0rd!'}).json()['access_token']
    b_headers = {'Authorization': f'Bearer {tb}'}

    assert raw_client.delete(f'/documents/{did}', headers=b_headers).status_code == 403
    assert raw_client.delete(f'/documents/{did}').status_code == 401
    assert raw_client.get('/documents', headers=b_headers).json() == []      # 只看得到自己的
    assert client.get(f'/documents/{did}').status_code == 200                # 没被删掉

import io
import zipfile
from pathlib import Path

PDF_OK = b"%PDF-1.7\n%fake but header right"


def _upload(client, cid, name, data, ctype='application/pdf', headers=None):
    return client.post('/documents/upload',
                       data={'course_id': str(cid)},
                       files={'file': (name, data, ctype)},
                       headers=headers or {})


def _fake_pptx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("ppt/presentation.xml", "<p:presentation/>")
        z.writestr("[Content_Types].xml", "<Types/>")
    return buf.getvalue()


def test_upload_exe_renamed_pdf_rejected(client):
    """MZ 头改名 .pdf → 415（后缀过了，魔数没过）。"""
    cid = _create_course(client, "上传课")
    resp = _upload(client, cid, "evil.pdf", b"MZ\x90\x00 this is an exe")
    assert resp.status_code == 415
    assert "PDF" in resp.json()["detail"]


def test_upload_fake_pdf_rejected(client):
    """纯文本改 .pdf，没有 %PDF- 头 → 415。"""
    cid = _create_course(client, "上传课")
    resp = _upload(client, cid, "note.pdf", b"just some text")
    assert resp.status_code == 415


def test_upload_wrong_ext_rejected(client):
    """后缀不在白名单 → 415，且不读内容就已经拒。"""
    cid = _create_course(client, "上传课")
    resp = _upload(client, cid, "script.exe", b"MZ\x90\x00")
    assert resp.status_code == 415


def test_upload_too_large_rejected(client, monkeypatch):
    """超限 → 413。用 monkeypatch 把上限压到 10 字节，避免在测试里搬 20MB。"""
    import src.router.document as rdoc
    monkeypatch.setattr(rdoc, 'MAX_SIZE', 10)

    cid = _create_course(client, "上传课")
    resp = _upload(client, cid, "big.pdf", b"%PDF-" + b"x" * 30)
    assert resp.status_code == 413


def test_upload_ok_path_is_uuid(client):
    """正常 PDF 且 filename 带 ../ → 201；库里存的是 uploads/<uuid>.pdf，用户输入不参与路径。"""
    cid = _create_course(client, "上传课")
    resp = _upload(client, cid, "../../etc/讲义.pdf", PDF_OK)
    assert resp.status_code == 201

    data = resp.json()
    path = Path(data["file_path"])
    assert data["filename"] == "讲义.pdf"              # 只留 basename
    assert path.parent == Path("uploads")              # 没逃出上传目录
    assert ".." not in data["file_path"]
    assert path.name.endswith(".pdf") and len(path.stem) == 32   # uuid4().hex
    assert path.exists()
    path.unlink()                                       # 别把测试文件留在盘上


def test_upload_pptx_ok_and_zip_not_pptx_rejected(client):
    """真 pptx 通过；普通 zip 改名 .pptx 拒。"""
    cid = _create_course(client, "上传课")
    ok = _upload(client, cid, "第1讲.pptx", _fake_pptx(),
                 'application/vnd.openxmlformats-officedocument.presentationml.presentation')
    assert ok.status_code == 201
    Path(ok.json()["file_path"]).unlink()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("readme.txt", "just a zip")
    bad = _upload(client, cid, "evil.pptx", buf.getvalue(), 'application/octet-stream')
    assert bad.status_code == 415


def test_upload_requires_token(client, raw_client):
    """不带 token → 401（上传是最贵的接口，不能裸奔）。"""
    cid = _create_course(client, "上传课")
    resp = _upload(raw_client, cid, "a.pdf", PDF_OK)
    assert resp.status_code == 401



def test_upload_to_others_course_403(client, raw_client):
    """B 往 A 的课程上传 → 403，且磁盘上不留文件。"""
    from src.service.upload import UPLOAD_DIR
    cid = _create_course(client, "A的课")
    raw_client.post('/auth/register', json={'username': 'userb', 'password': 'Passw0rd!'})
    tb = raw_client.post('/auth/login', json={'username': 'userb', 'password': 'Passw0rd!'}).json()['access_token']

    before = set(UPLOAD_DIR.glob("*"))
    resp = _upload(raw_client, cid, "a.pdf", PDF_OK, headers={'Authorization': f'Bearer {tb}'})
    assert resp.status_code == 403
    assert set(UPLOAD_DIR.glob("*")) == before      # 先校验后落盘，盘上干净
