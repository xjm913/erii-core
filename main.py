import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api import chat_router
# ... 原有 imports 保持不动 ...
from core.database import engine, Base
from models import chat_model # 🚨 极其关键：必须引入这个文件，SQLAlchemy 启动时才能扫描到里面的表结构

# 定义会话日志的文件名
LOG_FILE = "session_log.txt"

# 1. 组装 Python 的标准日志记录器
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger("EriiLogger")


# 2. 🚨 核心黑科技：生命周期钩子 (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):

# --- 🚨 新增：让 SQLAlchemy 自动去数据库里建表 ---
    print("⚙️ [系统日志] 正在同步数据库表结构...")
    Base.metadata.create_all(bind=engine)
    # -----------------------------------------------

    # 【服务启动时执行 (相当于前端的 componentDidMount)】
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("=== 🐉 小怪兽引擎：本次开发会话日志开始 ===\n")
    print(f"\n🚀 [日志系统] 会话存储已挂载，当前操作记录于: {LOG_FILE}")

    # 交出控制权，让应用正常运行接客
    yield

    # 【服务关闭时执行 (你在终端按 Ctrl+C 触发，相当于 componentWillUnmount)】
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)  # 无情物理删除！
        print(
            f"\n🗑️ [日志系统] 服务已关闭，会话日志 '{LOG_FILE}' 已自动销毁，不留痕迹！"
        )


# 3. 将 lifespan 注入到 FastAPI 实例中
app = FastAPI(title="EriiNote Backend Engine", lifespan=lifespan)

# 挂载跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 4. 挂载全局请求日志拦截器 (中间件)
@app.middleware("http")
async def session_logger(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000

    client_ip = request.client.host
    method = request.method
    url_path = request.url.path
    status_code = response.status_code

    # 组装日志内容
    log_msg = f"IP: {client_ip} | {method} {url_path} | 状态: {status_code} | 耗时: {process_time:.2f}ms"

    # 打印到终端让你看着爽
    print(f"🌍 [网络日志] {log_msg}")

    # 同时静默写入到当前的 txt 文件里（充当 session 存储）
    logger.info(log_msg)

    return response


# 挂载业务路由
app.include_router(chat_router.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
