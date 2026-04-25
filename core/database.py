from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

# 1. 组装跨次元的连接字符串 (等同于前端 Prisma 的 DATABASE_URL)
# 格式: postgresql://用户名:密码@主机:端口/数据库名
# 这里咱们先硬编码写死，跑通后再教你怎么优雅地挪到 .env 里
import os

# 🚨 必须是这种包裹了 os.getenv 的动态写法
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://zer0ff:erii_secret@127.0.0.1:5432/erii_db"
)

# 2. 制造引擎 (Engine)
# 它是大楼的“发电机”，负责在底层维持与 Postgres 数据库的 TCP 物理连接池
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 3. 制造会话工厂 (SessionLocal)
# 它是每次请求到来时，用来产生一个独立“数据库会话”的模具。
# autocommit=False 保证了咱们可以手动控制事务(Transaction)，出错时能完美回滚
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 制造数据模型基类 (Base)
# 以后咱们定义的“聊天记录表”、“用户表”，都必须继承这个基类。
# SQLAlchemy 会扫描继承了它的类，自动帮咱们在数据库里把表建出来
Base = declarative_base()


# 5. 依赖注入发生器 (给路由层用的魔法水管)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
