import os
import akshare as ak
import google.generativeai as genai
import datetime

# 1. 从环境变量获取 Key (由 GitHub Actions 注入)
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("Error: 未找到 GEMINI_API_KEY，请检查 GitHub Secrets 配置！")
    exit(1)

# 2. 配置 Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

def get_market_sentiment():
    print(">>> [1/3] 正在抓取财联社-今日电报...")
    # 获取财联社电报，只取最新的 5 条，避免 token 超标
    try:
        df = ak.stock_telegraph_cls()
        news_list = df.head(5)['内容'].tolist()
        news_text = "\n---\n".join(news_list)
        print(">>> 抓取成功！准备发送给 AI...")
    except Exception as e:
        print(f"抓取失败: {e}")
        return

    # 3. 构造 Prompt
    prompt = f"""
    你是 A股资深交易员。请根据以下最新的 5 条财经新闻，生成一份简报。
    
    新闻内容：
    {news_text}
    
    请输出以下格式（JSON）：
    {{
        "整体情绪": "恐慌/中性/贪婪",
        "核心利好板块": ["板块A", "板块B"],
        "简短点评": "用一句犀利的话总结对明天开盘的影响"
    }}
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
