from datetime import datetime,timedelta,timezone
import jwt
from src.config.settings import settings

ALGORITHM = 'HS256'

def create_token(user_id:int)->str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub':str(user_id),
        'iat':now,
        'exp':now + timedelta(minutes=settings.token_expire_minutes),
    }
    return jwt.encode(payload,settings.secret_key,algorithm=ALGORITHM)

def decode_token(token:str)->int|None:
    try:
        payload = jwt.decode(token,settings.secret_key,algorithms=[ALGORITHM])
        return int(payload['sub'])
    except (jwt.ExpiredSignatureError,jwt.InvalidTokenError,ValueError,KeyError):
        return None