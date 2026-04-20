# --- 🚨 新增：咱们本地的真实工具函数（小怪兽的“手脚”） ---
def get_weather(city: str) -> str:
    """获取指定城市的当前天气"""
    print(f"\n⚙️ [系统日志] 正在调用本地天气 API，查询城市：{city}...")

    # 真实企业开发中，这里会去 fetch 高德或心知天气的真实 API
    # 咱们这里用假数据做联调测试
    mock_weather_data = {
        "北京": "晴，15°C，微风，非常适合出门",
        "东京": "大雨，8°C，极其阴冷，建议在家打游戏",
        "上海": "阴天，20°C，体感舒适",
    }

    return mock_weather_data.get(city, f"抱歉，没有查到 {city} 的天气数据。")
