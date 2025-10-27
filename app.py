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

# Load environment variables
load_dotenv()

# Get API key
if hasattr(st, 'secrets') and 'GOOGLE_API_KEY' in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ GOOGLE_API_KEY not found! Add it to .env file or Streamlit secrets")
    st.info("Get your key from: https://makersuite.google.com/app/apikey")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Page config
st.set_page_config(
    page_title="GeminiFlow",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Dark Theme */
    .main, .stApp {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 100%);
        color: #ffffff;
    }
    
    .block-container {
        padding: 2rem 1.5rem !important;
        max-width: 1200px !important;
    }
    
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem !important;
        }
    }
    
    /* Hero Section */
    .hero-section {
        text-align: center;
        padding: 3rem 1.5rem;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
        border-radius: 24px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    @media (max-width: 768px) {
        .hero-section {
            padding: 2rem 1rem;
            border-radius: 20px;
        }
    }
    
    .hero-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%);
        animation: rotate 20s linear infinite;
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .logo {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        position: relative;
        z-index: 1;
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    @media (max-width: 768px) {
        .logo {
            font-size: 2.5rem;
        }
    }
    
    .brand-name {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #ffffff 0%, #8b5cf6 50%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        position: relative;
        z-index: 1;
    }
    
    @media (max-width: 768px) {
        .brand-name {
            font-size: 2rem;
        }
    }
    
    .tagline {
        color: rgba(255, 255, 255, 0.7);
        font-size: 1.1rem;
        margin-top: 1rem;
        font-weight: 500;
        position: relative;
        z-index: 1;
    }
    
    @media (max-width: 768px) {
        .tagline {
            font-size: 0.9rem;
        }
    }
    
    /* Stats Grid */
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    
    @media (max-width: 768px) {
        .stat-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
    }
    
    .stat-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        padding: 1.5rem;
        border-radius: 20px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        position: relative;
        overflow: hidden;
    }
    
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.1), transparent);
        transition: left 0.6s;
    }
    
    .stat-card:hover {
        transform: translateY(-8px);
        border-color: rgba(139, 92, 246, 0.5);
        box-shadow: 0 20px 60px rgba(139, 92, 246, 0.3);
    }
    
    .stat-card:hover::before {
        left: 100%;
    }
    
    .stat-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 900;
        color: #ffffff;
        line-height: 1;
        margin: 0.5rem 0;
    }
    
    @media (max-width: 768px) {
        .stat-value {
            font-size: 2rem;
        }
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.6);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Chat Messages */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.04) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        border: 1px solid rgba(139, 92, 246, 0.15) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    @media (max-width: 768px) {
        .stChatMessage {
            padding: 1rem !important;
        }
    }
    
    [data-testid="stChatMessageContent"] {
        color: rgba(255, 255, 255, 0.95) !important;
        font-size: 1rem !important;
        line-height: 1.7 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 100%) !important;
        border-right: 1px solid rgba(139, 92, 246, 0.2) !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #ffffff !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid rgba(139, 92, 246, 0.3) !important;
    }
    
    /* File Uploaders */
    [data-testid="stFileUploader"] {
        background: transparent !important;
    }
    
    [data-testid="stFileUploader"] section {
        background: rgba(139, 92, 246, 0.05) !important;
        border: 2px dashed rgba(139, 92, 246, 0.4) !important;
        border-radius: 16px !important;
        padding: 2rem 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(139, 92, 246, 0.7) !important;
        background: rgba(139, 92, 246, 0.1) !important;
    }
    
    [data-testid="stFileUploader"] label {
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 600 !important;
    }
    
    /* Buttons */
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.875rem 1.5rem !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        box-shadow: 0 8px 24px rgba(139, 92, 246, 0.3) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stButton > button::before, .stDownloadButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 12px 40px rgba(139, 92, 246, 0.5) !important;
    }
    
    .stButton > button:hover::before, .stDownloadButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton > button:active, .stDownloadButton > button:active {
        transform: translateY(-1px) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(139, 92, 246, 0.08) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        font-weight: 600 !important;
        color: rgba(255, 255, 255, 0.95) !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(139, 92, 246, 0.15) !important;
        border-color: rgba(139, 92, 246, 0.4) !important;
    }
    
    /* Chat Input */
    .stChatInputContainer {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stChatInputContainer:focus-within {
        border-color: rgba(139, 92, 246, 0.6) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2) !important;
    }
    
    /* Sliders */
    .stSlider [data-baseweb="slider"] {
        background: linear-gradient(90deg, #8b5cf6 0%, #6366f1 100%) !important;
    }
    
    /* Success/Info Messages */
    .stSuccess {
        background: rgba(34, 197, 94, 0.1) !important;
        border-left: 4px solid #22c55e !important;
        border-radius: 12px !important;
        color: #fff !important;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        border-left: 4px solid #3b82f6 !important;
        border-radius: 12px !important;
        color: #fff !important;
    }
    
    /* Hide defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Better scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(139, 92, 246, 0.5);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(139, 92, 246, 0.7);
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def extract_pdf_text(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        pages = len(pdf_reader.pages)
        
        for i, page in enumerate(pdf_reader.pages):
            try:
                text += page.extract_text() + "\n"
            except:
                pass
        
        return text.strip(), pages
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None, 0

def process_image(image_file):
    try:
        img = Image.open(image_file)
        max_size = 4096
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def get_file_size(file):
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def export_chat_json():
    export_data = {
        "session_start": st.session_state.session_start.isoformat(),
        "export_time": datetime.now().isoformat(),
        "message_count": len(st.session_state.messages),
        "messages": st.session_state.messages
    }
    return json.dumps(export_data, indent=2)

def export_chat_markdown():
    markdown = f"# GeminiFlow Chat Session\n\n"
    markdown += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    markdown += f"**Messages:** {len(st.session_state.messages)}\n\n---\n\n"
    for i, msg in enumerate(st.session_state.messages, 1):
        markdown += f"## Message {i}\n\n**User:** {msg['user']}\n\n"
        markdown += f"**Assistant:** {msg['bot']}\n\n---\n\n"
    return markdown

def extract_table_from_text(text):
    lines = text.split('\n')
    table_lines = []
    in_table = False
    
    for line in lines:
        if '|' in line:
            in_table = True
            cleaned = line.strip()
            if cleaned and not re.match(r'^\|[\s\-:]+\|', cleaned):
                table_lines.append(cleaned)
        elif in_table and line.strip() == '':
            break
    
    if not table_lines:
        return None
    
    try:
        headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
        data = []
        for line in table_lines[1:]:
            if line.strip():
                row = [cell.strip() for cell in line.split('|')[1:-1]]
                data.append(row)
        
        if data:
            return pd.DataFrame(data, columns=headers)
    except:
        return None
    return None

def create_excel_from_response(response_text):
    df = extract_table_from_text(response_text)
    if df is None:
        return None
    
    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
        output.seek(0)
        return output.getvalue()
    except:
        return None

def get_gemini_response(question, history, image=None, pdf_text=None):
    try:
        context = ""
        
        if history:
            context += "=== Previous Conversation ===\n"
            for msg in history[-5:]:
                context += f"\nUser: {msg['user']}\n"
                context += f"Assistant: {msg['bot'][:200]}...\n" if len(msg['bot']) > 200 else f"Assistant: {msg['bot']}\n"
        
        if pdf_text:
            context += f"\n\n=== Document Content ===\n{pdf_text[:8000]}"
        
        formatting = """
FORMATTING INSTRUCTIONS:
- Use markdown tables with | separators for data
- Show calculations step-by-step
- Format for Excel export compatibility
"""
        
        full_prompt = f"{formatting}\n\n{context}\n\nUser: {question}\nAssistant:"
        
        config = {
            "temperature": st.session_state.temperature,
            "max_output_tokens": st.session_state.max_tokens,
        }
        
        if image:
            response = model.generate_content([full_prompt, image], generation_config=config)
        else:
            response = model.generate_content(full_prompt, generation_config=config)
        
        return response.text
    
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Initialize session state
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

# Hero Section - CLEAN & MODERN
st.markdown("""
<div class="hero-section">
    <div class="logo">✨</div>
    <div class="brand-name">GeminiFlow</div>
    <div class="tagline">Excel Export • Image Analysis • PDF Processing</div>
</div>
""", unsafe_allow_html=True)

# Stats Grid - CLEAN DESIGN
st.markdown(f"""
<div class="stat-grid">
    <div class="stat-card">
        <span class="stat-icon">💬</span>
        <div class="stat-value">{len(st.session_state.messages)}</div>
        <div class="stat-label">Messages</div>
    </div>
    <div class="stat-card">
        <span class="stat-icon">🖼️</span>
        <div class="stat-value">{'1' if st.session_state.uploaded_image else '0'}</div>
        <div class="stat-label">Images</div>
    </div>
    <div class="stat-card">
        <span class="stat-icon">📄</span>
        <div class="stat-value">{'1' if st.session_state.uploaded_pdf else '0'}</div>
        <div class="stat-label">Documents</div>
    </div>
</div>
""", unsafe_allow_html=True)

# SIDEBAR - IMPROVED DESIGN
with st.sidebar:
    st.markdown("### ⚙️ Controls")
    
    with st.expander("🎛️ Model Settings"):
        st.session_state.temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        st.session_state.max_tokens = st.slider("Max Tokens", 256, 8192, 2048, 256)
    
    st.markdown("### 📁 Upload Files")
    
    # IMAGE UPLOAD
    uploaded_image = st.file_uploader("📸 Upload Image", type=['png', 'jpg', 'jpeg', 'webp'], key="img_upload")
    if uploaded_image:
        st.session_state.uploaded_image = uploaded_image
        st.success(f"✅ {uploaded_image.name}")
        st.caption(f"Size: {get_file_size(uploaded_image)}")
        img = process_image(uploaded_image)
        if img:
            st.image(img, use_container_width=True)
        if st.button("🗑️ Remove Image", use_container_width=True):
            st.session_state.uploaded_image = None
            st.rerun()
    
    # PDF UPLOAD
    uploaded_pdf = st.file_uploader("📄 Upload PDF", type=['pdf'], key="pdf_upload")
    if uploaded_pdf:
        st.session_state.uploaded_pdf = uploaded_pdf
        st.success(f"✅ {uploaded_pdf.name}")
        st.caption(f"Size: {get_file_size(uploaded_pdf)}")
        if st.session_state.pdf_text is None:
            with st.spinner("📖 Reading PDF..."):
                text, pages = extract_pdf_text(uploaded_pdf)
                if text:
                    st.session_state.pdf_text = text
                    st.info(f"📑 {pages} pages • {len(text.split())} words")
        if st.button("🗑️ Remove PDF", use_container_width=True):
            st.session_state.uploaded_pdf = None
            st.session_state.pdf_text = None
            st.rerun()
    
    st.markdown("### ⚡ Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # EXPORT
    if st.session_state.messages:
        st.markdown("### 📥 Export")
        
        st.download_button(
            "💬 Markdown",
            data=export_chat_markdown(),
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
        
        st.download_button(
            "📊 JSON",
            data=export_chat_json(),
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

# Chat Display
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="✨"):
        st.markdown("""
        ### 👋 Welcome to GeminiFlow!
        
        **What I can do:**
        - 📊 **Excel Export** - Convert tables to spreadsheets
        - 🖼️ **Image Analysis** - Understand and extract from images
        - 📄 **PDF Processing** - Analyze documents
        - 🔢 **Math Solutions** - Step-by-step calculations
        
        **Get Started:**
        1. Upload files via sidebar
        2. Ask your question
        3. Download Excel if response has tables
        """)

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message("user", avatar="👤"):
        st.markdown(msg["user"])
    
    with st.chat_message("assistant", avatar="✨"):
        st.markdown(msg["bot"])
        
        # Excel export
        if '|' in msg["bot"] and '-|-' in msg["bot"]:
            excel_data = create_excel_from_response(msg["bot"])
            if excel_data:
                st.download_button(
                    "📥 Download Excel",
                    data=excel_data,
                    file_name=f"table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"excel_{i}",
                    use_container_width=True
                )

# Chat Input
if prompt := st.chat_input("💭 Ask me anything..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    image_data = None
    if st.session_state.uploaded_image:
        image_data = process_image(st.session_state.uploaded_image)
    
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("✨ Thinking..."):
            response = get_gemini_response(
                prompt,
                st.session_state.messages,
                image=image_data,
                pdf_text=st.session_state.pdf_text
            )
        
        st.markdown(response)
        
        # Excel export
        if '|' in response and '-|-' in response:
            excel_data = create_excel_from_response(response)
            if excel_data:
                st.download_button(
                    "📥 Download Excel",
                    data=excel_data,
                    file_name=f"table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="excel_current",
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
<div style='text-align: center; padding: 1.5rem; color: rgba(255,255,255,0.5); font-size: 0.9rem;'>
    <strong>GeminiFlow</strong> • Powered by Gemini 2.0 Flash • Created by Brijesh Singh
</div>
""", unsafe_allow_html=True)