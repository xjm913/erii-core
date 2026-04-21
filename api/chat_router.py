from fastapi import APIRouter, File, UploadFile  # 🚨 新增 File, UploadFile
from schemas.chat_schema import ChatRequest
from services.llm_service import EriiAgentService
from fastapi.responses import StreamingResponse

# 1. 实例化路由器
router = APIRouter()

# 2. 实例化小怪兽大脑 (单例模式的雏形)
erii_agent = EriiAgentService()


# 3. 定义具体的路由接口
@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    负责处理 /chat 路径的 POST 请求
    """
    # 直接调用 Service 层的核心逻辑，Router 层不写任何具体的业务代码
    # reply = erii_agent.chat_with_llm(request.message)

    #  包装成 JSON 格式返回给前端
    # return {"reply": reply}

    return StreamingResponse(
        erii_agent.chat_with_llm(request.message), media_type="text/event-stream"
    )


# --- 🚨 新增：处理前端上传文档的接口 ---
@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    print(f"\n📎 [系统日志] 收到前端发来的文件，文件名: {file.filename}")
    content = await file.read()

    try:
        text_content = content.decode("utf-8")

        # 🚨 核心改造：把解码后的文本，直接喂给全局唯一的 erii_agent 大脑！
        erii_agent.receive_document(text_content, file.filename)

        return {
            "status": "success",
            "filename": file.filename,
            "message": "文件已成功植入绘梨衣的临时记忆中！",
        }
    except Exception as e:
        print(f"⚠️ 文件解码失败: {e}")
        return {"status": "error", "message": "目前只支持读取 txt 纯文本哦"}
