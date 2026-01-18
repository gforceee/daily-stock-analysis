import os
from tavily import TavilyClient
import google.generativeai as genai

# 配置 Key
TAVILY_KEY = os.environ.get("TAVILY_API_KEY")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
tavily = TavilyClient(api_key=TAVILY_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def deep_search_influencer(twitter_id):
    print(f">>> 正在全网搜寻博主 {twitter_id} 的背景资料...")
    
    # 1. 组合搜索指令
    query = f"twitter blogger {twitter_id} success story career path first bucket of gold"
    
    # 2. 调用 Tavily 搜索，获取网页正文
    search_result = tavily.search(query=query, search_depth="advanced", max_results=5)
    
    context = ""
    for res in search_result['results']:
        context += f"\n标题: {res['title']}\n内容: {res['content']}\n"

    # 3. 喂给 Gemini 进行分析
    prompt = f"""
    你是一个深度调查记者。以下是关于推特博主 {twitter_id} 的全网搜索资料：
    {context}
    
    请根据以上资料回答：
    1. 【核心领域】：他主要在哪个圈子（Web3/AI/出海/投资）出名？
    2. 【发家史】：他是如何赚到第一桶金的？关键转折点是什么？
    3. 【内容风格】：他平时分享的东西核心价值在哪里？
    4. 【评价】：他在圈内的影响力如何？
    
    如果资料不足，请基于现有信息进行合理解推测，并注明“基于现有资料推测”。
    请用大白话回答，不要官腔。
    """
    
    print(">>> AI 正在深度分析中...")
    response = model.generate_content(prompt)
    return response.text

if __name__ == "__main__":
    # 暂时手动输入一个 ID 测试，比如 "elonmusk" 或你想分析的博主
    target_id = "elonmusk" 
    report = deep_search_influencer(target_id)
    print("\n" + "="*30)
    print(f"--- {target_id} 深度调查报告 ---")
    print("="*30)
    print(report)
