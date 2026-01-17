import streamlit as st
import os, re, json, pandas as pd
from dotenv import load_dotenv
from google import genai
from googleapiclient.discovery import build

# --- 1. 初始化 ---
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ID = os.getenv("SEARCH_ENGINE_ID")
client = genai.Client(api_key=GEMINI_KEY)


# --- 2. Agent 的工具函数 ---

def google_search(query):
    """搜索功能"""
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_KEY)
        res = service.cse().list(q=query, cx=SEARCH_ID, num=8).execute()
        return res.get('items', [])
    except Exception as e:
        st.error(f"搜索出错: {e}")
        return []


def get_agent_plan(user_input, history):
    """
    大脑：决定是直接聊天，还是去搜索。
    如果是搜索，它会返回 [SEARCH] 关键词
    """
    prompt = f"""
    你是一个海外网红营销助手。用户需求是："{user_input}"

    任务：
    1. 如果用户让你找网红/博主，请输出 [SEARCH] 后面跟着 2 个最相关的 Google 搜索词。
    2. 如果用户只是在聊天或提问，请直接回答。

    背景知识：如果产品是“宠物骨灰盒”，合适的博主包括：兽医(Veterinarian)、宠物失去支持(Pet Loss Support)、高龄犬护理(Senior Dog Care)、宠物知识科普。

    对话历史：{history[-2:] if history else "无"}
    """
    res = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return res.text


def evaluate_influencer(item, brand_goal):
    """评价单个搜索结果"""
    prompt = f"""
    品牌目标：{brand_goal}
    网页标题：{item['title']}
    网页摘要：{item['snippet']}

    请判断这个链接是否是一个合适的网红/博主。
    输出 JSON 格式（必须包含 name, score, reason, email_draft）：
    {{ "name": "博主名/频道名", "score": 1-10分, "reason": "匹配理由", "email_draft": "100字英文邀约" }}
    """
    try:
        res = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        match = re.search(r'\{.*\}', res.text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except:
        return None


# --- 3. Streamlit 界面逻辑 ---

st.set_page_config(page_title="Pet Agent", layout="wide")
st.title("🐾 宠物网红营销 Agent")

# 初始化 Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "results_data" not in st.session_state:
    st.session_state.results_data = []

# 显示对话历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入
if user_prompt := st.chat_input("例如：帮我找一些分享宠物护理知识的 YouTube 博主"):
    # 记录用户话语
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        # 1. AI 思考计划
        with st.spinner("思考中..."):
            agent_plan = get_agent_plan(user_prompt, st.session_state.messages)

        if "[SEARCH]" in agent_plan:
            # 2. 执行搜索
            search_query = agent_plan.replace("[SEARCH]", "").strip()
            st.write(f"🕵️ 我决定去搜这些词: `{search_query}`")

            raw_items = google_search(search_query)

            if not raw_items:
                st.write("😔 没搜到任何相关网页，请尝试换个描述试试？")
            else:
                # 3. 分析结果
                results = []
                progress_text = st.empty()
                for i, item in enumerate(raw_items[:6]):
                    progress_text.text(f"正在分析第 {i + 1}/6 个潜在博主...")
                    analysis = evaluate_influencer(item, user_prompt)
                    # 降低门槛，只要大于等于 3 分都显示出来
                    if analysis and analysis.get('score', 0) >= 3:
                        analysis['link'] = item['link']
                        results.append(analysis)

                progress_text.empty()

                # 4. 展示结果 (增加报错保护)
                if results:
                    st.write(f"✅ 我为你找到了 {len(results)} 位值得关注的候选人：")
                    df = pd.DataFrame(results)
                    # 只有当 df 不为空且包含目标列时才展示
                    cols = ['name', 'score', 'reason', 'link']
                    available_cols = [c for c in cols if c in df.columns]
                    st.table(df[available_cols])

                    st.session_state.results_data = results
                    st.session_state.messages.append(
                        {"role": "assistant", "content": f"我找到了 {len(results)} 位博主，详情已展示。"})
                else:
                    st.write("😔 我看了一下搜索结果，但似乎没有发现特别契合的博主，你要不要换个方向（比如搜‘兽医’）？")
                    st.session_state.messages.append({"role": "assistant", "content": "未能找到匹配博主。"})
        else:
            # 直接回答
            st.markdown(agent_plan)
            st.session_state.messages.append({"role": "assistant", "content": agent_plan})

# 侧边栏：显示邀约邮件
if st.session_state.results_data:
    st.sidebar.title("✉️ 邀约信预览")
    for res in st.session_state.results_data:
        with st.sidebar.expander(f"博主: {res.get('name', '未知')}"):
            st.write(f"**匹配度:** {res.get('score', 0)}")
            st.code(res.get('email_draft', '无邮件内容'), language="markdown")