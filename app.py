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

# Page config - SIDEBAR NOW EXPANDED BY DEFAULT
st.set_page_config(
    page_title="GeminiFlow",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"  # FIXED: Changed from collapsed
)

# CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: #000000;
        color: #ffffff;
    }
    
    .stApp {
        background: #000000;
    }
    
    .block-container {
        padding: 2rem 1rem !important;
        max-width: 1400px !important;
    }
    
    /* MOBILE OPTIMIZATION */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.5rem !important;
        }
        
        /* Make sidebar button more visible */
        [data-testid="collapsedControl"] {
            background: rgba(139, 92, 246, 0.3) !important;
            border: 2px solid rgba(139, 92, 246, 0.6) !important;
            width: 50px !important;
            height: 50px !important;
            border-radius: 12px !important;
        }
    }
    
    .hero-section {
        text-align: center;
        padding: 2rem 1rem;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(59, 130, 246, 0.1));
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .brand-name {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #fff, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    @media (max-width: 768px) {
        .brand-name {
            font-size: 1.75rem;
        }
    }
    
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    @media (max-width: 768px) {
        .stat-grid {
            grid-template-columns: 1fr;
        }
    }
    
    .stat-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 1.25rem;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s;
    }
    
    .stat-card:hover {
        transform: translateY(-4px);
        border-color: rgba(139, 92, 246, 0.4);
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 900;
        color: #fff;
    }
    
    .stat-label {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Mobile hint box */
    .mobile-hint {
        background: rgba(139, 92, 246, 0.15);
        border: 2px solid rgba(139, 92, 246, 0.4);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: 600;
    }
    
    @media (min-width: 769px) {
        .mobile-hint {
            display: none;
        }
    }
    
    .stChatMessage {
        background: rgba(255, 255, 255, 0.02) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #8b5cf6, #6366f1);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: 700;
        transition: all 0.3s;
        width: 100%;
        min-height: 44px;
    }
    
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(139, 92, 246, 0.4);
    }
    
    [data-testid="stSidebar"] {
        background: #000000 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #fff;
        margin-bottom: 0.75rem;
    }
    
    /* File uploader styling */
    [data-testid="stFileUploader"] section {
        background: rgba(255, 255, 255, 0.03);
        border: 2px dashed rgba(139, 92, 246, 0.4);
        border-radius: 12px;
        padding: 1.5rem 1rem;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(139, 92, 246, 0.7);
        background: rgba(139, 92, 246, 0.05);
    }
    
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        font-weight: 600;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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

# Hero
st.markdown("""
<div class="hero-section">
    <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">✨</div>
    <div class="brand-name">GeminiFlow</div>
    <p style="color: rgba(255,255,255,0.6); margin-top: 0.5rem;">Excel Export • Image Analysis • PDF Processing</p>
</div>
""", unsafe_allow_html=True)

# MOBILE HINT - CRITICAL FIX
st.markdown("""
<div class="mobile-hint">
    📱 <strong>Mobile Users:</strong> Tap the <strong>></strong> button in top-left corner to upload files & access settings! 👈
</div>
""", unsafe_allow_html=True)

# Stats
st.markdown(f"""
<div class="stat-grid">
    <div class="stat-card">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">💬</div>
        <div class="stat-value">{len(st.session_state.messages)}</div>
        <div class="stat-label">Messages</div>
    </div>
    <div class="stat-card">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🖼️</div>
        <div class="stat-value">{'1' if st.session_state.uploaded_image else '0'}</div>
        <div class="stat-label">Images</div>
    </div>
    <div class="stat-card">
        <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📄</div>
        <div class="stat-value">{'1' if st.session_state.uploaded_pdf else '0'}</div>
        <div class="stat-label">Documents</div>
    </div>
</div>
""", unsafe_allow_html=True)

# SIDEBAR - Now visible by default
with st.sidebar:
    st.markdown('<div class="section-title">⚙️ Controls</div>', unsafe_allow_html=True)
    
    with st.expander("🎛️ Model Settings"):
        st.session_state.temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        st.session_state.max_tokens = st.slider("Max Tokens", 256, 8192, 2048, 256)
    
    st.markdown('<div class="section-title">📁 Upload Files</div>', unsafe_allow_html=True)
    
    # IMAGE UPLOAD
    uploaded_image = st.file_uploader("📸 Upload Image", type=['png', 'jpg', 'jpeg', 'webp'])
    if uploaded_image:
        st.session_state.uploaded_image = uploaded_image
        st.success(f"✅ {uploaded_image.name}")
        st.caption(f"📦 {get_file_size(uploaded_image)}")
        img = process_image(uploaded_image)
        if img:
            st.image(img, use_container_width=True)
        if st.button("🗑️ Remove Image", use_container_width=True):
            st.session_state.uploaded_image = None
            st.rerun()
    
    # PDF UPLOAD
    uploaded_pdf = st.file_uploader("📄 Upload PDF", type=['pdf'])
    if uploaded_pdf:
        st.session_state.uploaded_pdf = uploaded_pdf
        st.success(f"✅ {uploaded_pdf.name}")
        st.caption(f"📦 {get_file_size(uploaded_pdf)}")
        if st.session_state.pdf_text is None:
            with st.spinner("Reading PDF..."):
                text, pages = extract_pdf_text(uploaded_pdf)
                if text:
                    st.session_state.pdf_text = text
                    st.info(f"📑 {pages} pages extracted")
        if st.button("🗑️ Remove PDF", use_container_width=True):
            st.session_state.uploaded_pdf = None
            st.session_state.pdf_text = None
            st.rerun()
    
    st.markdown('<div class="section-title">⚡ Actions</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 Reset All", use_container_width=True):
            st.session_state.messages = []
            st.session_state.uploaded_image = None
            st.session_state.uploaded_pdf = None
            st.session_state.pdf_text = None
            st.rerun()
    
    # EXPORT OPTIONS
    if st.session_state.messages:
        st.markdown('<div class="section-title">📥 Export Chat</div>', unsafe_allow_html=True)
        
        st.download_button(
            "💬 Download Markdown",
            data=export_chat_markdown(),
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
        
        st.download_button(
            "📊 Download JSON",
            data=export_chat_json(),
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

# Chat Display
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="✨"):
            st.markdown("""
            ### 👋 Welcome to GeminiFlow!
            
            **Features:**
            - 📊 Excel auto-export from tables
            - 🖼️ Image analysis
            - 📄 PDF processing
            - 🔢 Step-by-step math solutions
            
            **Get Started:**
            1. Upload files via sidebar (tap **>** icon on mobile)
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
                        file_name=f"table_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"excel_{i}",
                        use_container_width=True
                    )

# Chat Input
if prompt := st.chat_input("💭 Message GeminiFlow..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    image_data = None
    if st.session_state.uploaded_image:
        image_data = process_image(st.session_state.uploaded_image)
    
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("🤔 Thinking..."):
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
<div style='text-align: center; padding: 1rem; color: rgba(255,255,255,0.5);'>
    GeminiFlow • Powered by Gemini 2.0 • Created by Brijesh Singh
</div>
""", unsafe_allow_html=True)