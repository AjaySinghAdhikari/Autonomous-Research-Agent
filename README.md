# 🤖 Autonomous Research Agent



## 🚀 What It Does

You type a research topic → the system:
1. **Planner** — breaks it into 5 focused sub-questions
2. **Searcher** — searches the web for each question
3. **Reader** — scrapes and reads every article
4. **Critic** — finds contradictions between sources
5. **Writer** — synthesizes everything into a structured report

## 🛠️ Tech Stack

- **Agent Framework** — LangGraph
- **AI Brain** — Claude API (Anthropic) / Groq (Llama3)
- **Web Search** — Tavily API
- **Vector Memory** — ChromaDB
- **Frontend** — Streamlit

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/autonomous-research-agent.git
cd autonomous-research-agent
```

### 2. Create virtual environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your API keys
```bash
cp .env.example .env
```
Then open `.env` and fill in:
- `TAVILY_API_KEY`
- `GROQ_API_KEY` (or `ANTHROPIC_API_KEY`)

## 🖥️ Running the App
```bash
streamlit run app/streamlit_app.py
```
