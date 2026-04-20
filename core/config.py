import os
from dotenv import load_dotenv

# 1. 加载环境变量保险箱
load_dotenv()


class Settings:
    """
    全局配置类：将零散的环境变量封装成结构化的对象
    """

    PROJECT_NAME: str = "EriiNote Backend"

    # 获取 API Key，如果获取不到，编辑器会有类型提示提醒你
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY")


# 2. 实例化：创建一个供全项目使用的全局配置对象
settings = Settings()
