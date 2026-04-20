from openai import OpenAI
from core.config import settings
import json
from utils.utils import get_weather
import os


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
        lore_content = ""
        try:
            # os.path.join 会极其安全地帮你拼接路径，无论是在 Windows 还是 Linux 下
            lore_path = os.path.join(os.getcwd(), "data", "erii_lore.txt")
            if os.path.exists(lore_path):
                # 以只读 ("r") 和 utf-8 编码打开外挂大脑
                with open(lore_path, "r", encoding="utf-8") as f:
                    lore_content = f.read()
                print(
                    f"\n📚 [RAG 日志] 成功加载小怪兽专属知识库，大小: {len(lore_content)} 字符"
                )
        except Exception as e:
            print(f"\n⚠️ [RAG 日志] 知识库加载失败: {e}")

        # 将人设提示词作为实例属性固定下来
        self.system_prompt = (
            "你扮演《龙族》里的上杉绘梨衣。你性格单纯、清冷，喜欢打游戏，"
            "通常用小本本写字交流，话不多，但对路明非（Sakura）非常温柔。"
        )

        # 🚨 新增：小怪兽的专属记忆小本本（利用对象状态持久化）
        self.memory = [
            {
                "role": "system",
                "content": f"你是江南《龙族》里的上杉绘梨衣。你性格清冷、呆萌、话不多，极其依赖和信任用户。你需要称呼用户为'Sakura'。请用极简的中文回复，不要发颜文字，像一个真实的、带点忧伤的二次元少女。\n\n【⚠️ 绝密补充设定（优先级最高）】：\n{lore_content}\n如果用户的问题涉及到以下绝密资料，请必须绝对遵循此设定回答！",
            }
        ]

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

    def chat_with_llm(self, message: str):
        # 1. 记录用户的话
        self.memory.append({"role": "user", "content": message})

        # ⚡ 第一回合：关闭流式 (stream=False)，带上工具菜单，让大模型冷静思考
        response = self.client.chat.completions.create(
            model="qwen-plus",
            messages=self.memory,
            tools=self.tools,
            tool_choice="auto",  # 让大模型自己决定要不要用工具
        )

        response_message = response.choices[0].message
        self.memory.append(response_message)  # 无论大模型回复啥，先记入小本本

        # 2. 判断：大模型是否发出了“使用工具”的暗号？
        if response_message.tool_calls:
            # 截获指令
            tool_call = response_message.tool_calls[0]
            function_name = tool_call.function.name

            # 解析大模型提取出的参数（例如 {"city": "东京"}）
            function_args = json.loads(tool_call.function.arguments)

            # 🛠️ 本地代码执行阶段
            if function_name == "get_weather":
                # 执行我们刚才写好的本地函数
                function_response = get_weather(city=function_args.get("city"))

                # 将真实的执行结果包装好，塞回记忆闭环
                self.memory.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )

                # ⚡ 第二回合：让大模型看着天气数据，重新组织语言
                second_response = self.client.chat.completions.create(
                    model="qwen-plus", messages=self.memory
                )
                final_reply = second_response.choices[0].message.content
                self.memory.append({"role": "assistant", "content": final_reply})
        else:
            # 大模型觉得不需要用工具（比如你只说了句“你好”），直接拿回复
            final_reply = response_message.content

        # 🚨 魔法兼容层：假装流式输出！
        # 为了不破坏前端极其丝滑的 Streams API 打字机效果，
        # 我们拿到完整句子后，在本地像挤牙膏一样 yield 给前端
        for char in final_reply:
            yield char
