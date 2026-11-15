from sqlalchemy import text

from src.db import engine

with engine.begin() as conn:   # begin() 自动提交，出错自动回滚
    conn.execute(
        text(
            "insert into `course` (`name`, `description`) "
            "values (:name, :desc)"
        ),
        {"name": "SQLAlchemy连接测试", "desc": "来自 Python 的第一次写库"},
    )

with engine.connect() as conn:
    row = conn.execute(
        text("select `id`, `name`, `created_at` from `course` order by `id` desc limit 1")
    ).first()
    print("读回结果：", row)
