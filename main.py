from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import chat_router
import uvicorn  # 👈 新增引入

# 1. 实例化全局应用
app = FastAPI(title="EriiNote Backend Engine")

# 2. 挂载跨域中间件 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许前端 Next.js 的 3000 端口来访问
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 将路由模块挂载到主程序，统一加上 /api 前缀
app.include_router(chat_router.router, prefix="/api")

# 👈 新增启动入口
if __name__ == "__main__":
    # 这样你就可以直接在编辑器里右键运行这个文件了
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
