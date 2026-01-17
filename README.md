# Influencer-Sourcing-Agent
# 🐾 AI Influencer Sourcing Agent (Conversational)

这是一个基于 Google Gemini 2.0 Flash 和 Google Search API 开发的智能网红营销代理。它不仅是一个搜索工具，更是一个能够理解用户意图、自主规划搜索策略并生成个性化邀约邮件的智能体（Agent）。

## 🌟 核心功能
- **对话式交互**：像聊天一样下达指令，Agent 会理解上下文。
- **自主搜索规划**：Agent 会根据产品属性自动联想相关的博主领域（如：将“宠物骨灰盒”关联至“兽医”和“宠物失去支持”）。
- **智能分析评估**：基于 Google 搜索摘要进行实时评分，筛选最匹配的候选人。
- **个性化邮件生成**：为每位博主量身定制英文邀约信，提高合作成功率。
- **极速响应**：基于异步处理和 Gemini 2.0 Flash 模型。

## 🛠️ 技术栈
- **Python 3.14**
- **LLM**: Google Gemini 2.0 Flash
- **UI**: Streamlit
- **Search API**: Google Custom Search JSON API
- **Data**: Pandas

## 🚀 快速开始
1. 克隆本项目：`git clone https://github.com/你的用户名/Influencer-Sourcing-Agent.git`
2. 安装依赖：`pip install -r requirements.txt`
3. 配置环境变量：在 `.env` 文件中填入你的 `GEMINI_API_KEY`, `GOOGLE_API_KEY` 和 `SEARCH_ENGINE_ID`。
4. 启动应用：`streamlit run app.py`

## 📈 未来规划
- 引入多代理协作架构（CrewAI/LangGraph）。
- 增加长期记忆（Memory）功能，记录已联系过的博主。
- 增加对社交平台（Instagram/TikTok）的直接内容爬取。
