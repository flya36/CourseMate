from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from src.app.deps import get_current_user
from src.db import get_db
from src.models.user import User
from src.schema.document import DocumentCreate, DocumentRead,DocumentUpdate
from src.service.course import get_course
from src.service.document import (create_document, delete_document, get_document,
                                  get_documents_by_course_id, list_documents, update_document)
from src.service.upload import MAX_SIZE, safe_filename, save_upload, validate_upload

router = APIRouter()


# 创建新文件路由接口
@router.post('/documents', response_model=DocumentRead, status_code=201)
def create_documents(document_create: DocumentCreate,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    return create_document(db, document_create, current_user)


# 上传文件（真正的文件落盘入口）
@router.post('/documents/upload', response_model=DocumentRead, status_code=201)
async def upload_document(course_id: int = Form(..., gt=0),
                          file: UploadFile = File(...),
                          db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    # ① 先判课程存在 + 归属（404/403），放在落盘之前，失败时磁盘上啥也不留
    get_course(db, course_id, current_user)

    # ② 只读到上限 +1：超限立刻停，不会把 2GB 全拉进内存
    data = await file.read(MAX_SIZE + 1)
    if len(data) > MAX_SIZE:
        raise HTTPException(413, f"文件超过 {MAX_SIZE // 1024 // 1024}MB 上限")

    # ③ 校验（内部再兜一次体积）+ 落盘
    filename = safe_filename(file.filename)
    ext = validate_upload(filename, data)
    rel_path = save_upload(data, ext)

    # ④ 写库；失败就把盘上刚写的文件删掉，别留孤儿
    try:
        return create_document(db, DocumentCreate(
            course_id=course_id,
            filename=filename,
            file_type=ext.lstrip("."),
            file_path=rel_path,
            file_size=len(data),
        ), current_user)
    except Exception:
        Path(rel_path).unlink(missing_ok=True)
        raise


# 读取文件路由接口
@router.get('/documents', response_model=list[DocumentRead])
def read_documents(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    limit: int = Query(10, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_documents(db, current_user, page, limit)


# 根据文件id读取文件路由接口
@router.get('/documents/{document_id}', response_model=DocumentRead)
def read_document_by_id(document_id: int,
                        db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    return get_document(db, document_id, current_user)


# 根据课程id读取课程文件路由接口
@router.get('/courses/{course_id}/documents', response_model=list[DocumentRead])
def list_documents_by_course_id(course_id: int,
                                db: Session = Depends(get_db),
                                current_user: User = Depends(get_current_user)):
    return get_documents_by_course_id(db, course_id, current_user)


# 根据文件id修改文件元信息路由接口
@router.put('/documents/{document_id}', response_model=DocumentRead)
def update_documents(document_id: int,
                     update_document_data: DocumentUpdate,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    return update_document(db, document_id, update_document_data, current_user)


# 根据文件id删除文件路由接口
@router.delete('/documents/{document_id}', status_code=204)
def delete_document_by_id(document_id: int,
                          db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    return delete_document(db, document_id, current_user)
