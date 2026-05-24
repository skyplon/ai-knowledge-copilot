# 🧠 AI Knowledge Copilot

AI-powered document intelligence assistant built with OpenAI + Streamlit.

Upload documents, ask questions in natural language, and generate context-aware insights using a lightweight Retrieval-Augmented Generation (RAG-lite) architecture.

---

## 🌐 Live Demo

🚀 https://ai-knowledge-copilot-qqurmsj8tcmzugptlwo245.streamlit.app/

> 💻 Best experience on desktop (V1 limitation).
> 
<p align="center">
  <img src="assets/Screenshot.png" width="800"/>
</p>

---

## 🚀 Overview

AI Knowledge Copilot enables users to:

- Upload multiple document types (PDF, DOCX, PPTX, CSV, TXT)
- Extract and aggregate knowledge across files
- Ask natural language questions
- Generate AI-powered summaries and insights
- Interact through a ChatGPT-style interface

This project demonstrates how enterprise AI copilots can transform unstructured data into conversational intelligence.

---

## 🧠 Core Use Cases

- 📚 Knowledge synthesis
- 🔍 Insight extraction
- ⚖️ Multi-document comparison
- 🧾 Executive briefings
- 🏢 Internal enterprise copilots

---

## 🏗️ System Architecture

```text
User Uploads Documents
        ↓
Document Parsing Layer
(PDF / DOCX / PPTX / CSV)
        ↓
Text Extraction
        ↓
Context Aggregation
        ↓
GPT-4o-mini Prompting
        ↓
AI Response Generation
        ↓
Chat-style UI Rendering
```
---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend/UI | Streamlit |
| LLM | OpenAI GPT-4o-mini |
| PDF Parsing | PyPDF2 |
| DOCX Parsing | python-docx |
| PPTX Parsing | python-pptx |
| Structured Data | pandas |
| Deployment | Streamlit Cloud |
| Version Control | GitHub |

---

## 💡 Features

- 📂 Multi-file upload
- 💬 Chat-style AI interaction
- ⚡ Suggested questions
- 👍 👎 Feedback system
- 🧠 Context-aware responses
- ☁️ Live cloud deployment

---

## ⚖️ Product & Engineering Trade-offs

| Decision | Reason |
|---|---|
| RAG-lite architecture | Faster MVP development |
| No vector database in V1 | Reduced complexity and deployment overhead |
| Streamlit instead of React | Rapid prototyping and iteration |
| GPT-4o-mini | Lower inference cost and fast responses |
| Desktop-first UX | Stable and cleaner demo experience |

---

## 📌 Known Limitations (V1)

- Optimized primarily for desktop usage
- Some mobile-uploaded PDFs may fail due to encoding inconsistencies
- OCR for scanned/image-based documents is not yet supported
- No semantic retrieval/vector search yet

---

## 🚀 Future Roadmap

### V2
- Vector embeddings + semantic retrieval
- Inline citations
- Persistent memory
- Robust mobile support
- OCR fallback for scanned documents

### V3
- Multi-agent orchestration
- Enterprise integrations (Drive, Slack, Notion)
- Analytics dashboard
- Human-in-the-loop review workflows

---

## ⚙️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/skyplon/ai-knowledge-copilot.git
cd ai-knowledge-copilot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API key

Create:

```text
.streamlit/secrets.toml
```

Add:

```toml
OPENAI_API_KEY = "your_api_key_here"
```

### 4. Run the app

```bash
streamlit run app.py
```

---

## ☁️ Deployment

This application is deployed using:

- GitHub
- Streamlit Cloud
- OpenAI API

Every push to the `main` branch automatically redeploys the app.

---

## 🧠 AI / Product Thinking Behind the Project

This project was intentionally designed as a lightweight AI copilot MVP focused on:

- Rapid experimentation
- Human-centered AI UX
- Enterprise knowledge workflows
- AI product architecture trade-offs
- Real-world deployment simplicity

Rather than optimizing for scale in V1, the focus was on validating:
- usability
- workflow value
- interaction patterns
- deployment feasibility

---

## 👤 Author

Juan Navarrete

Senior AI Product Manager focused on:
- Enterprise AI systems
- AI copilots
- Agentic workflows
- Knowledge intelligence platforms

🌎 GitHub: https://github.com/skyplon

---

## ⭐ Support

If you found this project interesting, feel free to give it a star ⭐
