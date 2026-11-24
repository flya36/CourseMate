from datetime import datetime
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field

class DocumentCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    course_id:int = Field(gt=0)
    filename:str=Field(min_length=1,max_length=255)
    file_type:Literal['pptx','pdf']
    file_path:str=Field(min_length=1,max_length=500)
    file_size:int=Field(gt=0, le=50*1024*1024)   # 上限 50MB（安全红线：文件大小校验）

class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int
    course_id:int
    filename:str
    file_type:str
    file_path:str
    file_size:int
    created_at:datetime

class DocumentUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    filename: str = Field(min_length=1, max_length=255)
