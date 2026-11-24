"""初始化数据库：按 ORM 模型建表（幂等，已存在的表不会被改动）。

用法：uv run python scripts/init_db.py
说明：必须先 `import src.models`，否则 `Base.metadata` 是空的，`create_all` 什么也不会建。
注意：本脚本只建表，不迁移。模型改字段后仍需手工 ALTER（见 docs/db-schema.md 第六节）。
"""

import sys
from pathlib import Path

# 让脚本从任意目录执行都能 import 到 src/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db import Base, engine  # noqa: E402
import src.models  # noqa: F401, E402  —— 关键：注册所有模型到 Base.metadata


def main() -> None:
    Base.metadata.create_all(engine)
    print("建表完成：", ", ".join(sorted(Base.metadata.tables)))


if __name__ == "__main__":
    main()
