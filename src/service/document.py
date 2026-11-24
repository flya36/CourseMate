from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.course import Course
from src.models.document import Document
from src.models.user import User
from src.schema.document import DocumentCreate
from src.service.course import _ensure_owner

# ───────── 1. 创建 ─────────
def create_document(db: Session, data: DocumentCreate, current_user: User) -> Document:
    """新建文件；课程必须属于当前用户（否则 403），归属写进 owner_id。"""
    course = db.get(Course, data.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_owner(course, current_user)          # 不能往别人的课程里塞文件

    document = Document(course_id=data.course_id,
                        filename=data.filename,
                        file_type=data.file_type,
                        file_path=data.file_path,
                        file_size=data.file_size,
                        owner_id=current_user.id)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

# ───────── 2. 查询 ─────────
def list_documents(db: Session, current_user: User, page: int = 1, limit: int = 10) -> list[Document]:
    """查询文档列表，只返回当前用户自己的文档，分页返回。"""
    stmt = (
        select(Document)
        .where(Document.owner_id == current_user.id)   # 不过滤就是把别人的文档直接列出来
        .order_by(Document.id)                      # 必须先排序，否则分页顺序不稳定
        .offset((page - 1) * limit)                 # 跳过前面几页
        .limit(limit)                               # 只取这一页的条数
    )
    return list(db.scalars(stmt).all())

# ───────── 3. 查看文件是否存在 + 归属 ─────────
def get_document(db: Session, document_id: int, current_user: User) -> Document:
    """先判存在（404），再判归属（403）。"""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    _ensure_owner(document, current_user)
    return document

# ───────── 4. 更新 ─────────
def update_document(db: Session, document_id: int, data: DocumentCreate, current_user: User) -> Document:
    """整体更新文件：先查 + 校验归属 → 改字段 → 提交。"""
    document = get_document(db, document_id, current_user)

    course = db.get(Course, data.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_owner(course, current_user)          # 改挂到别人的课程下同样要拦

    document.course_id = data.course_id
    document.filename = data.filename
    document.file_type = data.file_type
    document.file_path = data.file_path
    document.file_size = data.file_size
    db.commit()
    db.refresh(document)
    return document

# ───────── 5. 删除 ─────────
def delete_document(db: Session, document_id: int, current_user: User) -> None:
    """删除文件：先查 + 校验归属 → 删除 → 提交。"""
    document = get_document(db, document_id, current_user)
    db.delete(document)
    db.commit()

# ───────── 6. 根据课程id读取相关课程文件 ─────────
def get_documents_by_course_id(db: Session, course_id: int, current_user: User) -> list[Document]:
    """按课程过滤；课程归属不符时 403，而不是返回别人的文件列表。"""
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_owner(course, current_user)

    stmt = select(Document).where(Document.course_id == course_id).order_by(Document.id)
    return list(db.scalars(stmt).all())
