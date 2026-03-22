############################################################
# 🧠 AI KNOWLEDGE COPILOT — V1 (SELF-DOCUMENTED VERSION)
############################################################
"""
OVERVIEW
------------------------------------------------------------
This application is an AI-powered document analysis tool that:
- Ingests multiple file types (PDF, DOCX, PPTX, CSV, TXT)
- Converts them into a unified text representation
- Enables users to ask questions using a chat interface
- Uses an LLM (OpenAI GPT-4o-mini) to generate answers

ARCHITECTURE (RAG-LITE APPROACH)
------------------------------------------------------------
Instead of a full vector database pipeline, this version uses:

    Documents → Text Extraction → Context Injection → LLM

This simplifies deployment while still enabling contextual reasoning.

KEY TECHNOLOGIES
------------------------------------------------------------
- Streamlit → UI framework
- OpenAI GPT-4o-mini → Language model (reasoning engine)
- PyPDF2 / python-docx / python-pptx → File parsing
- Pandas → Structured data handling

DESIGN PRINCIPLES
------------------------------------------------------------
- Simplicity over complexity (no heavy frameworks)
- Clean UX (chat-based interaction)
- Stateful UI (chat memory + feedback system)
- Deployment-ready architecture
"""


############################################################
# 1. IMPORTS — External Libraries & Dependencies
############################################################
"""
This section loads all required libraries.

We intentionally use lightweight, well-supported libraries
to avoid deployment issues and keep the system stable.
"""

import streamlit as st                  # UI framework
from openai import OpenAI              # LLM API client
import uuid                            # Unique IDs for messages (prevents UI bugs)

# File processing libraries (multimodal ingestion)
from PyPDF2 import PdfReader           # PDF parsing
from docx import Document as DocxDocument   # Word parsing
from pptx import Presentation          # PowerPoint parsing
import pandas as pd                    # CSV / structured data


############################################################
# 2. APPLICATION CONFIGURATION
############################################################
"""
Initializes:
- Page layout
- OpenAI client using secure environment variables

IMPORTANT:
API keys are stored in Streamlit secrets for security.
"""

