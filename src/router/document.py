from src.schema.document import DocumentCreate,DocumentRead
from src.service.document import create_document,get_document,update_document,list_documents,delete_document,get_documents_by_course_id
from fastapi import APIRouter,Depends, Query
from sqlalchemy.orm import Session
from src.db import get_db
from src.app.deps import get_current_user
from src.models.user import User

router = APIRouter()



# 创建新文件路由接口
@router.post('/documents',response_model=DocumentRead,status_code=201)
def create_documents(document_create:DocumentCreate,db:Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    return create_document(db,document_create,current_user)

# 读取文件路由接口
@router.get('/documents',response_model=list[DocumentRead])
def read_documents(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),        # 小于 1 → 422
    limit: int = Query(10, ge=1, le=100, description="每页条数"),     # 超过 100 → 422
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_documents(db, current_user, page, limit)

# 根据文件id读取文件路由接口
@router.get('/documents/{document_id}',response_model=DocumentRead)
def read_document_by_id(document_id:int,db:Session=Depends(get_db),current_user: User = Depends(get_current_user)):
    return get_document(db,document_id,current_user)

# 根据课程id读取课程文件路由接口
@router.get('/courses/{course_id}/documents',response_model=list[DocumentRead])
def list_documents_by_course_id(course_id:int,db:Session=Depends(get_db),current_user: User = Depends(get_current_user)):
    return get_documents_by_course_id(db,course_id,current_user)

# 根据文件id修改课程信息路由接口
@router.put('/documents/{document_id}', response_model=DocumentRead)
def update_documents(document_id:int,update_document_data:DocumentCreate,db:Session=Depends(get_db),current_user: User = Depends(get_current_user)):
    return update_document(db,document_id,update_document_data,current_user)

# 根据课程id删除课程路由接口
@router.delete('/documents/{document_id}', status_code=204)
def delete_document_by_id(document_id:int,db:Session=Depends(get_db),current_user: User = Depends(get_current_user)):
    return delete_document(db,document_id,current_user)
