# ============================================================
# AI KNOWLEDGE COPILOT — V1 MVP
# ============================================================
# WHAT IS THIS?
# ------------------------------------------------------------
# This application allows users to upload different types of data
# (documents, spreadsheets, images, audio, video) and interact
# with them using AI.
#
# It converts all inputs into text, stores them in a vector
# database, and enables:
# - Question answering (Q&A)
# - Summarization
# - Insight extraction
# - Document comparison
#
# This is an example of a "Retrieval-Augmented Generation (RAG)"
# system with multimodal ingestion.
# ============================================================


# ============================================================
# IMPORT REQUIRED LIBRARIES
# ------------------------------------------------------------
# These libraries handle:
# - UI (Streamlit)
# - File parsing (PDF, DOCX, PPTX, etc.)
# - Multimodal processing (OCR, audio transcription)
# - AI & embeddings (LangChain + OpenAI)
# ============================================================

import streamlit as st
import pytesseract
from PIL import Image
import whisper
import subprocess
import pandas as pd
import xml.etree.ElementTree as ET

from docx import Document as DocxDocument
from pptx import Presentation

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI


# ============================================================
# SYSTEM CONFIGURATION
# ------------------------------------------------------------
# Configure system dependencies like OCR (Tesseract).
# This is required for extracting text from images.
# ============================================================

pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"


# ============================================================
# PAGE CONFIGURATION
# ------------------------------------------------------------
# Define how the app looks in the browser.
# ============================================================

st.set_page_config(page_title="AI Knowledge Copilot", layout="wide")


# ============================================================
# UI STYLING (CUSTOM CSS)
# ------------------------------------------------------------
# Adds a clean, professional design similar to SaaS apps.
# ============================================================

st.markdown("""
<style>
.main { background-color: #f8fafc; }

h1 { font-weight: 700; color: #111827; }
h2, h3 { color: #1f2937; }

.chat-card {
    background: white;
    padding: 1.2rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
}

.user-msg { font-weight: 600; }
.ai-msg { color: #374151; }

section[data-testid="stSidebar"] { background-color: #111827; }

section[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

input, textarea { color: black !important; }

</style>
""", unsafe_allow_html=True)


# ============================================================
# APPLICATION HEADER
# ------------------------------------------------------------
# This is what the user sees first.
# Explains what the app does in simple terms.
# ============================================================

st.markdown("# AI Knowledge Copilot")

st.markdown("""
Analyze documents, structured data, and media using a unified AI interface.

Upload files and ask questions, generate summaries, extract insights,
or compare documents — all in one place.
""")

st.info("Upload files → Ask questions → Generate insights → Compare documents")


# ============================================================
# SIDEBAR — USER INPUT & CONFIGURATION
# ------------------------------------------------------------
# The sidebar acts as a control panel where users:
# - Select analysis mode
# - Upload files
# - Choose documents to compare
# ============================================================

st.sidebar.markdown("## Workspace")

mode = st.sidebar.selectbox(
    "Analysis Mode",
    [
        "Q&A (Ask questions)",
        "Summarize (Overview)",
        "Insights (Key takeaways)"
    ]
)

uploaded_files = st.sidebar.file_uploader(
    "Upload files",
    type=["pdf","txt","docx","pptx","csv","xml","xlsx",
          "png","jpg","jpeg","mp3","wav","mp4"],
    accept_multiple_files=True
)

# Document comparison selection
file_names = [f.name for f in uploaded_files] if uploaded_files else []

compare_docs = st.sidebar.multiselect(
    "Compare two documents",
    file_names,
    max_selections=2
)


# ============================================================
# FILE PROCESSING FUNCTION (MULTIMODAL INGESTION)
# ------------------------------------------------------------
# This is the MOST IMPORTANT part of the system.
#
# It converts ALL file types into text so the AI can understand them.
#
# Example:
# - PDF → text
# - Image → OCR → text
# - Audio → transcription → text
# ============================================================

