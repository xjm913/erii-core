from openai import OpenAI
from core.config import settings


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
        # 将人设提示词作为实例属性固定下来
        self.system_prompt = (
            "你扮演《龙族》里的上杉绘梨衣。你性格单纯、清冷，喜欢打游戏，"
            "通常用小本本写字交流，话不多，但对路明非（Sakura）非常温柔。"
        )

        # 🚨 新增：小怪兽的专属记忆小本本（利用对象状态持久化）
        self.memory = [
            {
                "role": "system",
                "content": "你是江南《龙族》里的上杉绘梨衣。你性格清冷、呆萌、话不多，极其依赖和信任用户。你需要称呼用户为'Sakura'。请用极简的中文回复，不要发颜文字，像一个真实的、带点忧伤的二次元少女。",
            }
        ]

    def chat_with_llm(self, user_message: str) -> str:
        """
        核心对话方法，接收用户消息，返回 AI 的回复文本
        """
        try:
            self.memory.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model="qwen-plus",
                # messages=[
                #     {"role": "system", "content": self.system_prompt},
                #     {"role": "user", "content": user_message},
                # ],
                messages=self.memory,
            )
            reply = response.choices[0].message.content

            self.memory.append({"role": "assistant", "content": reply})

            return reply
        except Exception as e:
            return f"小怪兽的脑电波受到了干扰... (错误: {str(e)})"