st.set_page_config(page_title="AI Knowledge Copilot", layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


############################################################
# 3. UI STYLING (LIGHTWEIGHT DESIGN SYSTEM)
############################################################
"""
Applies custom CSS to improve:
- Spacing
- Readability
- Chat message appearance

This mimics a minimal SaaS-style interface.
"""

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
.stChatMessage {
    border-radius: 12px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)


############################################################
# 4. HEADER — APPLICATION TITLE & DESCRIPTION
############################################################
"""
Defines the main entry point of the UI.

Provides users with context on what the application does.
"""

st.title("🧠 AI Knowledge Copilot")
st.markdown("### Analyze documents and interact with your knowledge using AI")


############################################################
# 5. SIDEBAR — WORKSPACE (CONTROL PLANE)
############################################################
"""
The sidebar acts as the CONTROL PLANE of the application.

Responsibilities:
- File ingestion (upload documents)
- User guidance (suggested questions)

UX PATTERN:
Sidebar = Input / Controls
Main Area = Interaction / Output
"""

with st.sidebar:

    st.header("📂 Workspace")

    # Multi-file uploader (supports multiple formats)
    uploaded_files = st.file_uploader(
        "Upload files",
        accept_multiple_files=True,
        type=["pdf", "docx", "pptx", "csv", "txt"]
    )

    st.divider()

    st.subheader("💡 Suggested questions")

    # Session state used to trigger queries programmatically
    if "trigger_question" not in st.session_state:
        st.session_state.trigger_question = None

    def set_question(q):
        """
        Stores a predefined query in session state.
        This allows buttons to simulate user input.
        """
        st.session_state.trigger_question = q

    # Suggested prompts improve usability and discovery
    st.button("Summarize documents", on_click=set_question, args=("Summarize these documents",))
    st.button("Key insights", on_click=set_question, args=("What are the key insights?",))
    st.button("Risks", on_click=set_question, args=("What are the risks?",))
    st.button("Compare documents", on_click=set_question, args=("Compare these documents",))


############################################################
# 6. DOCUMENT PROCESSING (MULTIMODAL INGESTION)
############################################################
"""
This function extracts text from multiple file formats.

CORE IDEA:
Different data types → normalized into plain text

This is critical because LLMs operate on text input.

SUPPORTED FORMATS:
- PDF → page-based extraction
- DOCX → paragraph extraction
- PPTX → slide + shape extraction
- CSV → structured data → string
- TXT → raw text
"""

def extract_text(file):
    text = ""

    # -------- PDF --------
    if file.type == "application/pdf":
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""

    # -------- DOCX --------
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = DocxDocument(file)
        for p in doc.paragraphs:
            text += p.text + "\n"

    # -------- PPTX --------
    elif file.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        prs = Presentation(file)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"

    # -------- CSV --------
    elif file.type == "text/csv":
        df = pd.read_csv(file)
        text += df.to_string()

    # -------- TXT --------
    elif file.type == "text/plain":
        text += file.read().decode("utf-8")

    return text


############################################################
# 7. KNOWLEDGE BASE CONSTRUCTION
############################################################
"""
This step builds a SINGLE CONTEXT STRING from all uploaded documents.

ALGORITHM:
- Iterate through files
- Extract text
- Concatenate into unified context

NOTE:
This is a simplified RAG approach (no embeddings).
"""

all_text = ""

if uploaded_files:
    with st.spinner("📚 Processing documents..."):
        for file in uploaded_files:
            all_text += extract_text(file) + "\n\n"

    st.success(f"{len(uploaded_files)} files processed")


############################################################
# 8. SESSION STATE (CHAT MEMORY)
############################################################
"""
Stores conversation history across reruns.

STRUCTURE:
[
    {
        id: unique identifier,
        role: "user" or "assistant",
        content: message text,
        feedback: optional (for assistant)
    }
]
"""

if "messages" not in st.session_state:
    st.session_state.messages = []


############################################################
# 9. CHAT RENDERING (CONVERSATIONAL UI)
############################################################
"""
Displays chat messages in order.

Includes:
- Chat bubbles
- Feedback system (👍 👎)
- Unique IDs to avoid Streamlit key collisions
"""

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Feedback only for AI responses
        if msg["role"] == "assistant":

            msg_id = msg["id"]
            disabled = msg.get("feedback") is not None

            col1, col2 = st.columns([1, 1])

            with col1:
                if st.button("👍", key=f"up_{msg_id}", disabled=disabled):
                    msg["feedback"] = "up"
                    st.rerun()

            with col2:
                if st.button("👎", key=f"down_{msg_id}", disabled=disabled):
                    msg["feedback"] = "down"
                    st.rerun()

            # Feedback confirmation UI
            if msg.get("feedback") == "up":
                st.success("Marked as helpful")

            elif msg.get("feedback") == "down":
                st.info("Marked as not helpful")


############################################################
# 10. USER INPUT HANDLING
############################################################
"""
Handles two types of input:
1. Manual user input (chat box)
2. Suggested questions (sidebar buttons)

This improves usability and onboarding.
"""

user_input = st.chat_input("Ask about your documents...")

if st.session_state.trigger_question:
    user_input = st.session_state.trigger_question
    st.session_state.trigger_question = None


############################################################
# 11. AI RESPONSE GENERATION (LLM INFERENCE)
############################################################
"""
This is the CORE INTELLIGENCE of the system.

MODEL:
- GPT-4o-mini (OpenAI)

PROCESS:
1. Combine document context + user query
2. Send prompt to LLM
3. Generate grounded response

ALGORITHM:
Prompt-based retrieval (no embeddings)
"""

if user_input and all_text:

    # Store user message
    st.session_state.messages.append({
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("🤖 Thinking..."):

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Answer using ONLY the provided documents."
                    },
                    {
                        "role": "user",
                        "content": f"{all_text[:12000]}\n\nQuestion: {user_input}"
                    }
                ]
            )

            answer = response.choices[0].message.content
            st.markdown(answer)

    # Store assistant message with feedback field
    st.session_state.messages.append({
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": answer,
        "feedback": None
    })

    st.rerun()


############################################################
# 12. EMPTY STATE HANDLING
############################################################
"""
Prevents user errors when no documents are uploaded.
"""

elif user_input and not all_text:
    st.warning("Please upload documents first.")