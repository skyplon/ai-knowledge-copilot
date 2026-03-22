"""
=========================================================
AI KNOWLEDGE COPILOT — V1 (CHAT-STYLE RAG APPLICATION)
=========================================================

WHAT THIS APP DOES
---------------------------------------------------------
This application allows users to:
- Upload multiple documents (PDF, DOCX, PPTX, CSV)
- Convert them into a searchable knowledge base
- Ask questions in a chat-style interface
- Receive AI-generated answers grounded in the documents

ARCHITECTURE OVERVIEW (RAG PIPELINE)
---------------------------------------------------------
1. File ingestion (multi-format support)
2. Text extraction
3. Chunking (text splitting)
4. Embeddings (OpenAI)
5. Vector storage (FAISS)
6. Retrieval (semantic search)
7. Generation (LLM response with context)

DESIGN PRINCIPLES
---------------------------------------------------------
- Clean, modular structure
- Minimal dependencies (stable deployment)
- Chat-style UX (product-ready)
- Clear documentation for readability
"""

# =========================================================
# 1. IMPORTS & DEPENDENCIES
# =========================================================

import streamlit as st
from tempfile import NamedTemporaryFile

# OpenAI
from openai import OpenAI
client = OpenAI()

# Vector search
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# File processing
from langchain_community.document_loaders import PyPDFLoader
from docx import Document as DocxDocument
from pptx import Presentation
import pandas as pd

# =========================================================
# 2. CUSTOM DOCUMENT CLASS
# =========================================================
# Replaces LangChain Document (simpler + avoids dependency issues)

class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata if metadata else {}

# =========================================================
# 3. FILE PROCESSING FUNCTION
# =========================================================
# Converts uploaded files into text documents

def process_file(file):
    docs = []

    with NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file.read())
        file_path = tmp.name

    # -------- PDF --------
    if file.name.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        docs = loader.load()

    # -------- DOCX --------
    elif file.name.endswith(".docx"):
        doc = DocxDocument(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        docs = [Document(page_content=text)]

    # -------- PPTX --------
    elif file.name.endswith(".pptx"):
        prs = Presentation(file_path)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        docs = [Document(page_content=text)]

    # -------- CSV --------
    elif file.name.endswith(".csv"):
        df = pd.read_csv(file_path)
        docs = [Document(page_content=df.to_string())]

    return docs

# =========================================================
# 4. APP CONFIGURATION
# =========================================================

st.set_page_config(page_title="AI Knowledge Copilot", layout="wide")

# =========================================================
# 5. SIDEBAR (WORKSPACE CONTROL PANEL)
# =========================================================
# Handles file uploads + suggested queries

with st.sidebar:
    st.markdown("## Workspace")
    st.caption("Upload and manage your knowledge sources")

    uploaded_files = st.file_uploader(
        "Upload files",
        accept_multiple_files=True
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)} files uploaded")

    st.divider()

    st.markdown("### Suggested questions")

    suggested = [
        "Summarize these documents",
        "What are the key insights?",
        "What are the risks?",
        "Compare these documents"
    ]

    for q in suggested:
        if st.button(q):
            st.session_state["query"] = q

# =========================================================
# 6. MAIN HEADER
# =========================================================

st.title("AI Knowledge Copilot")
st.caption("Analyze documents, data, and media using a unified AI interface.")

# =========================================================
# 7. BUILD KNOWLEDGE BASE
# =========================================================
# Processes documents → chunks → embeddings → FAISS

all_docs = []

if uploaded_files:
    with st.spinner("Processing documents..."):
        for file in uploaded_files:
            docs = process_file(file)
            all_docs.extend(docs)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    split_docs = splitter.split_documents(all_docs)

    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(split_docs, embeddings)

    st.success(f"{len(split_docs)} chunks indexed successfully")

# =========================================================
# 8. CHAT INTERFACE (CORE UX)
# =========================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

query = st.chat_input("Ask a question about your documents")

# Support suggested questions
if "query" in st.session_state:
    query = st.session_state["query"]
    del st.session_state["query"]

if query and uploaded_files:

    # Add user message
    st.session_state.chat_history.append(("user", query))

    # Retrieve context
    docs = db.similarity_search(query, k=3)
    context = "\n\n".join([d.page_content for d in docs])

    # Generate answer
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer ONLY using the provided context."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
    )

    answer = response.choices[0].message.content

    # Store assistant response
    st.session_state.chat_history.append(("assistant", answer, docs))

# =========================================================
# 9. CHAT DISPLAY (LIKE CHATGPT)
# =========================================================

for msg in st.session_state.chat_history:

    if msg[0] == "user":
        with st.chat_message("user"):
            st.write(msg[1])

    elif msg[0] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg[1])

            # Sources (collapsible)
            with st.expander("Sources"):
                for i, d in enumerate(msg[2]):
                    st.markdown(f"**Source {i+1}**")
                    st.write(d.page_content[:300])

# =========================================================
# 10. EMPTY STATE
# =========================================================

if not uploaded_files:
    st.info("Upload documents from the sidebar to begin.")