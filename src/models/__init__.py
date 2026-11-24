"""ORM 模型包。

集中导入所有模型，作用有两个：
1. 任何 `import src.models` 的地方，`Base.metadata` 里就自动有全部表（`create_all` 依赖这一点）
2. 让建表脚本不必逐个 import 模块，漏一个表也不至于静默少建
"""

from src.models.course import Course
from src.models.document import Document
from src.models.user import User

__all__ = ["Course", "Document", "User"]
