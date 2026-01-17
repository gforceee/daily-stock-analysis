import os
import akshare as ak
import google.generativeai as genai
import pandas as pd

# 1. 从环境变量获取 Key
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("Error: 未找到 GEMINI_API_KEY，请检查 GitHub Secrets 配置！")
    exit(1)

# 2. 配置 Gemini
genai.configure(api_key=api_key)

def get_best_model():
    """
    自动寻找当前账号可用的最佳模型
    优先级: Gemini 1.5 Flash -> Gemini 1.5 Pro -> Gemini Pro -> 任意可用模型
    """
    print(">>> [0/3] 正在自动检索可用模型列表...")
    available_models = []
    try:
        for m in genai.list_models():
            # 必须支持 generateContent 方法的模型才能用来生成文本
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
    except Exception as e:
        print(f"!!! 获取模型列表失败: {e}")
        return None

    if not available_models:
        print("!!! 未找到任何可用模型，请检查 API Key 权限")
        return None

    # 打印一下找到了哪些，方便调试
    # print(f"可用模型: {available_models}")

    # 优先级匹配逻辑
    # 1. 优先找 1.5 Flash (最快，最稳)
    for m in available_models:
        if 'gemini-1.5-flash' in m:
            return m
    
    # 2. 其次找 1.5 Pro
    for m in available_models:
        if 'gemini-1.5-pro' in m:
            return m
            
    # 3. 再其次找老版 Pro
    for m in available_models:
        if 'gemini-pro' in m:
            return m

    # 4. 实在不行，返回列表里的第一个
    return available_models[0]

# 获取并初始化模型
model_name = get_best_model()
if model_name:
    print(f">>> 成功选中模型: {model_name}")
    model = genai.GenerativeModel(model_name)
else:
    print("!!! 无法初始化模型，程序退出")
    exit(1)

def get_market_sentiment():
    print(">>> [1/3] 正在抓取上证指数(000001)最新资讯...")
    
    news_text = ""
    try:
        # 东方财富-个股新闻接口
        df = ak.stock_news_em(symbol="000001")
        
        # 只取最新的 5 条
        latest_news = df.head(5)
        
        # 拼接新闻标题和内容
        news_list = []
        for index, row in latest_news.iterrows():
            title = row.get('新闻标题', '无标题')
            content = row.get('新闻内容', '无内容')
            news_item = f"标题：{title}\n内容：{str(content)[:100]}..." 
            news_list.append(news_item)
            
        news_text = "\n---\n".join(news_list)
        print(">>> 抓取成功！准备发送给 AI...")
        
    except Exception as e:
        print(f"抓取失败: {e}")
        return

    # 3. 构造 Prompt
    prompt = f"""
    你是 A股资深交易员。请根据以下关于“上证指数”的最新 5 条新闻，生成一份简报。
    
    新闻内容：
    {news_text}
    
    请输出以下格式（纯文本即可，不要Markdown）：
    【整体情绪】：（恐慌/中性/贪婪）
    【核心板块】：（列出1-2个利好方向）
    【犀利点评】：（用一句简短的话总结对明天开盘的影响）
    """

    # 4. 调用 Gemini
    print(">>> [2/3] AI 正在分析中...")
    try:
        response = model.generate_content(prompt)
        print("\n" + "="*30)
        print(">>> [3/3] 分析报告如下：")
        print("="*30)
        print(response.text)
        print("="*30)
    except Exception as e:
        print(f"AI 调用失败: {e}")

if __name__ == "__main__":
    get_market_sentiment()
