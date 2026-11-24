def test_create_course_returns_201(client):
    """创建成功：201 + 返回自增 id 和自动时间戳。"""
    resp = client.post('/courses', json={"name": "操作系统", "description": "核心课"})
    assert resp.status_code == 201                 # 状态码
    data = resp.json()
    assert data["id"] is not None                  # 自增 id 已回填（不要写死 == 1）
    assert data["name"] == "操作系统"
    assert data["created_at"] is not None          # created_at 由数据库生成


def test_create_course_missing_name_returns_422(client):
    """缺必填字段：422。"""
    resp = client.post('/courses', json={"description": "只有描述"})
    assert resp.status_code == 422


def test_get_unknown_course_returns_404(client):
    """查不存在的 id：404 + 业务提示文案。"""
    resp = client.get('/courses/99999')
    assert resp.status_code == 404
    assert resp.json()["detail"] == "课程不存在"


def test_update_course_then_get(client):
    """更新成功可回读；更新不存在的 id 返回 404。"""
    created = client.post('/courses', json={"name": "数据结构"}).json()
    cid = created["id"]                            # 动态取 id，不写死

    resp = client.put(f'/courses/{cid}', json={"name": "数据结构（改）", "description": "新"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "数据结构（改）"

    assert client.put('/courses/99999', json={"name": "x"}).status_code == 404


def test_delete_course_then_get_404(client):
    """删除成功 204；删除后再查 404。"""
    created = client.post('/courses', json={"name": "临时课程"}).json()
    cid = created["id"]

    resp = client.delete(f'/courses/{cid}')
    assert resp.status_code == 204                 # 204 无响应体，别调 resp.json()

    assert client.get(f'/courses/{cid}').status_code == 404

def test_list_courses_pagination(client):
    """分页生效：建 3 门课，每页 2 条 → 第 1 页 2 条、第 2 页 1 条。"""
    for name in ["分页课A", "分页课B", "分页课C"]:
        assert client.post('/courses', json={"name": name}).status_code == 201

    p1 = client.get('/courses?page=1&limit=2')
    assert p1.status_code == 200
    assert len(p1.json()) == 2                     # 第 1 页满 2 条

    p2 = client.get('/courses?page=2&limit=2')
    assert p2.status_code == 200
    assert len(p2.json()) == 1                     # 最后一页只剩 1 条，正常


def test_list_courses_out_of_range_page_returns_empty(client):
    """页码越界：返回空列表 + 200，不是 404/500。"""
    resp = client.get('/courses?page=99&limit=10')
    assert resp.status_code == 200
    assert resp.json() == []                       # 空列表语义

def test_delete_course_with_documents_returns_409(client):
    """删除"仍有文档"的课程：409，且课程和文档都还在（没被误删）。"""
    cid = client.post('/courses', json={"name": "有文档的课"}).json()["id"]
    doc = client.post('/documents', json={
        "course_id": cid,
        "filename": "讲义.pdf",
        "file_type": "pdf",
        "file_path": "/uploads/讲义.pdf",
        "file_size": 100,
    })
    assert doc.status_code == 201                 # 文档建成功（外键指向课程）
    did = doc.json()["id"]

    resp = client.delete(f'/courses/{cid}')       # 删课程
    assert resp.status_code == 409                # 被外键拦住 → 409
    assert "文档" in resp.json()["detail"]        # 有业务提示

    # 关键：确认"什么都没被删掉"
    assert client.get(f'/courses/{cid}').status_code == 200
    assert client.get(f'/documents/{did}').status_code == 200


def test_delete_course_after_documents_removed(client):
    """先删文档、再删课程：应该成功 204。"""
    cid = client.post('/courses', json={"name": "先删子后删父"}).json()["id"]
    did = client.post('/documents', json={
        "course_id": cid, "filename": "子.pdf", "file_type": "pdf",
        "file_path": "/uploads/子.pdf", "file_size": 100,
    }).json()["id"]

    assert client.delete(f'/documents/{did}').status_code == 204    # 先删子
    assert client.delete(f'/courses/{cid}').status_code == 204      # 再删父 → 成功


def test_create_duplicate_course_name_returns_409(client):
    """重名课程：第一次 201，第二次被唯一约束拦下 → 409（不再是 500）。"""
    assert client.post('/courses', json={"name": "唯一课"}).status_code == 201
    resp = client.post('/courses', json={"name": "唯一课"})
    assert resp.status_code == 409
    assert resp.json()["detail"]                    # 有提示，且是 {detail} 格式


def test_update_course_can_clear_description(client):
    """整体更新语义：description 传 null 应该真的清零，而不是保留旧值。"""
    cid = client.post('/courses', json={"name": "清空测试", "description": "旧描述"}).json()["id"]

    resp = client.put(f'/courses/{cid}', json={"name": "清空测试", "description": None})
    assert resp.status_code == 200
    assert resp.json()["description"] is None       # 旧值被清掉

def test_user_b_cannot_delete_user_a_course(client, raw_client):
    """A 建的课程，B 来删 → 403；完全不带 token → 401；两码必须分开出现。"""
    course_id = client.post('/courses', json={'name': 'A的课', 'description': 'x'}).json()['id']

    # B 单独登录，token 通过显式 headers 使用，不动 raw_client 的默认请求头
    raw_client.post('/auth/register', json={'username': 'userb', 'password': 'Passw0rd!'})
    tb = raw_client.post('/auth/login', json={'username': 'userb', 'password': 'Passw0rd!'}).json()['access_token']

    r403 = raw_client.delete(f'/courses/{course_id}', headers={'Authorization': f'Bearer {tb}'})
    r401 = raw_client.delete(f'/courses/{course_id}')

    assert r403.status_code == 403
    assert r401.status_code == 401
    assert client.get(f'/courses/{course_id}').status_code == 200   # 两次拒绝都没造成删除
