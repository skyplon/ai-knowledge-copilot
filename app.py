############################################################
# 🧠 AI KNOWLEDGE COPILOT — V1 (POLISHED UX VERSION)
############################################################
# DESCRIPTION:
# This app allows users to upload documents and interact with them
# using an AI-powered chat interface.
#
# FEATURES:
# - Upload multiple documents (PDF, DOCX, PPTX, CSV, TXT)
# - Ask questions about your documents
# - Suggested questions (with loading feedback)
# - Clean ChatGPT-style interface
#
# NOTE:
# This version avoids LangChain for stability in deployment.
############################################################


############################################################
# 1. IMPORT LIBRARIES
############################################################
import streamlit as st
from openai import OpenAI
import tempfile
import os

from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from pptx import Presentation
import pandas as pd


############################################################
# 2. INITIALIZE APP + OPENAI CLIENT
############################################################
st.set_page_config(page_title="AI Knowledge Copilot", layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


############################################################
# 3. CUSTOM UI STYLING (PRO LOOK)
############################################################
st.markdown("""
<style>
.main {
    background-color: #f8fafc;
}
.block-container {
    padding-top: 2rem;
}
h1 {
    font-size: 2.5rem !important;
}
.stChatMessage {
    border-radius: 12px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)


############################################################
# 4. TITLE & APP DESCRIPTION
############################################################
st.title("🧠 AI Knowledge Copilot")
st.markdown("### Analyze documents and interact with your knowledge using AI")

st.info("Upload documents on the left sidebar to start chatting with your data.")


############################################################
# 5. SIDEBAR (WORKSPACE + SUGGESTED QUESTIONS)
############################################################
with st.sidebar:

    st.header("📂 Workspace")
    st.markdown("Upload and manage your knowledge sources.")

    uploaded_files = st.file_uploader(
        "Upload files",
        accept_multiple_files=True,
        type=["pdf", "docx", "pptx", "csv", "txt"]
    )

    st.divider()

    st.subheader("💡 Suggested questions")

    if "trigger_question" not in st.session_state:
        st.session_state.trigger_question = None

    def trigger(q):
        st.session_state.trigger_question = q

    st.button("Summarize these documents", on_click=trigger, args=("Summarize these documents",))
    st.button("What are the key insights?", on_click=trigger, args=("What are the key insights?",))
    st.button("What are the risks?", on_click=trigger, args=("What are the risks?",))
    st.button("Compare these documents", on_click=trigger, args=("Compare these documents",))


############################################################
# 6. DOCUMENT PROCESSING (MULTI-FORMAT SUPPORT)
############################################################
def extract_text(file):
    text = ""

    if file.type == "application/pdf":
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""

    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = DocxDocument(file)
        for para in doc.paragraphs:
            text += para.text + "\n"

    elif file.type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
        prs = Presentation(file)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"

    elif file.type == "text/csv":
        df = pd.read_csv(file)
        text += df.to_string()

    elif file.type == "text/plain":
        text += file.read().decode("utf-8")

    return text


############################################################
# 7. BUILD KNOWLEDGE BASE
############################################################
all_text = ""

if uploaded_files:
    with st.spinner("📚 Processing documents..."):
        for file in uploaded_files:
            all_text += extract_text(file) + "\n\n"

    st.success(f"✅ {len(uploaded_files)} files processed successfully")


############################################################
# 8. CHAT MEMORY INITIALIZATION
############################################################
if "messages" not in st.session_state:
    st.session_state.messages = []

if "feedback" not in st.session_state:
    st.session_state.feedback = []

############################################################
# 9. DISPLAY CHAT HISTORY
############################################################
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # 👉 Only show feedback for assistant messages
        if msg["role"] == "assistant":

            col1, col2 = st.columns([1, 1])

            with col1:
                if st.button("👍", key=f"up_{i}"):
                    st.session_state.feedback.append({
                        "message_id": i,
                        "feedback": "up"
                    })
                    st.success("Thanks for your feedback!")

            with col2:
                if st.button("👎", key=f"down_{i}"):
                    st.session_state.feedback.append({
                        "message_id": i,
                        "feedback": "down"
                    })
                    st.info("Feedback noted. We'll improve!")

    with st.expander("📊 Feedback log (demo purposes)"):
        st.write(st.session_state.feedback)

############################################################
# 10. HANDLE USER INPUT (CHAT + SUGGESTED QUESTIONS)
############################################################
user_input = st.chat_input("Ask anything about your documents...")

# PRIORITY: Suggested question triggers
if st.session_state.trigger_question:
    user_input = st.session_state.trigger_question
    st.session_state.trigger_question = None


############################################################
# 11. PROCESS QUERY + SHOW LOADING FEEDBACK
############################################################
if user_input and all_text:

    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 🔥 LOADING FEEDBACK (THIS IS YOUR REQUEST)
    with st.chat_message("assistant"):
        with st.spinner("🤖 Thinking... analyzing your documents..."):

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI assistant helping analyze documents."
                    },
                    {
                        "role": "user",
                        "content": f"""
                        Use the following documents to answer the question.

                        DOCUMENTS:
                        {all_text[:12000]}

                        QUESTION:
                        {user_input}
                        """
                    }
                ]
            )

            answer = response.choices[0].message.content

            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})


############################################################
# 12. EMPTY STATE (NO FILES)
############################################################
elif user_input and not all_text:
    st.warning("⚠️ Please upload documents first.")


############################################################
# END OF APP
############################################################