import pytest                                    # 测试框架
from fastapi.testclient import TestClient        # 不需要启动服务就能调接口的测试客户端
from sqlalchemy import create_engine             # 建测试库的连接引擎
from sqlalchemy.orm import sessionmaker          # 测试会话工厂
from urllib.parse import quote_plus              # 密码特殊字符编码

from src.app.main import app                     # 你的 FastAPI 应用
from src.config.settings import settings         # 复用 .env 的账号密码（不硬编码）
from src.db import Base, get_db                  # Base 建表用；get_db 要被替换掉


# 测试库连接串：库名换成 coursemate_test，账号密码仍从 .env 读
TEST_DATABASE_URL = (
    f"mysql+pymysql://{settings.db_user}:{quote_plus(settings.db_password)}"
    f"@{settings.db_host}:{settings.db_port}/coursemate_test"
)

test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture
def db_session():
    """每个测试独立：建表 → 给会话 → 测完拆表（保证下个测试从干净状态开始）。"""
    Base.metadata.create_all(test_engine)        # 建表（模型已在 import 时注册到 Base）
    session = TestSessionLocal()                 # 新建测试会话
    try:
        yield session                            # 交给测试使用
    finally:
        session.close()                          # 关会话
        Base.metadata.drop_all(test_engine)      # 拆表，清掉本测试的数据


@pytest.fixture
def _api_with_test_db(db_session):
    """把应用里的 get_db 换成测试库会话，供下面两个客户端 fixture 复用。"""
    def override_get_db():
        yield db_session                         # 依赖注入返回测试会话

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()             # 测完恢复原状，防止串到别的测试


@pytest.fixture
def raw_client(_api_with_test_db):
    """未登录的客户端：专用来测 401、或用显式 headers 冒充别人。"""
    return TestClient(app)


@pytest.fixture
def client(_api_with_test_db):
    """已登录的客户端：注册 tester → 登录 → token 挂到默认请求头。

    注意：client 与 raw_client 是两个独立的 TestClient 实例，
    请求头互不影响；同一条用例里可以同时用它们区分"有 token / 没 token"。
    """
    c = TestClient(app)
    c.post('/auth/register', json={'username': 'tester', 'password': 'Passw0rd!'})
    r = c.post('/auth/login', json={'username': 'tester', 'password': 'Passw0rd!'})
    c.headers.update({'Authorization': f"Bearer {r.json()['access_token']}"})
    return c
