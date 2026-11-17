from argon2 import PasswordHasher
from argon2.exceptions import VerificationError,VerifyMismatchError

ph = PasswordHasher(time_cost=2,memory_cost=19456,parallelism=1)

def hash_password(raw: str) -> str:
    '''加盐哈希密码'''
    return ph.hash(raw)

def verify_password(stored:str,raw: str)->bool:
    '''验证密码正确性'''
    try:
        return ph.verify(stored,raw)
    except (VerifyMismatchError,VerificationError):
        return False

def needs_rehash(stored: str) -> bool:
    '''判断是否需要rehash'''
    return ph.check_needs_rehash(stored)