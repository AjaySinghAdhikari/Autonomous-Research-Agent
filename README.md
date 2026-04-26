# 🤖 Autonomous Research Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/LangGraph-Agentic%20Pipeline-orange?logo=langchain&logoColor=white" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/Groq-Llama%203.3%2070B-purple?logo=meta&logoColor=white" alt="Groq Llama 3.3"/>
  <img src="https://img.shields.io/badge/Streamlit-Frontend-red?logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"/>
</p>

> A 5-agent AI pipeline that autonomously plans, searches, reads, critiques,
> and synthesizes research reports from live web sources — in minutes.

---

## 📚 Table of Contents

- [What It Does](#-what-it-does)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Setup](#-setup)
- [Running the App](#-running-the-app)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 What It Does

Type a research topic and the pipeline automatically:

| Step | Agent | Action |
|------|-------|--------|
| 1 | **Planner** | Breaks the topic into 5 focused sub-questions |
| 2 | **Searcher** | Searches the web for each sub-question via Tavily |
| 3 | **Reader** | Scrapes and stores every article in a vector DB |
| 4 | **Critic** | Identifies contradictions between sources |
| 5 | **Writer** | Synthesizes all findings into a structured Markdown report |

The final report includes a TL;DR, key findings with inline citations, detected contradictions, a confidence assessment, and a full references table.

---

## 🏗️ Architecture

```
User Input (Topic)
       │
       ▼
  ┌─────────┐     ┌──────────┐     ┌────────┐     ┌────────┐     ┌────────┐
  │ Planner │────▶│ Searcher │────▶│ Reader │────▶│ Critic │────▶│ Writer │
  └─────────┘     └──────────┘     └────────┘     └────────┘     └────────┘
  5 sub-questions  Tavily search   Scrape + store   Detect         Markdown
                   results         in ChromaDB      contradictions  report
```

The entire pipeline is orchestrated by **LangGraph**, which manages state across all five agents.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | [LangGraph](https://github.com/langchain-ai/langgraph) |
| LLM | [Groq](https://groq.com/) (Llama 3.3 70B) / [Anthropic](https://anthropic.com/) (Claude) |
| Web Search | [Tavily API](https://tavily.com/) |
| Web Scraping | [Trafilatura](https://trafilatura.readthedocs.io/) |
| Vector Memory | [ChromaDB](https://www.trychroma.com/) |
| Frontend | [Streamlit](https://streamlit.io/) |

---

## ⚙️ Setup

### Prerequisites

- Python 3.10 or higher
- A [Groq API key](https://console.groq.com/keys) (free tier available)
- A [Tavily API key](https://tavily.com/) (free tier available)

### 1. Clone the repository

```bash
git clone https://github.com/AjaySinghAdhikari/Autonomous-Research-Agent.git
cd Autonomous-Research-Agent
```

### 2. Create and activate a virtual environment

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

### 4. Configure API keys

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

> **Optional:** Set `ANTHROPIC_API_KEY` if you want to switch the LLM brain to Claude.

---

## 🖥️ Running the App

```bash
streamlit run app/streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📁 Project Structure

```
Autonomous-Research-Agent/
├── agents/
│   ├── planner.py          # Breaks topic into sub-questions
│   ├── searcher.py         # Web search via Tavily
│   ├── reader.py           # Scrape URLs and store in ChromaDB
│   ├── critic.py           # Detect contradictions across sources
│   └── writer.py           # Synthesize final research report
├── graph/
│   └── research_graph.py   # LangGraph pipeline definition
├── memory/
│   └── vector_store.py     # ChromaDB vector store wrapper
├── tools/
│   ├── search_tool.py      # Tavily search helper
│   └── scraper_tool.py     # Trafilatura scraper helper
├── app/
│   └── streamlit_app.py    # Streamlit web UI
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
