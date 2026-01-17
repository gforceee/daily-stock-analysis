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
# 使用更通用的 gemini-pro 模型，避免 flash 模型有时候不可用的问题
model = genai.GenerativeModel('gemini-pro')

def get_market_sentiment():
    print(">>> [1/3] 正在抓取上证指数(000001)最新资讯...")
    
    news_text = ""
    try:
        # 替换为东方财富-个股新闻接口，查询"上证指数"的新闻
        # 000001 代表上证指数，这里的新闻最能代表大盘
        df = ak.stock_news_em(symbol="000001")
        
        # 只取最新的 5 条
        latest_news = df.head(5)
        
        # 拼接新闻标题和内容
        news_list = []
        for index, row in latest_news.iterrows():
            # 东方财富的列名通常是 '新闻标题' 和 '新闻内容'
            title = row.get('新闻标题', '无标题')
            content = row.get('新闻内容', '无内容')
            # 稍微清洗一下，去掉过多的换行
            news_item = f"标题：{title}\n内容：{str(content)[:100]}..." 
            news_list.append(news_item)
            
        news_text = "\n---\n".join(news_list)
        print(">>> 抓取成功！准备发送给 AI...")
        
    except Exception as e:
        print(f"抓取失败: {e}")
        # 如果 akshare 报错，我们打印具体的列名以便调试
        try:
            print("尝试打印数据列名:", df.columns)
        except:
            pass
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
