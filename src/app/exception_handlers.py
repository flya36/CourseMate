import logging
from fastapi import FastAPI,Request,HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger('coursemate')

def register_exception_handlers(app:FastAPI) -> None:
    # ① 业务错误：显式统一 {detail} 格式
    @app.exception_handler(HTTPException)
    def http_exc(request:Request,exc:HTTPException):
        return JSONResponse(status_code=exc.status_code,content={'detail':exc.detail})
    
    # ② 校验失败：422 三件套（loc/msg/type)
    @app.exception_handler(RequestValidationError)
    def validation_exc(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    # ③ 兜底 500：记 traceback（服务端留痕）+ 通用信息（不给堆栈）
    @app.exception_handler(Exception)
    async def unhandled_exc(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})