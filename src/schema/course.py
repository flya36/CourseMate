from pydantic import BaseModel,ConfigDict, Field

class CourseCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    user_id:int
    course_name:str
    course_teacher:str=Field(min_length=2)

class CourseRead(BaseModel):
    course_id: int
    user_id:int
    course_name:str
    course_teacher:str