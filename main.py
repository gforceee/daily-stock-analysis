import os
import akshare as ak
import google.generativeai as genai
import time
import pandas as pd

# 1. 配置 Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: 未找到 GEMINI_API_KEY")
    exit(1)

genai.configure(api_key=api_key)

# =======================================================
# 核心修复：不再自动寻找，强制指定 'gemini-1.5-flash'
# 这是目前免费额度最高、最稳定的版本
# =======================================================
MODEL_NAME = 'gemini-1.5-flash'
print(f">>> 正在初始化模型: {MODEL_NAME} ...")
model = genai.GenerativeModel(MODEL_NAME)

def get_market_sentiment():
    print(">>> [1/3] 正在抓取上证指数(000001)最新资讯...")
    
    news_text = ""
    try:
        # 东方财富接口
        df = ak.stock_news_em(symbol="000001")
        latest_news = df.head(5)
        
        news_list = []
        for index, row in latest_news.iterrows():
            title = row.get('新闻标题', '无标题')
            content = row.get('新闻内容', '无内容')
            # 缩减字数，节省 token
            news_item = f"标题：{title}\n内容：{str(content)[:80]}..." 
            news_list.append(news_item)
            
        news_text = "\n---\n".join(news_list)
        print(">>> 抓取成功！")
        
    except Exception as e:
        print(f"抓取失败: {e}")
        return

    # 构造 Prompt
    prompt = f"""
    你是A股资深交易员。基于以下上证指数最新新闻，写一份简报。
    
    新闻：
    {news_text}
    
    请输出格式：
    【整体情绪】：(恐慌/中性/贪婪)
    【核心板块】：(1-2个关键词)
    【犀利点评】：(一句话总结对明日开盘影响)
    """

    print(">>> [2/3] AI 正在分析中 (请稍候)...")
    try:
        # 增加一个超时设置，防止卡死
        response = model.generate_content(prompt)
        print("\n" + "="*30)
        print(">>> [3/3] 分析报告如下：")
        print("="*30)
        print(response.text)
        print("="*30)
    except Exception as e:
        print(f"AI 调用报错: {e}")
        print("建议：如果是 Quota 问题，请检查 API Key 是否开通了 Billing 或者换个号。")

if __name__ == "__main__":
    get_market_sentiment()
