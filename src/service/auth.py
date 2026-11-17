from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.user import User
from src.schema.auth import RegisterIn
from src.service.password import hash_password

def register_user(db: Session, data: RegisterIn) -> User:
    user = User(username=data.username, password_hash=hash_password(data.password))
    db.add(user)
    try:
        db.commit()                 # 唯一索引在这里生效
    except IntegrityError:
        db.rollback()               # 必须回滚，否则会话处于脏状态
        raise HTTPException(status_code=409, detail='该用户名不可用')
    db.refresh(user)
    return user
