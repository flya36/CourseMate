from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from src.db import Base
from sqlalchemy import text, Boolean, DateTime, String, func


class User(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))   # Argon2id PHC 串，不是明文
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text('1'))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())