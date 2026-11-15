from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.course import Course
from src.models.document import Document
from src.schema.document import DocumentCreate

# ───────── 1. 创建 ─────────
def create_document(db: Session, data: DocumentCreate) -> Document:
    """新建文件"""
    course = db.get(Course,data.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    document = Document(course_id=data.course_id,
                        filename=data.filename,
                        file_type=data.file_type,
                        file_path=data.file_path,
                        file_size=data.file_size)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

# ───────── 2. 查询 ─────────
def list_documents(db:Session, page: int = 1, limit: int = 10)->list[Document]:
    """查询文档列表，分页返回（默认第 1 页、每页 10 条）。"""
    stmt = (
        select(Document)
        .order_by(Document.id)                      # 必须先排序，否则分页顺序不稳定
        .offset((page - 1) * limit)                 # 跳过前面几页
        .limit(limit)                               # 只取这一页的条数
    )
    return list(db.scalars(stmt).all())

# ───────── 3. 查看文件是否存在（被 4、5 复用） ─────────
def get_document(db:Session,document_id:int)->Document:
    """按主键查文件，查不到抛 404。"""
    document = db.get(Document,document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    return document

# ───────── 4. 更新 ─────────
def update_document(db:Session,document_id:int,data:DocumentCreate)->Document:
    """整体更新文件：先查 → 改字段 → 提交。"""
    document = get_document(db,document_id)
    if db.get(Course,data.course_id) is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    document.course_id=data.course_id
    document.filename=data.filename
    document.file_type=data.file_type
    document.file_path=data.file_path
    document.file_size=data.file_size
    db.commit()
    db.refresh(document)
    return document

# ───────── 5. 删除 ─────────
def delete_document(db:Session,document_id:int)->None:
    """删除文件：先查确认存在 → 删除 → 提交。"""
    document = get_document(db,document_id)
    db.delete(document)
    db.commit()

# ───────── 6. 根据课程id读取相关课程文件 ─────────
def get_documents_by_course_id(db:Session,course_id:int)->list[Document]:
    course = db.get(Course,course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    stmt = select(Document).where(Document.course_id==course_id).order_by(Document.id)
    return list(db.scalars(stmt).all())