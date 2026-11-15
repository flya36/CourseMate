from pydantic import BaseModel,ConfigDict, Field
from datetime import datetime

class CourseCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None

class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)   # ← 关键开关
    id: int
    name: str
    description: str | None
    created_at: datetime