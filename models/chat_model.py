from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from core.database import Base

# 🚨 继承自 database.py 里的 Base 模具
class MessageRecord(Base):
    # 告诉 SQLAlchemy，在真实的 Postgres 里这张表叫什么名字
    __tablename__ = "message_records"

    # 定义表的各个字段（列）
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 预留的会话 ID（未来如果你想给别人用，靠这个字段区分是哪个用户的聊天）
    session_id = Column(String(50), index=True, default="default_sakura") 
    
    role = Column(String(20))     # 记录是谁说的话：'user' 还是 'assistant'
    content = Column(Text)        # 聊天内容（用 Text 类型防止话太长塞不下）
    created_at = Column(DateTime, default=datetime.utcnow) # 自动记录发消息的时间