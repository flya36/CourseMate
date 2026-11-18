from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.user import User
from src.schema.auth import LoginIn, RegisterIn
from src.service.password import hash_password,needs_rehash, verify_password

from sqlalchemy import select

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


DUMMY_HASH = hash_password('coursemate-dummy-password')

LOGIN_FAILED = HTTPException(
    status_code=401,
    detail='用户名或口令错误',
    headers={'WWW-Authenticate': 'Bearer'},
)

def authenticate(db:Session,data:LoginIn)->User:
    user = db.execute(select(User).where(User.username == data.username)).scalar_one_or_none()

    if user is None:
        verify_password(DUMMY_HASH,data.password)
        raise LOGIN_FAILED

    if not verify_password(user.password_hash,data.password):
        raise LOGIN_FAILED

    if not user.is_active:
        raise LOGIN_FAILED

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password)
        db.commit()

    return user