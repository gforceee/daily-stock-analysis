import os
import akshare as ak
import google.generativeai as genai
import sys

# 1. 基础配置
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: 未找到 GEMINI_API_KEY")
    exit(1)

genai.configure(api_key=api_key)

# 2. 模型选择逻辑 (保留之前成功的版本)
def get_flash_model():
    print(">>> [0/3] 正在搜索可用的 Flash 模型...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name.lower():
                    print(f">>> 找到目标: {m.name}")
                    return m.name
        # 降级方案
        print(">>> 警告: 没找到 Flash，尝试 Pro...")
        for m in genai.list_models():
             if 'generateContent' in m.supported_generation_methods:
                 if 'pro' in m.name.lower() and '2.5' not in m.name.lower():
                     return m.name
    except Exception as e:
        print(f"!!! 模型搜索失败: {e}")
        return 'models/gemini-pro' # 最后的保底
    return 'models/gemini-pro'

# 初始化模型
target_model_name = get_flash_model()
model = genai.GenerativeModel(target_model_name)

def get_market_sentiment():
    print(">>> [1/3] 正在抓取上证指数(000001)资讯...")
    
    news_text = ""
    try:
        df = ak.stock_news_em(symbol="000001")
        latest_news = df.head(5) # 取最新的5条
        
        news_list = []
        for index, row in latest_news.iterrows():
            title = row.get('新闻标题', '无标题')
            content = row.get('新闻内容', '无内容')
            news_item = f"标题：{title}\n内容：{str(content)[:80]}..." 
            news_list.append(news_item)
            
        news_text = "\n---\n".join(news_list)
        print(">>> 抓取成功！")
        
    except Exception as e:
        print(f"抓取失败: {e}")
        return

    # =====================================================
    # 【核心优化区】：这里修改了 Prompt，要求 AI 说人话
    # =====================================================
    prompt = f"""
    你是A股资深交易员，擅长【右侧趋势交易】，风格犀利直接。
    请阅读以下关于“上
