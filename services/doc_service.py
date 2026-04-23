from fastapi import UploadFile
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.vector_store import vector_store


async def process_and_store_document(file: UploadFile):
    # 1. 读取前端传来的二进制文件
    content = await file.read()
    # 真实开发中这里会用 LangChain 的各种 Loader 来解析 PDF/Word，咱们目前先极简处理 txt
    text_content = content.decode("utf-8")

    # 2. 启动“粉碎机” (Text Splitter)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # 每块最多 500 个字符
        chunk_overlap=50,  # 🚨 极客细节：上下块重叠 50 个字符，防止一句话被从中间无情劈断导致语义丢失！
        separators=["\n\n", "\n", "。", "！", "？", " ", ""],
    )

    # 3. 把长文本切成小碎块
    chunks = text_splitter.split_text(text_content)

    # 🚨 核心修复：防御性编程！强行剔除掉被切出来的“纯空白”和“只包含换行符”的碎块
    # 因为阿里云碰到纯空字符串也会当场暴毙报 400 错误
    chunks = [chunk for chunk in chunks if chunk.strip()]

    # 4. 把纯文本包装成 LangChain 认识的标准 Document 对象，并打上来源元数据 (Metadata)
    documents = [
        Document(page_content=chunk, metadata={"source": file.filename})
        for chunk in chunks
    ]

    # 5. 终极魔法：高维升维并入库
    # 这行代码会在底层自动调用阿里云的 Embedding 模型，把文字变成 1536 维的浮点数，然后存进咱们的 pgvector 数据库！
    print(
        f"📦 [向量库] 正在将《{file.filename}》切分为 {len(documents)} 个记忆碎片并写入数据库..."
    )
    vector_store.add_documents(documents)

    return len(documents)
