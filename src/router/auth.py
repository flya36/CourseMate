from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.db import get_db
from src.schema.auth import RegisterIn
from src.service.auth import register_user

router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/register', status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    user = register_user(db, body)
    return {'id': user.id, 'username': user.username}   # 只回显这两个，不要回 password_hash
