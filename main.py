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

# =======================================================
# 核心修复：暴力搜索 Flash 模型
# =======================================================
def get_flash_model():
    print(">>> [0/3] 正在搜索可用的 Flash 模型...")
    try:
        # 遍历所有模型
        for m in genai.list_models():
            # 必须支持生成内容
            if 'generateContent' in m.supported_generation_methods:
                name = m.name.lower()
                # 只要名字里带 'flash'，我们就用它！
                if 'flash' in name:
                    print(f">>> 找到目标: {m.name}")
                    return m.name
                    
        # 如果实在没找到 Flash，为了不报错，降级去找 Pro
        print(">>> 警告: 没找到 Flash 模型，尝试寻找 Pro...")
        for m in genai.list_models():
             if 'generateContent' in m.supported_generation_methods:
                 if 'pro' in m.name.lower() and '2.5' not in m.name.lower(): # 避开收费的2.5
                     print(f">>> 降级使用: {m.name}")
                     return m.name
                     
    except Exception as e:
        print(f"!!! 模型搜索失败: {e}")
        return None
    
    return None

# 初始化
target_model_name = get_flash_model()

if not target_model_name:
    print("!!! 悲剧了：你的账号似乎找不到任何可用模型。")
    # 最后的最后，死马当活马医，硬试一个最老的
    target_model_name = 'models/gemini-pro' 
    print(f"!!! 尝试强行使用备用方案: {target_model_name}")

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

    prompt = f"""
    你是A股资深交易员。基于以下上证指数最新新闻，写一份简报。
    新闻：
    {news_text}
    请输出格式：
    【整体情绪】：(恐慌/中性/贪婪)
    【核心板块】：(1-2个关键词)
    【犀利点评】：(一句话总结对明日开盘的影响)
    """

    print(">>> [2/3] AI 正在分析中...")
    try:
        response = model.generate_content(prompt)
        print("\n" + "="*30)
        print(">>> [3/3] 分析报告如下：")
        print("="*30)
        print(response.text)
        print("="*30)
    except Exception as e:
        print(f"AI 调用报错: {e}")

if __name__ == "__main__":
    get_market_sentiment()
