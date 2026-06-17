# Autonomous Research Agent

An autonomous multi-agent system that plans, searches, reads, critiques, and synthesizes structured research reports from live web sources — built on a five-stage LangGraph pipeline.

---

## Overview

Autonomous Research Agent automates the end-to-end research workflow. Given a single topic, the system decomposes it into focused sub-questions, gathers and reads relevant sources from the web, identifies contradictions or gaps across them, and produces a coherent, well-structured report — with minimal human intervention.

This project explores agentic orchestration, retrieval-augmented reasoning, and multi-model LLM routing as building blocks for autonomous research systems.

---

## Pipeline Architecture

The system is composed of five specialized agents, each responsible for a discrete stage of the research process:

| Stage | Agent | Responsibility |
|-------|-------|-----------------|
| 1 | **Planner** | Decomposes the research topic into 5 focused sub-questions |
| 2 | **Searcher** | Queries the web for relevant sources per sub-question |
| 3 | **Reader** | Scrapes and parses content from retrieved sources |
| 4 | **Critic** | Cross-references sources to surface contradictions and inconsistencies |
| 5 | **Writer** | Synthesizes findings into a structured, citation-aware report |

The pipeline is orchestrated as a directed graph, allowing for clear state management and modular extension of individual stages.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Orchestration | LangGraph |
| LLM Backend | Claude API (Anthropic) / Groq (Llama 3) |
| Web Search | Tavily API |
| Vector Memory | ChromaDB |
| Frontend | Streamlit |

---

## Getting Started

### Prerequisites

- Python 3.10+
- API keys for Tavily, and either Groq or Anthropic

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/autonomous-research-agent.git
cd autonomous-research-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and provide the following:
TAVILY_API_KEY=your_key_here

GROQ_API_KEY=your_key_here        # if using Groq

ANTHROPIC_API_KEY=your_key_here   # if using Claude

### 5. Run the application

```bash
streamlit run app/streamlit_app.py
```
<<<<<<< HEAD

---

## Project Structure

autonomous-research-agent/

├── app/

│   └── streamlit_app.py     # Streamlit frontend entry point

├── agents/                  # Planner, Searcher, Reader, Critic, Writer

├── graph/                   # LangGraph pipeline definition

├── requirements.txt

├── .env.example

└── README.md


---

## Roadmap

- [ ] Support for additional search providers
- [ ] Configurable number of sub-questions
- [ ] Export reports to PDF / Markdown
- [ ] Source reliability scoring

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
