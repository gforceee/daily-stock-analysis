import os
import akshare as ak
import google.generativeai as genai
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys

# 1. 配置 Key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("Error: 未找到 GEMINI_API_KEY")
    exit(1)

genai.configure(api_key=api_key)

# 2. RSS 生成函数 (纯原生，无依赖)
def update_rss(title, content):
    filename = "rss.xml"
    # RSS 头部模板
    rss_template = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Gemini A股每日早报</title>
  <link>https://github.com/YourUsername/daily-stock-analysis</link>
  <description>由 AI 自动生成的 A股市场情绪日报</description>
</channel>
</rss>
"""
    
    # 如果文件不存在，创建基础结构
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(rss_template)

    try:
        # 解析 XML
        tree = ET.parse(filename)
        root = tree.getroot()
        channel = root.find('channel')

        # 创建新 Item
        new_item = ET.Element('item')
        
        # 标题 (带日期)
        item_title = ET.SubElement(new_item, 'title')
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        item_title.text = f"[{today}] {title}"
        
        # 内容 (支持 HTML 换行)
        item_desc = ET.SubElement(new_item, 'description')
        # 把换行符转换成 HTML 的 <br>，这样 RSS 阅读器里好看
        html_content = content.replace("\n", "<br>")
        item_desc.text = f"<![CDATA[{html_content}]]>"
        
        # 发布时间
        item_pubdate = ET.SubElement(new_item, 'pubDate')
        item_pubdate.text = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        # 插入到 channel 的第一个位置 (在 description 后面)
        # 找到插入点：通常在 title, link, description 之后
        insert_index = 3 
        channel.insert(insert_index, new_item)
        
        #以此限制只保留最近 30 条
        items = channel.findall('item')
        if len(items) > 30:
            for i in range(30, len(items)):
                channel.remove(items[i])

        # 保存文件
        # 为了美观，先用 minidom 格式化一下 (虽然有点多余，但为了兼容性)
        # 这里简单直接写回
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        print(">>> ✅ RSS 文件更新成功！")
        
    except Exception as e:
        print(f">>> ❌ RSS 更新失败: {e}")

# 3. 模型选择逻辑
def get_flash_model():
    print(">>> [0/4] 正在搜索可用的 Flash 模型...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name.lower():
                    print(f">>> 找到目标: {m.name}")
                    return m.name
        # 降级方案
        for m in genai.list_models():
             if 'generateContent' in m.supported_generation_methods:
                 if 'pro' in m.name.lower() and '2.5' not in m.name.lower():
                     return m.name
    except Exception as e:
        pass
    return 'models/gemini-pro'

target_model_name = get_flash_model()
model = genai.GenerativeModel(target_model_name)

def get_market_sentiment():
    print(">>> [1/4] 正在抓取上证指数(000001)资讯...")
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
    你是A股资深交易员，擅长【右侧趋势交易】，风格犀利直接。
    请阅读以下关于“上证指数”的最新 5 条新闻，忽略套话，直击核心。
    新闻内容：{news_text}
    请严格按照以下格式输出（纯文本）：
    【市场温度】：(打分0-100)
    【持仓建议】：(躺赢/减仓/止损/观望)
    【核心理由】：(大白话解释，50字以内)
    """

    print(">>> [2/4] AI 正在分析中...")
    try:
        response = model.generate_content(prompt)
        final_result = response.text
        
        print("\n" + "="*30)
        print(">>> [3/4] 分析完成")
        print(final_result)
        print("="*30)

        # 提取分数做标题
        title = "A股早报"
        if "【市场温度】" in final_result:
             try:
                 score = final_result.split("【市场温度】：")[1].split("\n")[0].strip()
                 title = f"A股早报: {score}"
             except:
                 pass

        # 更新 RSS
        print(">>> [4/4] 更新 RSS Feed...")
        update_rss(title, final_result)

    except Exception as e:
        print(f"AI 调用报错: {e}")

if __name__ == "__main__":
    get_market_sentiment()
