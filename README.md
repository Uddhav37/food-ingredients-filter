# 🧪 IngredientIQ — AI-Powered Ingredient Health Analyzer

> **Snap. Analyze. Decide.** — Turn any product label into an instant, AI-researched health verdict.***

## 📖 Overview

IngredientIQ is an agentic AI application that analyzes product ingredient labels from a photo and gives a clear **BUY / DON'T BUY** recommendation backed by real-time web research. It combines Google Cloud Vision OCR, LangChain ReAct agents, Gemini Pro, and Tavily search to autonomously investigate every ingredient — then synthesizes findings into a human-readable health verdict.

***

## ✨ Features

- 📸 **Image-based OCR** — Upload a photo of any ingredient label; Google Cloud Vision extracts text with 90%+ accuracy
- 🤖 **Agentic Research** — A LangChain ReAct agent autonomously searches the web for health information on each ingredient
- 🧠 **In-Memory Context** — Agents maintain multi-step reasoning context for deeper, coherent analysis
- 🗄️ **Ingredient Database** — Every researched ingredient is cached; repeat scans are near-instant
- 📊 **Health Scoring** — Ingredients scored individually and aggregated into a product-level health rating
- ✅ **Clear Verdict** — BUY or DON'T BUY with full natural-language reasoning and per-ingredient breakdown

***

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│          Streamlit UI           │
└──────────────┬──────────────────┘
               │
   ┌───────────▼───────────┐
   │      OCR Service      │
   │  Google Cloud Vision  │
   └───────────┬───────────┘
               │  Ingredients List
   ┌───────────▼───────────┐
   │   LangChain Agent     │◄── Gemini Pro (Vertex AI)
   │  ReAct + Tavily Search│
   └───────────┬───────────┘
               │  Research Results
   ┌───────────▼───────────┐
   │  Recommendation Engine│
   │  Health Score + Verdict│
   └───────────┬───────────┘
               │
   ┌───────────▼───────────┐
   │   Ingredient Database │
   └───────────────────────┘
```

***

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit |
| OCR Engine | Google Cloud Vision API |
| AI Agent Framework | LangChain (ReAct Agent) |
| Large Language Model | Gemini Pro via Vertex AI |
| Web Search Tool | Tavily Search API |
| Database | Cloud Firestore |
| Deployment | Google Cloud Run + Docker |

***

## 📂 Project Structure

```
ingredientiq/
├── app.py                    # Streamlit entry point
├── services/
│   ├── ocr_service.py        # Vision API + ingredient parser
│   ├── agent_service.py      # LangChain ReAct agent
│   ├── recommendation.py     # Health score + verdict generator
│   └── database.py           # DB operations
├── prompts/
│   └── research_prompt.py    # Agent prompt templates
├── utils/
│   ├── text_cleaner.py       # OCR normalization
│   └── helpers.py
├── Dockerfile
├── .env.example
└── README.md
```

***

## 🔄 How It Works

1. **Upload** — User uploads a photo of a product's ingredient label
2. **OCR** — Cloud Vision extracts and parses individual ingredients
3. **Research** — A LangChain ReAct agent searches the web per ingredient for health impacts, safety flags, and regulatory status
4. **Cache** — All findings saved to DB; previously seen ingredients load instantly
5. **Verdict** — Gemini Pro generates a BUY / DON'T BUY recommendation with full reasoning

***

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

***

<p align="center">Built with ❤️ at Hackathon 2026</p>
