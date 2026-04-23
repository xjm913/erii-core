#!/bin/bash

echo "🐉 [系统自检] 正在唤醒小怪兽的记忆中枢..."

# 检查 erii-postgres 容器是否已经在运行
if [ "$(docker ps -q -f name=erii-postgres)" ]; then
    echo "✅ 数据库正常心跳中，5432 端口已就绪！"
else
    echo "⚙️ 检测到数据库处于沉睡状态，正在发送点火指令..."
    # 唤醒咱们昨天建好的那个名为 erii-postgres 的容器
    docker start erii-postgres
    echo "🚀 数据库点火成功！"
fi