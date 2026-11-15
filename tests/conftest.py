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
def client(db_session):
    """把应用里的 get_db 替换成测试库会话，返回 TestClient。"""
    def override_get_db():
        yield db_session                         # 依赖注入返回测试会话

    app.dependency_overrides[get_db] = override_get_db   # 关键：覆盖真库依赖
    yield TestClient(app)                        # 交给测试发请求
    app.dependency_overrides.clear()             # 测完恢复原状，防止串到别的测试
