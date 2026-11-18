from pydantic import BaseModel, Field,field_validator

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)   # Argon2 无 72 字节限制，放心给 128
    @field_validator('username', mode='before')
    @classmethod
    def normalize_username(cls, v):
        if isinstance(v, str):
            v = v.strip().lower()       # 去首尾空格 + 统一小写
        return v

class LoginIn(BaseModel):
    username:str = Field(min_length=1,max_length=50)
    password:str = Field(min_length=1,max_length=128)

    @field_validator('username', mode='before')
    @classmethod
    def normalize_username(cls, v):
        if isinstance(v, str):
            v = v.strip().lower()
        return v