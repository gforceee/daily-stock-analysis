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

# 2. 模型选择逻辑
def get_flash_model():
    print(">>> [0/3] 正在搜索可用的 Flash 模型...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name.lower():
                    print(f">>> 找到目标: {m.name}")
                    return m.name
        print(">>> 警告: 没找到 Flash，尝试 Pro...")
        for m in genai.list_models():
             if 'generateContent' in m.supported_generation_methods:
                 if 'pro' in m.name.lower() and '2.5' not in m.name.lower():
                     return m.name
    except Exception as e:
        print(f"!!! 模型搜索失败: {e}")
        return 'models/gemini-pro'
    return 'models/gemini-pro'

# 初始化模型
target_model_name = get_flash_model()
model = genai.GenerativeModel(target_model_name)

def get_market_sentiment():
    print(">>> [1/3] 正在抓取上证指数(000001)资讯...")
    
    news_text = ""
    try:
        df = ak.stock_news_em(symbol="000001")
        latest_news = df.head(5)
        
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
    # 注意：下面这个 prompt 必须用三个引号结尾，千万别漏了
    # =====================================================
    prompt = f"""
    你是A股资深交易员，擅长【右侧趋势交易】，风格犀利直接。
    请阅读以下关于“上证指数”的最新 5 条新闻，忽略套话，直击核心。
    
    新闻内容：
    {news_text}
    
    请严格按照以下格式输出（不要Markdown，直接纯文本）：
    
    【市场温度】：(请打分，0-100分。0是极度冰点，50是震荡，80以上是过热)
    【持仓建议】：(针对持有权重股的人：继续躺赢 / 逢高减仓 / 止损离场？选一个)
    【空仓建议】：(针对想进场的人：立即买入 / 回调低吸 / 观望勿动？选一个)
    【核心理由】：(用最直白的大白话解释为什么，不要超过50个字)
    """

    print(">>> [2/3] AI 正在分析中...")
    try:
        response = model.generate_content(prompt)
        print("\n" + "="*30)
        print(">>> [3/3] 优化后的分析报告：")
        print("="*30)
        print(response.text)
        print("="*30)
    except Exception as e:
        print(f"AI 调用报错: {e}")

if __name__ == "__main__":
    get_market_sentiment()
