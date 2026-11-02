import uvicorn
from fastapi import FastAPI

from src.router import health, course

app = FastAPI()
# 注册路由：把各 router 模块挂载到主应用
app.include_router(health.router)
app.include_router(course.router)

from src.app.exception_handlers import register_exception_handlers
register_exception_handlers(app)

# if __name__ == '__main__':
#     uvicorn.run(app , host='127.0.0.1', port=8000)

# 启动方式
# uv run python -m uvicorn src.app.main:app --reload