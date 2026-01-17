import os
import re
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai
from googleapiclient.discovery import build
from playwright.sync_api import sync_playwright

# --- 1. 配置加载 ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")


# --- 2. 核心工具函数 ---

def google_search(query):
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID, num=10).execute()  # 每次搜10个
        return res.get('items', [])
    except Exception as e:
        print(f"❌ 搜索出错: {e}")
        return []


def smart_scrape(url):
    """ 使用 Playwright 抓取内容 """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            text = page.inner_text("body")
            browser.close()
            return " ".join(text.split())[:3000]
    except:
        return ""


def deep_analyze(brand_req, page_content):
    """ AI 评估逻辑 """
    prompt = f"品牌需求：{brand_req}\n内容：{page_content}\n分析并输出JSON：{{'name':'','score':0,'contact':'','tags':[],'reason':''}}"
    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else None
    except:
        return None


# --- 3. 智能 Agent 主逻辑 ---

def run_smart_agent():
    brand_req = "推广一款适合程序员的静音、人体工学机械键盘"

    # --- A. 让 AI 自动生成多个搜索维度 ---
    print("🧠 Agent 正在思考多个搜索角度...")
    plan_prompt = f"针对需求 '{brand_req}'，给出3个互不相同的 Google 搜索指令。例如一个针对YouTube，一个针对专业科技媒体，一个针对个人博客。只输出搜索指令，每行一个。"
    plan_res = client.models.generate_content(model="gemini-2.0-flash", contents=plan_prompt)
    search_queries = [q.strip() for q in plan_res.text.strip().split('\n') if q.strip()]

    print(f"📋 确定的搜索计划：\n{search_queries}\n")

    all_data = []
    visited_urls = set()  # 用于记录已经处理过的链接，防止重复

    # --- B. 循环执行搜索计划 ---
    for idx, query in enumerate(search_queries):
        print(f"--- 🚀 正在执行第 {idx + 1} 轮搜索: {query} ---")
        raw_items = google_search(query)

        for item in raw_items:
            url = item['link']

            # 💡 关键：去重检查
            if url in visited_urls:
                continue
            visited_urls.add(url)

            print(f"🔍 正在处理: {item['title'][:30]}...")
            content = smart_scrape(url)

            if content:
                analysis = deep_analyze(brand_req, content)
                if analysis and analysis.get('score', 0) >= 6:  # 只要 6 分以上的优质网红
                    analysis['link'] = url
                    all_data.append(analysis)
                    print(f"   ✅ 发现匹配博主: {analysis['name']} (得分: {analysis['score']})")

    # --- C. 最终汇总保存 ---
    if all_data:
        df = pd.DataFrame(all_data)
        # 按照分数从高到低排序
        df = df.sort_values(by="score", ascending=False)
        df.to_csv("master_influencer_list.csv", index=False, encoding="utf-8-sig")
        print(f"\n🎉 大功告成！共搜集到 {len(all_data)} 位优质候选人，已存入 master_influencer_list.csv")
    else:
        print("\n😔 未能找到匹配的博主，请尝试调整品牌需求关键词。")


if __name__ == "__main__":
    run_smart_agent()