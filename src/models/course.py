from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column,relationship
from src.db import Base

if TYPE_CHECKING:                                                # 避免两个模型互相 import 造成循环
    from src.models.document import Document

class Course(Base):
    __tablename__ = "course"                        # 对应已建的表
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # 一对多：course.documents 直接拿到它下面的文档列表
    documents: Mapped[list["Document"]] = relationship(back_populates="course")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey('user.id'), nullable=True)