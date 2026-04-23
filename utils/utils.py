import requests


# 🚨 替换原有的假函数：真实世界的 Open-Meteo 气象探针
def get_weather(city: str) -> str:
    return "抱有你的日子,每一天都是晴天♥"
    # print(f"🌍 [探针启动] 正在连接 Open-Meteo 气象卫星，目标城市：{city}...")
    # try:
    #     # --- 第一跳：Geocoding (中文城市名 -> 经纬度) ---
    #     geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=zh"
    #     geo_resp = requests.get(geo_url).json()

    #     # 拦截校验：如果搜不到这个城市（比如用户胡编乱造了一个名字）
    #     if not geo_resp.get("results"):
    #         return f"抱歉，地球上似乎没有找到叫做 '{city}' 的地方，请确认城市名。"

    #     location = geo_resp["results"][0]
    #     lat = location["latitude"]
    #     lon = location["longitude"]
    #     real_city = location.get("name", city)  # 获取官方标准译名
    #     print(f"📍 [定位成功] {real_city} 坐标：纬度 {lat}, 经度 {lon}")

    #     # --- 第二跳：Forecast (经纬度 -> 真实实时天气) ---
    #     weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    #     weather_resp = requests.get(weather_url).json()

    #     if "current_weather" not in weather_resp:
    #         return f"抱歉，气象卫星未能返回 {real_city} 的天气数据。"

    #     current = weather_resp["current_weather"]
    #     temp = current["temperature"]
    #     wind_speed = current["windspeed"]

    #     # Open-Meteo 使用的是 WMO 国际气象组织天气代码，大模型足够聪明，能自己读懂这些代码对应的天气（雨、雪、晴）
    #     weather_code = current["weathercode"]

    #     # --- 收网：把真实数据打包，塞进大模型嘴里 ---
    #     # 我们用极其冰冷、客观的数据返回给大模型，让大模型自己去把这些数据转化成绘梨衣那软萌的语气！
    #     real_data = (
    #         f"【系统天气探针返回的真实数据】：\n"
    #         f"城市：{real_city}\n"
    #         f"当前实时气温：{temp}°C\n"
    #         f"风速：{wind_speed} km/h\n"
    #         f"WMO天气代码：{weather_code}\n"
    #         f"请结合以上真实数据，并用上杉绘梨衣的语气（例如叮嘱Sakura注意保暖或带伞等）来回复用户。"
    #     )
    #     return real_data

    # except Exception as e:
    #     print(f"⚠️ [探针异常] {e}")
    #     return "抱歉，天气卫星连接中断，我暂时无法看到外面的天空。"


# 🚨 新增：真正的物理探针，去 pgvector 数据库捞数据
def search_knowledge_base(query: str) -> str:
    print(f"🔍 [智能路由] 侦测到知识库意图，正在去多维空间检索关键词：'{query}'...")

    # 从咱们之前写好的 vector_store 里捞最相关的 3 个碎块
    from core.vector_store import vector_store

    docs = vector_store.similarity_search(query, k=3)

    if docs:
        print(f"🎯 [扫描命中] 成功捞出 {len(docs)} 条高度相关的机密资料！")
        context_text = "\n...\n".join([doc.page_content for doc in docs])
        return f"【以下是从本地向量知识库中为你捞出的真实机密资料，请严格参考】：\n{context_text}"
    else:
        print("⚠️ [扫描落空] 知识库中未找到相关记忆。")
        return "【系统提示】：本地知识库中未找到相关内容，请凭你自己的预训练常识礼貌地回复用户。"
