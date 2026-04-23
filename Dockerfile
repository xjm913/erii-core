# 1. 使用轻量级 Python 环境
FROM python:3.10-slim

# 2. 安装编译 psycopg2 所需的系统底层依赖
RUN apt-get update && apt-get install -y \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# 3. 设置工作目录
WORKDIR /app

# 4. 复制依赖清单并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 复制所有代码
COPY . .

# 6. 暴露 8000 端口
EXPOSE 8000

# 7. 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]