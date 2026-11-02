from src.schema.course import CourseCreate,CourseRead
from src.service.course import create_course, list_courses
from fastapi import APIRouter

router = APIRouter()



# 创建新课程路由接口
@router.post('/courses',response_model=CourseRead,status_code=201)
def create_courses(course_create:CourseCreate):
    return create_course(course_create)

# 创建读取课程路由接口
@router.get('/courses',response_model=list[CourseRead])
def read_courses():
    return list_courses()