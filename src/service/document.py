from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.course import Course
from src.models.document import Document
from src.models.user import User
from src.schema.document import DocumentCreate,DocumentUpdate
from src.service.course import _ensure_owner
from src.service.upload import resolve_path

# ───────── 1. 创建 ─────────
def create_document(db: Session, data: DocumentCreate, current_user: User) -> Document:
    """新建文件；课程必须属于当前用户（否则 403），归属写进 owner_id。"""
    course = db.get(Course, data.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_owner(course, current_user)          # 不能往别人的课程里塞文件

    rel = Path(data.file_path)
    if rel.is_absolute() or not rel.parts or rel.parts[0] != "uploads" or ".." in rel.parts:
        raise HTTPException(400, "非法文件路径")   # 绝对路径 / 不在 uploads 下 / 用 .. 逃逸

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
def update_document(db: Session, document_id: int, data: DocumentUpdate, current_user: User) -> Document:
    """只改展示用元信息：file_path / file_size / file_type 由服务端掌握，不接受客户端传入。"""
    document = get_document(db, document_id, current_user)

    document.filename = data.filename
    db.commit()
    db.refresh(document)
    return document

# ───────── 5. 删除 ─────────
def delete_document(db: Session, document_id: int, current_user: User) -> None:
    """删除文件：先查 + 校验归属 → 删除 → 提交。"""
    document = get_document(db, document_id, current_user)
    file_path = document.file_path
    db.delete(document)
    db.commit()
    resolve_path(file_path).unlink(missing_ok=True)

# ───────── 6. 根据课程id读取相关课程文件 ─────────
def get_documents_by_course_id(db: Session, course_id: int, current_user: User) -> list[Document]:
    """按课程过滤；课程归属不符时 403，而不是返回别人的文件列表。"""
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    _ensure_owner(course, current_user)

    stmt = select(Document).where(Document.course_id == course_id).order_by(Document.id)
    return list(db.scalars(stmt).all())
