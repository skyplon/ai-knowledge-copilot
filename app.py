"""
=========================================================
AI KNOWLEDGE COPILOT — V1 PRO (CHAT + POLISHED UI)
=========================================================

This version upgrades:
- Clean chat interface
- Professional UI styling
- Sidebar workspace model
- Improved readability and spacing
"""

# =========================================================
# 1. IMPORTS
# =========================================================

import streamlit as st
from tempfile import NamedTemporaryFile

from openai import OpenAI
client = OpenAI()

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.document_loaders import PyPDFLoader
from docx import Document as DocxDocument
from pptx import Presentation
import pandas as pd

# =========================================================
# 2. PAGE CONFIG + STYLING
# =========================================================

st.set_page_config(page_title="AI Knowledge Copilot", layout="wide")

# 🎨 CUSTOM CSS (PRO LOOK)
st.markdown("""
<style>
.main {
    padding-top: 2rem;
}

.block-container {
    padding-top: 2rem;
}

h1 {
    font-weight: 700;
}

[data-testid="stSidebar"] {
    background-color: #0f172a;
    color: white;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.stChatMessage {
    border-radius: 12px;
    padding: 12px;
}

.stTextInput input {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. DOCUMENT CLASS
# =========================================================

class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata if metadata else {}

# =========================================================
# 4. FILE PROCESSING
# =========================================================

def process_file(file):
    docs = []

    with NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file.read())
        file_path = tmp.name

    if file.name.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        docs = loader.load()

    elif file.name.endswith(".docx"):
        doc = DocxDocument(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        docs = [Document(text)]

    elif file.name.endswith(".pptx"):
        prs = Presentation(file_path)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        docs = [Document(text)]

    elif file.name.endswith(".csv"):
        df = pd.read_csv(file_path)
        docs = [Document(df.to_string())]

    return docs

# =========================================================
# 5. SIDEBAR (WORKSPACE)
# =========================================================

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

st.markdown("# AI Knowledge Copilot")
st.markdown(
    "<div style='color:gray; margin-bottom:20px;'>Analyze documents and interact with knowledge using AI</div>",
    unsafe_allow_html=True
)

# =========================================================
# 7. BUILD KNOWLEDGE BASE
# =========================================================

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
# 8. CHAT STATE
# =========================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

query = st.chat_input("Ask anything about your documents...")

# Suggested question trigger
if "query" in st.session_state:
    query = st.session_state["query"]
    del st.session_state["query"]

# =========================================================
# 9. CHAT LOGIC
# =========================================================

if query and uploaded_files:

    st.session_state.chat_history.append(("user", query))

    docs = db.similarity_search(query, k=3)
    context = "\n\n".join([d.page_content for d in docs])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Answer ONLY from the provided context."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
    )

    answer = response.choices[0].message.content

    st.session_state.chat_history.append(("assistant", answer, docs))

# =========================================================
# 10. CHAT UI (CHATGPT STYLE)
# =========================================================

for msg in st.session_state.chat_history:

    if msg[0] == "user":
        with st.chat_message("user"):
            st.write(msg[1])

    elif msg[0] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg[1])

            with st.expander("Sources"):
                for i, d in enumerate(msg[2]):
                    st.markdown(f"**Source {i+1}**")
                    st.write(d.page_content[:300])

# =========================================================
# 11. EMPTY STATE
# =========================================================

if not uploaded_files:
    st.info("Upload documents from the sidebar to begin.")