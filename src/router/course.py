from src.schema.course import CourseCreate,CourseRead
from src.service.course import create_course, list_courses,get_course,update_course,delete_course
from fastapi import APIRouter,Depends, Query
from sqlalchemy.orm import Session
from src.db import get_db

router = APIRouter()



# 创建新课程路由接口
@router.post('/courses',response_model=CourseRead,status_code=201)
def create_courses(course_create:CourseCreate,db:Session = Depends(get_db)):
    return create_course(db,course_create)

# 读取课程路由接口
@router.get('/courses',response_model=list[CourseRead])
def read_courses(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),        # 小于 1 → 422
    limit: int = Query(10, ge=1, le=100, description="每页条数"),     # 超过 100 → 422
    db: Session = Depends(get_db),
):
    return list_courses(db, page, limit)

# 根据课程id读取具体课程路由接口
@router.get('/courses/{course_id}',response_model=CourseRead)
def read_course_by_id(course_id:int,db:Session=Depends(get_db)):
    return get_course(db,course_id)

# 根据课程id修改课程信息路由接口
@router.put('/courses/{course_id}', response_model=CourseRead)
def update_courses(course_id:int,update_courses:CourseCreate,db:Session=Depends(get_db)):
    return update_course(db,course_id,update_courses)

# 根据课程id删除课程路由接口
@router.delete('/courses/{course_id}', status_code=204)
def delete_courses(course_id:int,db:Session=Depends(get_db)):
    return delete_course(db,course_id)