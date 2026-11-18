from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.app.security import decode_token
from src.db import get_db
from src.models.user import User

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer(auto_error=False)   # auto_error=False 是关键

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='未认证或凭证无效',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    if credentials is None:
        raise exc
    user_id = decode_token(credentials.credentials)   # 这里已经帮你剥掉 Bearer 前缀
    if user_id is None:
        raise exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise exc
    return user