from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)

def test_create_course_missing_field_returns_422():
    resp = client.post('/courses', json={"user_id": 1})
    assert resp.status_code == 422

def test_create_course_success_returns_201():
    resp = client.post('/courses', json={
        "user_id": 1, "course_name": "操作系统", "course_teacher": "张老师"
    })
    assert resp.status_code == 201
    assert resp.json()["course_id"] == 1