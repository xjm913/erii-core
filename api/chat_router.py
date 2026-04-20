from fastapi import APIRouter
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
