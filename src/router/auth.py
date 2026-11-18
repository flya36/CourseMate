from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.db import get_db
from src.schema.auth import RegisterIn
from src.service.auth import register_user,authenticate

from src.app.deps import get_current_user
from src.app.security import create_token
from src.models.user import User
from src.schema.auth import LoginIn

router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/register', status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    user = register_user(db, body)
    return {'id': user.id, 'username': user.username}   # 只回显这两个，不要回 password_hash

@router.post('/login')
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = authenticate(db, body)
    return {'access_token': create_token(user.id), 'token_type': 'bearer'}

@router.get('/me')
def me(current_user: User = Depends(get_current_user)):
    return {'id': current_user.id, 'username': current_user.username}