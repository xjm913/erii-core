from openai import OpenAI
from core.config import settings
import json
from utils.utils import get_weather, search_knowledge_base
import os
from sqlalchemy.orm import Session  # 🚨 新增
from models.chat_model import MessageRecord  # 🚨 引入咱们刚建的表模型
import requests  # 🚨 新增：用来向真实的 Open-Meteo 发起 HTTP 请求
from core.vector_store import vector_store  # 🚨 新增：引入咱们的向量雷达


class EriiAgentService:
    """
    绘梨衣的 AI 大脑：封装所有的对话状态与大模型调用逻辑
    """

    def __init__(self):
        # 构造函数：在类被实例化时第一步执行的地方
        # 初始化大模型客户端，并将其挂载到实例的 self 上
        self.client = OpenAI(
            api_key=settings.DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        # --- 🚨 新增：RAG 检索阶段 (Retrieval) ---
        # lore_content = ""
        # try:
        #     # os.path.join 会极其安全地帮你拼接路径，无论是在 Windows 还是 Linux 下
        #     lore_path = os.path.join(os.getcwd(), "data", "erii_lore.txt")
        #     if os.path.exists(lore_path):
        #         # 以只读 ("r") 和 utf-8 编码打开外挂大脑
        #         with open(lore_path, "r", encoding="utf-8") as f:
        #             lore_content = f.read()
        #         print(
        #             f"\n📚 [RAG 日志] 成功加载小怪兽专属知识库，大小: {len(lore_content)} 字符"
        #         )
        # except Exception as e:
        #     print(f"\n⚠️ [RAG 日志] 知识库加载失败: {e}")

        # 将人设提示词作为实例属性固定下来
        self.system_prompt = {
            "role": "system",
            "content": (
                "你扮演《龙族》里的上杉绘梨衣。你性格单纯、清冷，喜欢打游戏，"
                "通常用小本本写字交流，说话比较简短，但对路明非（Sakura）非常温柔。"
            ),
        }

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "当用户询问天气时，必须调用此函数获取真实数据。不要自己瞎猜天气。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "城市名称，例如：北京，东京",
                            }
                        },
                        "required": ["city"],
                    },
                },
            },
            # 👇 新增：本地知识库检索工具
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "当用户询问关于刚刚上传的文档、绘梨衣的特定设定、或者需要查阅本地知识库中的内容时，必须调用此工具获取背景资料。如果是普通的日常问候闲聊，请绝对不要调用此工具。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "需要去知识库中精确检索的核心问题或关键词",
                            }
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

        # 🚨 新增：用于存放动态上传文档的临时口袋
        self.current_document = ""
        self.current_filename = ""

    # def chat_with_llm(self, user_message: str) -> str:
    #     """
    #     # . 🚨 新增：加入 stream=True 参数，开启水龙头
    #     """
    #     try:
    #         self.memory.append({"role": "user", "content": user_message})

    #         response = self.client.chat.completions.create(
    #             model="qwen-plus",
    #             # messages=[
    #             #     {"role": "system", "content": self.system_prompt},
    #             #     {"role": "user", "content": user_message},
    #             # ],
    #             messages=self.memory,
    #             stream=True,
    #         )
    #         full_reply = ""
    #         # reply = response.choices[0].message.content

    #         for chunk in response:
    #             if chunk.choices[0].delta.content is not None:
    #                 char = chunk.choices[0].delta.content
    #                 full_reply += char
    #                 yield char

    #         self.memory.append({"role": "assistant", "content": full_reply})

    #         # return reply
    #     except Exception as e:
    #         return f"小怪兽的脑电波受到了干扰... (错误: {str(e)})"

    # 🚨 新增：接收临时文档的方法
    def receive_document(self, text: str, filename: str):
        self.current_document = text
        self.current_filename = filename
        print(f"🧠 [大脑日志] 成功装载临时记忆：{filename}，长度 {len(text)} 字符")

    def chat_with_llm(self, message: str, db: Session):
        # --- 🟢 第一步：真身落盘（只存用户的极简原话） ---
        user_record = MessageRecord(role="user", content=message)
        db.add(user_record)
        db.commit()

        # --- 🟢 第二步：提取历史记忆 ---
        history_records = db.query(MessageRecord).order_by(MessageRecord.id.asc()).all()
        messages_for_llm = [self.system_prompt]
        for record in history_records:
            messages_for_llm.append({"role": record.role, "content": record.content})

        # 🚨 极其关键：彻底删除了这里原本的 vector_store.similarity_search 无脑检索代码！

        # --- 🟢 第三步：第一次握手（非流式探测意图） ---
        response = self.client.chat.completions.create(
            model="qwen-plus",
            messages=messages_for_llm,
            tools=self.tools,  # 把带有天气和知识库的完整菜单递给大模型
        )
        response_message = response.choices[0].message

        # --- 🟢 第四步：拦截智能体的工具路由 ---
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            tool_result = ""  # 准备存放工具执行的结果

            # 路由分支 A：查天气
            if function_name == "get_weather":
                tool_result = get_weather(args.get("city"))

            # 路由分支 B：查阅本地向量数据库
            elif function_name == "search_knowledge_base":
                tool_result = search_knowledge_base(args.get("query"))

            # 🚨 终极修复：使用咱们之前防 400 报错的神级序列化方法
            assistant_msg = response_message.model_dump(exclude_none=True)
            messages_for_llm.append(assistant_msg)

            # 把工具真实的执行结果塞回去
            messages_for_llm.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": tool_result,
                }
            )

            # 带着真实数据，开启第二次真实呲水
            final_response = self.client.chat.completions.create(
                model="qwen-plus", messages=messages_for_llm, stream=True
            )
        else:
            # 如果大模型觉得只是在闲聊，直接把回复伪装成字流吐出去
            final_response = [
                {"choices": [{"delta": {"content": char}}]}
                for char in response_message.content
            ]

        # --- 🟢 第五步：一边呲水，一边用“暗桶”接水落盘 ---
        full_reply = ""
        for chunk in final_response:
            delta = (
                chunk.choices[0].delta
                if hasattr(chunk, "choices")
                else chunk["choices"][0]["delta"]
            )
            content = (
                delta.content if hasattr(delta, "content") else delta.get("content")
            )
            if content:
                full_reply += content
                yield content

        if full_reply:
            ai_record = MessageRecord(role="assistant", content=full_reply)
            db.add(ai_record)
            db.commit()
