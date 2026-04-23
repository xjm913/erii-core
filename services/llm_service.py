from openai import OpenAI
from core.config import settings
import json
from utils.utils import get_weather
import os
from sqlalchemy.orm import Session  # 🚨 新增
from models.chat_model import MessageRecord  # 🚨 引入咱们刚建的表模型
import requests  # 🚨 新增：用来向真实的 Open-Meteo 发起 HTTP 请求


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
        self.system_prompt = (
            "你扮演《龙族》里的上杉绘梨衣。你性格单纯、清冷，喜欢打游戏，"
            "通常用小本本写字交流，话不多，但对路明非（Sakura）非常温柔。"
        )

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
            }
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

        # --- 🟢 第一步：真身落盘（只把 Sakura 的【原话】存进硬盘！） ---
        user_record = MessageRecord(role="user", content=message)
        db.add(user_record)
        db.commit()

        # --- 🟢 第二步：从硬盘提取历史记忆 ---
        history_records = db.query(MessageRecord).order_by(MessageRecord.id.asc()).all()
        messages_for_llm = [{"role": "system", "content": self.system_prompt}]
        for record in history_records:
            messages_for_llm.append({"role": record.role, "content": record.content})

        # --- 🟢 第三步：幻影骗脑（RAG 动态拼凑，绝不落盘！） ---
        if self.current_document:
            augmented_message = (
                f"【系统提示：以下是用户刚刚上传的文档《{self.current_filename}》的全部内容：】\n"
                f"...\n{self.current_document}\n...\n"
                f"【请结合上述文档内容，回答用户的以下问题】：\n{message}"
            )
            # 强行把发给大模型的最后一条消息（也就是刚查出来的用户原话）替换成加强版
            messages_for_llm[-1]["content"] = augmented_message

            # 阅后即焚，防止污染下一个毫不相干的问题
            self.current_document = ""
            self.current_filename = ""

        # --- 🟢 第四步：呼叫大模型（第一次握手：非流式探测工具） ---
        # 🚨 因为在流式状态下处理 JSON 碎片极其痛苦，咱们采用魔法降维：先探测是否需要用工具
        response = self.client.chat.completions.create(
            model="qwen-plus", messages=messages_for_llm, tools=self.tools  # 挂上手脚！
        )
        response_message = response.choices[0].message

        # --- 🟢 第五步：拦截工具调用 (Function Calling) ---
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            if tool_call.function.name == "get_weather":
                args = json.loads(tool_call.function.arguments)
                city = args.get("city")
                print(f"⚙️ [系统日志] 正在调用本地天气 API，查询城市：{city}...")

                weather_result = get_weather(city)  # 调用本地函数

                # 把工具结果塞进上下文
                messages_for_llm.append(response_message)
                messages_for_llm.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": weather_result,
                    }
                )

                # 第二次呼叫大模型，带着天气数据开启流式
                final_response = self.client.chat.completions.create(
                    model="qwen-plus", messages=messages_for_llm, stream=True
                )
        else:
            # 如果没调用工具，为了兼容前端的打字机特效，咱们把拿到的完整回复伪装成字流吐出去
            final_response = [
                {"choices": [{"delta": {"content": char}}]}
                for char in response_message.content
            ]

        # --- 🟢 第六步：一边呲水，一边用“暗桶”接水 ---
        full_reply = ""
        for chunk in final_response:
            # 兼容原生 stream 和咱们伪装的 stream
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

        # --- 🟢 第七步：呲水结束，把小怪兽的回复存进硬盘 ---
        if full_reply:
            ai_record = MessageRecord(role="assistant", content=full_reply)
            db.add(ai_record)
            db.commit()
