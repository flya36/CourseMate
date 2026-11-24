from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.course import Course
from src.models.user import User
from src.schema.course import CourseCreate
from sqlalchemy.exc import IntegrityError

# ───────── 1. 创建 ─────────
def create_course(db:Session,data:CourseCreate,current_user: User)->Course:
    """新建课程：add → commit → refresh 三段式。"""
    if db.scalars(select(Course).where(Course.name == data.name)).first() is not None:
        raise HTTPException(status_code=409, detail=f"课程名「{data.name}」已存在")
    course = Course(
        name = data.name,
        description = data.description,
        owner_id=current_user.id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

# ───────── 判断课程是否属于当前用户 ─────────
def _ensure_owner(course: Course, current_user: User)->None:
    '''资源存在但归属不符时抛 403。'''
    if course.owner_id is None or course.owner_id != current_user.id:
        raise HTTPException(status_code=403,detail='无权访问该资源')

# ───────── 2. 查询 ─────────
def list_courses(db: Session, current_user: User,page: int = 1, limit: int = 10) -> list[Course]:
    """查询课程列表，分页返回（默认第 1 页、每页 10 条）。"""

    stmt = (
        select(Course)
        .where(Course.owner_id == current_user.id)
        .order_by(Course.id)                        # 必须先排序，否则分页顺序不稳定
        .offset((page - 1) * limit)                 # 跳过前面几页
        .limit(limit)                               # 只取这一页的条数
    )
    return list(db.scalars(stmt).all())

# ───────── 3. 查看课程是否存在（被 4、5 复用） ─────────
def get_course(db:Session,course_id:int,current_user:User)->Course:
    '''先判存在（404），再判归属（403）。'''
    course = db.get(Course,course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_owner(course, current_user)
    return course

# ───────── 4. 更新 ─────────
def update_course(db:Session,course_id:int,data:CourseCreate,current_user: User)->Course:
    """整体更新课程：先查 → 改字段 → 提交。"""
    course = get_course(db, course_id, current_user)
    if course.name != data.name and db.scalars(select(Course).where(Course.name == data.name)).first() is not None:
        raise HTTPException(status_code=409, detail=f"课程名「{data.name}」已存在")
    course.name = data.name
    course.description = data.description
    db.commit()
    db.refresh(course)
    return course

# ───────── 5. 删除 ─────────
def delete_course(db:Session,course_id:int,current_user: User)->None:
    """删除课程；如果该课程下还有文档，返回 409 """
    course = get_course(db, course_id, current_user)
    db.delete(course)
    try:
        db.commit()                              # 提交，数据库执行 DELETE → 触发外键 RESTRICT
    except IntegrityError:                       # 数据库报"父行被引用"（Error 1451）
        db.rollback()                            # 回滚，否则会话进入"待回滚"状态
        raise HTTPException(
            status_code=409,
            detail="该课程下还有文档，无法删除，请先删除文档",
        )