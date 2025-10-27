from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import time
from PIL import Image
import PyPDF2
from datetime import datetime
import json
import re
import pandas as pd
from io import BytesIO

load_dotenv()

if hasattr(st, 'secrets') and 'GOOGLE_API_KEY' in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ GOOGLE_API_KEY not found!")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

st.set_page_config(
    page_title="GeminiFlow",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@600;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .main, .stApp {
        background: #0a0a0a;
        color: #fff;
    }
    
    .block-container {
        padding: 1rem !important;
        max-width: 1200px !important;
    }
    
    /* Hero */
    .hero {
        text-align: center;
        padding: 1.5rem 1rem;
        margin-bottom: 1rem;
        background: rgba(139, 92, 246, 0.08);
        border-radius: 20px;
        border: 1px solid rgba(139, 92, 246, 0.2);
    }
    
    .hero-logo { font-size: 2.5rem; }
    .hero-title {
        font-size: 2rem;
        font-weight: 900;
        background: linear-gradient(135deg, #fff, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.25rem 0;
    }
    .hero-subtitle {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.85rem;
    }
    
    /* Stats */
    .stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .stat {
        background: rgba(255, 255, 255, 0.04);
        padding: 0.75rem 0.5rem;
        border-radius: 12px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        text-align: center;
    }
    
    .stat-icon { font-size: 1.25rem; }
    .stat-value {
        font-size: 1.5rem;
        font-weight: 900;
        color: #fff;
        margin: 0.25rem 0;
    }
    .stat-label {
        font-size: 0.65rem;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
    }
    
    /* Sidebar Toggle Button - VISIBLE */
    .sidebar-hint {
        background: linear-gradient(135deg, #8b5cf6, #6366f1);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
        cursor: pointer;
        border: 2px solid rgba(139, 92, 246, 0.5);
    }
    
    /* Chat */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 12px !important;
        padding: 0.75rem !important;
        margin: 0.5rem 0 !important;
        border: 1px solid rgba(139, 92, 246, 0.15) !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0a0a0a !important;
        border-right: 1px solid rgba(139, 92, 246, 0.2) !important;
    }
    
    [data-testid="stSidebar"] h3 {
        color: #fff !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        margin: 1rem 0 0.5rem 0 !important;
        padding-bottom: 0.4rem !important;
        border-bottom: 2px solid rgba(139, 92, 246, 0.3) !important;
    }
    
    /* File Upload */
    [data-testid="stFileUploader"] section {
        background: rgba(139, 92, 246, 0.05) !important;
        border: 2px dashed rgba(139, 92, 246, 0.3) !important;
        border-radius: 10px !important;
        padding: 1rem 0.5rem !important;
    }
    
    /* Buttons */
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #8b5cf6, #6366f1) !important;
        color: white !important;
        border: none !important;
        padding: 0.65rem 1rem !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        width: 100% !important;
        font-size: 0.9rem !important;
    }
    
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(139, 92, 246, 0.4) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(139, 92, 246, 0.08) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        font-weight: 600 !important;
        padding: 0.65rem !important;
        font-size: 0.9rem !important;
    }
    
    /* Chat Input */
    .stChatInputContainer {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        border-radius: 12px !important;
    }
    
    /* Success */
    .stSuccess {
        background: rgba(34, 197, 94, 0.1) !important;
        border-left: 3px solid #22c55e !important;
        border-radius: 6px !important;
        padding: 0.5rem !important;
        font-size: 0.85rem !important;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        border-left: 3px solid #3b82f6 !important;
        border-radius: 6px !important;
        padding: 0.5rem !important;
        font-size: 0.85rem !important;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

def extract_pdf_text(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            try:
                text += page.extract_text() + "\n"
            except:
                pass
        return text.strip(), len(pdf_reader.pages)
    except Exception as e:
        return None, 0

def process_image(image_file):
    try:
        img = Image.open(image_file)
        if img.width > 4096 or img.height > 4096:
            img.thumbnail((4096, 4096), Image.Resampling.LANCZOS)
        return img
    except:
        return None

def get_file_size(file):
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0

def export_chat_json():
    data = {
        "session": st.session_state.session_start.isoformat(),
        "messages": st.session_state.messages
    }
    return json.dumps(data, indent=2)

def export_chat_markdown():
    md = f"# GeminiFlow Chat\n\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    for i, msg in enumerate(st.session_state.messages, 1):
        md += f"## Message {i}\n\n**User:** {msg['user']}\n\n**Assistant:** {msg['bot']}\n\n---\n\n"
    return md

def extract_table_from_text(text):
    lines = text.split('\n')
    table_lines = []
    for line in lines:
        if '|' in line and not re.match(r'^\|[\s\-:]+\|', line.strip()):
            table_lines.append(line.strip())
    
    if len(table_lines) < 2:
        return None
    
    try:
        headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
        data = [[c.strip() for c in line.split('|')[1:-1]] for line in table_lines[1:]]
        return pd.DataFrame(data, columns=headers)
    except:
        return None

def create_excel_from_response(text):
    df = extract_table_from_text(text)
    if df is None:
        return None
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)
    output.seek(0)
    return output.getvalue()

def get_gemini_response(question, history, image=None, pdf_text=None):
    try:
        context = ""
        if history:
            for msg in history[-3:]:
                context += f"\nUser: {msg['user']}\nAssistant: {msg['bot'][:150]}...\n"
        if pdf_text:
            context += f"\n\nDocument:\n{pdf_text[:6000]}"
        
        prompt = f"Use markdown tables. Show step-by-step.\n\n{context}\n\nUser: {question}\nAssistant:"
        
        config = {"temperature": st.session_state.temperature, "max_output_tokens": st.session_state.max_tokens}
        
        if image:
            response = model.generate_content([prompt, image], generation_config=config)
        else:
            response = model.generate_content(prompt, generation_config=config)
        
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "uploaded_pdf" not in st.session_state:
    st.session_state.uploaded_pdf = None
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = None
if "session_start" not in st.session_state:
    st.session_state.session_start = datetime.now()
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 2048

# Hero
st.markdown("""
<div class="hero">
    <div class="hero-logo">✨</div>
    <h1 class="hero-title">GeminiFlow</h1>
    <p class="hero-subtitle">Excel Export • Image Analysis • PDF Processing</p>
</div>
""", unsafe_allow_html=True)

# MOBILE: Sidebar hint with instructions
st.markdown("""
<div class="sidebar-hint">
    👈 <strong>Tap the arrow (>) in top-left</strong> to upload files, adjust settings & export chat!
</div>
""", unsafe_allow_html=True)

# Stats
st.markdown(f"""
<div class="stats">
    <div class="stat">
        <div class="stat-icon">💬</div>
        <div class="stat-value">{len(st.session_state.messages)}</div>
        <div class="stat-label">Messages</div>
    </div>
    <div class="stat">
        <div class="stat-icon">🖼️</div>
        <div class="stat-value">{'1' if st.session_state.uploaded_image else '0'}</div>
        <div class="stat-label">Images</div>
    </div>
    <div class="stat">
        <div class="stat-icon">📄</div>
        <div class="stat-value">{'1' if st.session_state.uploaded_pdf else '0'}</div>
        <div class="stat-label">Documents</div>
    </div>
</div>
""", unsafe_allow_html=True)

# SIDEBAR - Where all controls live
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    with st.expander("🎛️ Model Config", expanded=False):
        st.session_state.temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1, 
                                                 help="Higher = more creative, Lower = more focused")
        st.session_state.max_tokens = st.slider("Max Tokens", 256, 8192, 2048, 256,
                                                help="Maximum response length")
    
    st.markdown("### 📤 Upload Files")
    
    # IMAGE
    uploaded_image = st.file_uploader("📸 Upload Image", type=['png', 'jpg', 'jpeg', 'webp'], 
                                     key="img", label_visibility="visible")
    if uploaded_image:
        st.session_state.uploaded_image = uploaded_image
        st.success(f"✅ {uploaded_image.name}")
        st.caption(f"Size: {get_file_size(uploaded_image)}")
        img = process_image(uploaded_image)
        if img:
            st.image(img, use_container_width=True)
        if st.button("🗑️ Remove Image", use_container_width=True, key="rm_img"):
            st.session_state.uploaded_image = None
            st.rerun()
    
    # PDF
    uploaded_pdf = st.file_uploader("📄 Upload PDF", type=['pdf'], 
                                   key="pdf", label_visibility="visible")
    if uploaded_pdf:
        st.session_state.uploaded_pdf = uploaded_pdf
        st.success(f"✅ {uploaded_pdf.name}")
        st.caption(f"Size: {get_file_size(uploaded_pdf)}")
        if st.session_state.pdf_text is None:
            with st.spinner("📖 Reading PDF..."):
                text, pages = extract_pdf_text(uploaded_pdf)
                if text:
                    st.session_state.pdf_text = text
                    words = len(text.split())
                    st.info(f"📑 {pages} pages • {words:,} words")
        else:
            words = len(st.session_state.pdf_text.split())
            st.info(f"📑 {words:,} words loaded")
        if st.button("🗑️ Remove PDF", use_container_width=True, key="rm_pdf"):
            st.session_state.uploaded_pdf = None
            st.session_state.pdf_text = None
            st.rerun()
    
    st.markdown("### ⚡ Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear Chat", use_container_width=True, help="Clear all messages"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 Reset All", use_container_width=True, help="Reset everything"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # EXPORT
    if st.session_state.messages:
        st.markdown("### 📥 Export Chat")
        
        st.download_button(
            "💬 Download Markdown (.md)",
            data=export_chat_markdown(),
            file_name=f"geminiflow_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
            help="Download chat as Markdown file"
        )
        
        st.download_button(
            "📊 Download JSON",
            data=export_chat_json(),
            file_name=f"geminiflow_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
            help="Download chat as JSON file"
        )

# Chat Display
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="✨"):
        st.markdown("""
        **👋 Welcome!**
        
        I can help you with:
        - 📊 Excel exports from tables
        - 🖼️ Image analysis
        - 📄 PDF processing
        - 🔢 Math solutions
        
        **Get Started:**
        1. Tap **>** in top-left to open sidebar
        2. Upload your files (image/PDF)
        3. Ask me anything!
        """)

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message("user", avatar="👤"):
        st.markdown(msg["user"])
    
    with st.chat_message("assistant", avatar="✨"):
        st.markdown(msg["bot"])
        
        if '|' in msg["bot"] and '-|-' in msg["bot"]:
            excel = create_excel_from_response(msg["bot"])
            if excel:
                st.download_button(
                    "📥 Download Excel",
                    data=excel,
                    file_name=f"table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"xl_{i}",
                    use_container_width=True
                )

# Chat Input
if prompt := st.chat_input("💭 Ask me anything..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    img_data = None
    if st.session_state.uploaded_image:
        img_data = process_image(st.session_state.uploaded_image)
    
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("✨ Thinking..."):
            response = get_gemini_response(prompt, st.session_state.messages, 
                                         image=img_data, pdf_text=st.session_state.pdf_text)
        st.markdown(response)
        
        if '|' in response and '-|-' in response:
            excel = create_excel_from_response(response)
            if excel:
                st.download_button(
                    "📥 Download Excel",
                    data=excel,
                    file_name=f"table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="xl_new",
                    use_container_width=True
                )
    
    st.session_state.messages.append({
        "user": prompt,
        "bot": response,
        "timestamp": datetime.now().isoformat()
    })
    st.rerun()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; padding: 0.75rem; color: rgba(255,255,255,0.4); font-size: 0.8rem;'>
    <strong>GeminiFlow</strong> • Powered by Gemini 2.0 • Created by Brijesh Singh
</div>
""", unsafe_allow_html=True)