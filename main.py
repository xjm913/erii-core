from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

# 1. 激活保险箱：读取 .env 文件到操作系统的环境变量中
load_dotenv()

# 2. 实例化框架：相当于 Node.js 里的 const app = express()
app = FastAPI()

# 3. 跨域配置：允许 Next.js 的 3000 端口来请求咱们
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. 初始化大模型客户端：百炼完美兼容 OpenAI 接口标准，所以直接用 openai 库
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


# 5. 定义数据验证模型：这非常像 TypeScript 里的 Interface
class ChatRequest(BaseModel):
    message: str


# 6. 定义路由接口：这叫“装饰器”，相当于 Express 里的 app.post('/api/chat', ...)
@app.post("/api/chat")
async def chat_with_erii(request: ChatRequest):
    try:
        # 调用大模型 (注意这里是标准的 ChatGPT 对话格式：system 设定性格，user 是用户输入)
        response = client.chat.completions.create(
            model="qwen-plus",  # 使用通义千问 Plus 模型
            messages=[
                {
                    "role": "system",
                    "content": "你扮演《龙族》里的上杉绘梨衣。你性格单纯、清冷，喜欢打游戏，通常用小本本写字交流，话不多，但对路明非（你称呼他为Sakura）非常温柔。请保持这个设定回答问题。",
                },
                {"role": "user", "content": request.message},
            ],
        )
        # 将大模型吐出来的文字，包装成 JSON 格式返回给前端
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        # 异常捕获，相当于 try...catch
        return {"reply": f"小怪兽的脑电波受到了干扰... (错误: {str(e)})"}