def process_file(file):

    file_path = f"temp_{file.name}"

    with open(file_path, "wb") as f:
        f.write(file.read())

    docs = []

    try:
        if file.name.endswith(".pdf"):
            docs = PyPDFLoader(file_path).load()

        elif file.name.endswith(".txt"):
            docs = TextLoader(file_path).load()

        elif file.name.endswith(".docx"):
            doc = DocxDocument(file_path)
            text = "\n".join(p.text for p in doc.paragraphs)
            docs = [Document(page_content=text)]

        elif file.name.endswith(".pptx"):
            prs = Presentation(file_path)
            text = "\n".join(
                shape.text for slide in prs.slides
                for shape in slide.shapes if hasattr(shape, "text")
            )
            docs = [Document(page_content=text)]

        elif file.name.endswith(".csv"):
            df = pd.read_csv(file_path)
            docs = [Document(page_content=df.to_string())]

        elif file.name.endswith(".xlsx"):
            df = pd.read_excel(file_path)
            docs = [Document(page_content=df.head().to_string())]

        elif file.name.endswith(".xml"):
            tree = ET.parse(file_path)
            docs = [Document(page_content=ET.tostring(tree.getroot(), encoding="unicode"))]

        elif file.name.lower().endswith((".png",".jpg",".jpeg")):
            text = pytesseract.image_to_string(Image.open(file_path))
            docs = [Document(page_content=text)]

        elif file.name.lower().endswith((".mp3",".wav")):
            result = whisper.load_model("base").transcribe(file_path)
            docs = [Document(page_content=result["text"])]

        elif file.name.lower().endswith(".mp4"):
            audio_path = file_path + ".mp3"
            subprocess.run(["ffmpeg","-i",file_path,"-q:a","0","-map","a",audio_path])
            result = whisper.load_model("base").transcribe(audio_path)
            docs = [Document(page_content=result["text"])]

    except Exception as e:
        st.warning(f"Failed to process {file.name}")

    return docs


# ============================================================
# BUILD VECTOR DATABASE (KNOWLEDGE BASE)
# ------------------------------------------------------------
# Converts text into embeddings so the AI can search
# semantically (not just keyword matching).
# ============================================================

if uploaded_files and "vector_db" not in st.session_state:

    with st.spinner("Processing files and building knowledge base..."):

        all_docs = []

        for file in uploaded_files:
            docs = process_file(file)

            for d in docs:
                d.metadata["source_file"] = file.name
                all_docs.append(d)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )

        split_docs = splitter.split_documents(all_docs)

        db = FAISS.from_documents(split_docs, OpenAIEmbeddings())
        st.session_state.vector_db = db


# ============================================================
# RAG SYSTEM (AI QUESTION ANSWERING)
# ------------------------------------------------------------
# This is where:
# - Relevant chunks are retrieved
# - AI generates a grounded response
# ============================================================

if "vector_db" in st.session_state:

    qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(temperature=0),
        retriever=st.session_state.vector_db.as_retriever(),
        return_source_documents=True
    )

    st.markdown("## Analysis")

    # Suggested questions
    suggested = st.selectbox(
        "Suggested questions",
        ["None",
         "Summarize the documents",
         "What are the key insights?",
         "What are the risks?",
         "Compare the documents"]
    )

    user_input = st.text_input("Ask your own question")

    query = None

    if suggested != "None":
        query = suggested
    elif user_input:
        query = user_input

    if "Summarize" in mode:
        query = "Provide a concise summary"
    elif "Insights" in mode:
        query = "Extract key insights and themes"

    if query:

        with st.spinner("Generating response..."):
            result = qa({"query": query})

        st.markdown("## Results")

        st.markdown(f"""
        <div class="chat-card">
            <div class="user-msg">Query</div>
            <div>{query}</div>
            <br>
            <div class="ai-msg">Response</div>
            <div>{result["result"]}</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Sources"):
            for doc in result["source_documents"]:
                st.write(doc.page_content[:300])


    # ============================================================
    # DOCUMENT COMPARISON FEATURE
    # ------------------------------------------------------------
    # Allows users to compare two uploaded documents
    # ============================================================

    if len(compare_docs) == 2:

        st.markdown("## Document Comparison")

        docs = [
            d.page_content for d in st.session_state.vector_db.docstore._dict.values()
            if d.metadata.get("source_file") in compare_docs
        ]

        combined = "\n\n".join(docs[:10])

        prompt = f"""
        Compare these documents:
        {combined}

        Highlight:
        - Differences
        - Similarities
        - Key insights
        """

        response = ChatOpenAI().invoke(prompt)

        st.write(response.content)

else:
    st.info("Upload files in the sidebar to begin.")