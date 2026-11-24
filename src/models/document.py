from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, DateTime,ForeignKey,String,func
from sqlalchemy.orm import Mapped,mapped_column, relationship
from src.db import Base

if TYPE_CHECKING:
    from src.models.course import Course

class Document(Base):
    __tablename__ = 'document'
    id:Mapped[int]=mapped_column(primary_key=True,autoincrement=True)
    course_id:Mapped[int]=mapped_column(ForeignKey('course.id'))
    filename:Mapped[str]=mapped_column(String(255))
    file_type:Mapped[str]=mapped_column(String(20))
    file_path:Mapped[str]=mapped_column(String(500))
    file_size:Mapped[int]=mapped_column(BigInteger)
    created_at:Mapped[datetime]=mapped_column(DateTime,server_default=func.now())

    # 多对一的反向：document.course 直接拿到所属课程对象
    course: Mapped["Course"] = relationship(back_populates="documents")
    owner_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)   # 归属：NOT NULL 由 DB 兜底