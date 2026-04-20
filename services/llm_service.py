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

    def chat_with_llm(self, user_message: str) -> str:
        """
        核心对话方法，接收用户消息，返回 AI 的回复文本
        """
        try:
            response = self.client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"小怪兽的脑电波受到了干扰... (错误: {str(e)})"
