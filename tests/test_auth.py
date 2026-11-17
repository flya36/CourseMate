from sqlalchemy import select
from src.models.user import User

def test_register_stores_argon2_hash(client, db_session):
    r = client.post('/auth/register', json={'username': 'fengliyuan', 'password': 'Passw0rd!'})
    assert r.status_code == 201
    assert 'password_hash' not in r.json()                    # 响应不回显哈希

    row = db_session.execute(select(User).where(User.username == 'fengliyuan')).scalar_one()
    assert row.password_hash.startswith('$argon2id$')
    assert 'Passw0rd!' not in row.password_hash               # 库里没有明文

from sqlalchemy import func, select

def test_register_duplicate_username(client, db_session):
    payload = {'username': 'dup_user', 'password': 'Passw0rd!'}
    assert client.post('/auth/register', json=payload).status_code == 201
    r2 = client.post('/auth/register', json=payload)
    assert r2.status_code == 409
    assert r2.json()['detail'] == '该用户名不可用'
    count = db_session.execute(select(func.count()).select_from(User)).scalar()
    assert count == 1                      # 关键：不是 2
