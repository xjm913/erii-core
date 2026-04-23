from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from core.config import settings

# 1. 配置“升维翻译官” (Embedding 模型)
# 既然咱们用的是阿里云百炼的兼容模式，这里直接调用百炼自带的 text-embedding 引擎
embeddings = OpenAIEmbeddings(
    api_key=settings.DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="text-embedding-v3",  # 阿里云兼容的通用向量模型
    chunk_size=10,  # 🚨 核心修复：强行限制每次只发 10 个碎块给阿里云，防止撑爆它的“喉咙
    check_embedding_ctx_length=False,  # 🚨 终极修复：严禁 LangChain 自作聪明把中文字符转成数字 Token！强行发送纯文本原浆！
)

# 2. 组装向量数据库的连接字符串
# 注意：LangChain 的 PGVector 需要使用 psycopg3 (psycopg) 协议，
# 我们在 database.py 用的是 psycopg2，所以这里的连接头是 postgresql+psycopg://
VECTOR_DB_URL = "postgresql+psycopg://zer0ff:erii_secret@127.0.0.1:5432/erii_db"

# 3. 实例化向量集合 (Collection)
# 这就好比在 erii_db 数据库里，专门划出一块叫 "erii_knowledge" 的区域来存咱们的碎块
vector_store = PGVector(
    embeddings=embeddings,
    collection_name="erii_knowledge",
    connection=VECTOR_DB_URL,
    use_jsonb=True,  # 开启 Postgres 的高级 JSON 存储特性，速度更快
)
