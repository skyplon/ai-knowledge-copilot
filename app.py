"""
AI KNOWLEDGE COPILOT (V1 - CLEAN RAG IMPLEMENTATION)

---------------------------------------------------
WHAT THIS APP DOES
---------------------------------------------------
This application allows users to upload multiple files (PDF, DOCX, PPTX, CSV)
and interact with them using natural language.

It implements a Retrieval-Augmented Generation (RAG) system:
1. Extracts text from files
2. Splits text into chunks
3. Converts chunks into embeddings
4. Stores embeddings in a vector database (FAISS)
5. Retrieves relevant chunks based on user query
6. Sends context + question to an LLM (OpenAI)
7. Returns grounded answers + sources

---------------------------------------------------
KEY DESIGN PRINCIPLES
---------------------------------------------------
- No heavy LangChain abstractions (more stable for deployment)
- Modular file processing
- Clear separation of responsibilities
- Production-friendly architecture
"""

# =========================================================
# 1. IMPORTS & DEPENDENCIES
# =========================================================
# This section loads all required libraries

import streamlit as st
import os
from tempfile import NamedTemporaryFile

# OpenAI client (LLM)
from openai import OpenAI
client = OpenAI()

# Vector DB + embeddings (safe LangChain components only)
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings

# Text splitting (modern compatible module)
from langchain_text_splitters import RecursiveCharacterTextSplitter

# File loaders
from langchain_community.document_loaders import PyPDFLoader
from docx import Document as DocxDocument
from pptx import Presentation
import pandas as pd

# =========================================================
# CUSTOM DOCUMENT CLASS (replaces LangChain Document)
# =========================================================
class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata if metadata else {}

# =========================================================
# 2. UI CONFIGURATION
# =========================================================
# This defines the layout and initial UI components

# =========================================================
# SIDEBAR (WORKSPACE PANEL)
# =========================================================
with st.sidebar:
    st.markdown("## Workspace")

    st.markdown("Upload and manage your knowledge sources")

    uploaded_files = st.file_uploader(
        "Upload files",
        accept_multiple_files=True
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)} files uploaded")

    st.divider()

    st.markdown("### Suggested questions")

    suggested_questions = [
        "Summarize these documents",
        "What are the key insights?",
        "What are the risks or gaps?",
        "Compare these documents"
    ]

    for q in suggested_questions:
        if st.button(q):
            st.session_state["query"] = q


# =========================================================
# MAIN PAGE HEADER
# =========================================================
st.title("AI Knowledge Copilot")
st.caption("Analyze documents, data, and media using a unified AI interface.")

# =========================================================
# DOCUMENT PROCESSING
# =========================================================
all_docs = []

if uploaded_files:
    with st.spinner("Processing documents..."):
        for file in uploaded_files:
            docs = process_file(file)
            all_docs.extend(docs)

# =========================================================
# BUILD VECTOR STORE
# =========================================================
if all_docs:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    split_docs = splitter.split_documents(all_docs)

    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(split_docs, embeddings)

    st.success(f"{len(split_docs)} chunks indexed")

    # =====================================================
    # QUERY INPUT
    # =====================================================
    query = st.text_input(
        "Ask a question about your data",
        value=st.session_state.get("query", "")
    )

    if query:
        with st.spinner("Generating answer..."):

            docs = db.similarity_search(query, k=3)
            context = "\n\n".join([d.page_content for d in docs])

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Answer based only on the provided context."
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}"
                    }
                ]
            )

            answer = response.choices[0].message.content

            # =================================================
            # ANSWER DISPLAY
            # =================================================
            st.subheader("Answer")
            st.write(answer)

            # =================================================
            # SOURCES (COLLAPSIBLE)
            # =================================================
            with st.expander("View sources"):
                for i, d in enumerate(docs):
                    st.markdown(f"**Source {i+1}**")
                    st.write(d.page_content[:500])

if not uploaded_files:
    st.info("👈 Upload documents from the workspace panel to begin")

# =========================================================
# 3. FILE PROCESSING FUNCTION
# =========================================================
# This function converts uploaded files into text documents
# that the AI system can understand

def process_file(file):
    docs = []

    # Save file temporarily
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
# 4. FILE UPLOAD INTERFACE
# =========================================================
# Allows users to upload multiple files

all_docs = []

if uploaded_files:
    for file in uploaded_files:
        docs = process_file(file)
        all_docs.extend(docs)

# =========================================================
# 5. BUILD VECTOR DATABASE (FAISS)
# =========================================================
# Converts documents into embeddings and stores them
# for semantic search

if all_docs:
    st.info("Processing documents and building knowledge base...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    split_docs = splitter.split_documents(all_docs)

    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(split_docs, embeddings)

    st.success(f"✅ {len(split_docs)} chunks indexed successfully")

    # =====================================================
    # 6. USER QUERY INTERFACE
    # =====================================================
    # Allows users to ask questions about uploaded data

    query = st.text_input("💬 Ask a question about your data")

    if query:
        # =================================================
        # 7. RETRIEVAL STEP (Semantic Search)
        # =================================================
        # Find the most relevant document chunks

        docs = db.similarity_search(query, k=3)

        context = "\n\n".join([d.page_content for d in docs])

        # =================================================
        # 8. GENERATION STEP (LLM RESPONSE)
        # =================================================
        # Send retrieved context + user question to OpenAI

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that answers questions using ONLY the provided context."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}"
                }
            ]
        )

        answer = response.choices[0].message.content

        # =================================================
        # 9. OUTPUT DISPLAY
        # =================================================
        # Show answer + supporting sources

        st.subheader("📌 Answer")
        st.write(answer)

        st.subheader("📚 Sources (retrieved context)")
        for i, d in enumerate(docs):
            st.markdown(f"**Source {i+1}:**")
            st.write(d.page_content[:500])

else:
    st.warning("Upload at least one file to begin.")