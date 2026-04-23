from fastapi import APIRouter, File, UploadFile, Depends  # 🚨 新增 File, UploadFile
from schemas.chat_schema import ChatRequest
from services.llm_service import EriiAgentService
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session  # 🚨 新增 Session 类型
from core.database import get_db  # 🚨 新增获取数据库管子的生成器
from services.doc_service import process_and_store_document  # 🚨 引入加工厂流水线
from sqlalchemy import text  # 🚨 新增：用于执行极其暴力的原生 SQL
from core.database import engine  # 🚨 新增：引入数据库超级引擎

# 1. 实例化路由器
router = APIRouter()

# 2. 实例化小怪兽大脑 (单例模式的雏形)
erii_agent = EriiAgentService()


# 3. 定义具体的路由接口
@router.post("/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    负责处理 /chat 路径的 POST 请求
    继续流式返回前端，但是注入db
    """
    # 直接调用 Service 层的核心逻辑，Router 层不写任何具体的业务代码
    # reply = erii_agent.chat_with_llm(request.message)

    #  包装成 JSON 格式返回给前端
    # return {"reply": reply}

    return StreamingResponse(
        erii_agent.chat_with_llm(request.message, db), media_type="text/event-stream"
    )


# --- 🚨 新增：处理前端上传文档的接口 ---
# @router.post("/upload")
# async def upload_document(file: UploadFile = File(...)):
#     print(f"\n📎 [系统日志] 收到前端发来的文件，文件名: {file.filename}")
#     content = await file.read()

#     try:
#         text_content = content.decode("utf-8")

#         # 🚨 核心改造：把解码后的文本，直接喂给全局唯一的 erii_agent 大脑！
#         erii_agent.receive_document(text_content, file.filename)

#         return {
#             "status": "success",
#             "filename": file.filename,
#             "message": "文件已成功植入绘梨衣的临时记忆中！",
#         }
#     except Exception as e:
#         print(f"⚠️ 文件解码失败: {e}")
#         return {"status": "error", "message": "目前只支持读取 txt 纯文本哦"}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    print(f"\n📎 [系统日志] 收到前端发来的文件，准备进行向量化处理: {file.filename}")

    try:
        # 🚨 核心改造：直接把文件扔进咱们写好的流水线，等待它切片入库
        chunk_count = await process_and_store_document(file)

        return {
            "status": "success",
            "filename": file.filename,
            "message": f"文件已成功吃透！切分成了 {chunk_count} 个记忆碎片存入小怪兽的永久大脑。",
        }
    except Exception as e:
        print(f"⚠️ 文件处理失败: {e}")
        return {"status": "error", "message": f"文件向量化失败: {str(e)}"}


@router.delete("/clear-docs")
async def clear_documents():
    print("\n🧹 [系统日志] 收到前端指令，准备物理清空向量知识库...")
    try:
        # 🚨 极客级物理清空：直接利用底层引擎，无情清空 pgvector 的数据表
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE langchain_pg_embedding;"))

        print("✅ [系统日志] 向量知识库已彻底销毁！")
        return {"status": "success", "message": "小怪兽已经把看过的文档全忘光啦！"}
    except Exception as e:
        print(f"⚠️ 清空失败: {e}")
        return {"status": "error", "message": f"清空失败: {str(e)}"}
