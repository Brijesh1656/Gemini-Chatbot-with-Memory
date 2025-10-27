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

# Streamlined CSS - Much cleaner
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Dark Theme */
    .main, .stApp {
        background: #0a0a0a;
        color: #ffffff;
    }
    
    .block-container {
        padding: 1.5rem 1rem !important;
        max-width: 1200px !important;
    }
    
    /* Hero - Simple & Clean */
    .hero {
        text-align: center;
        padding: 2rem 1rem;
        margin-bottom: 1.5rem;
        background: rgba(139, 92, 246, 0.08);
        border-radius: 20px;
        border: 1px solid rgba(139, 92, 246, 0.2);
    }
    
    .hero-logo {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    .hero-title {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #fff, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .hero-subtitle {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.95rem;
        margin-top: 0.5rem;
    }
    
    @media (max-width: 768px) {
        .hero {
            padding: 1.5rem 0.75rem;
        }
        .hero-logo {
            font-size: 2rem;
        }
        .hero-title {
            font-size: 1.75rem;
        }
        .hero-subtitle {
            font-size: 0.85rem;
        }
    }
    
    /* Stats - Compact on Mobile */
    .stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.75rem;
        margin-bottom: 1.5rem;
    }
    
    @media (max-width: 768px) {
        .stats {
            gap: 0.5rem;
        }
    }
    
    .stat {
        background: rgba(255, 255, 255, 0.04);
        padding: 1rem;
        border-radius: 16px;
        border: 1px solid rgba(139, 92, 246, 0.2);
        text-align: center;
        transition: all 0.3s;
    }
    
    .stat:hover {
        border-color: rgba(139, 92, 246, 0.5);
        transform: translateY(-2px);
    }
    
    @media (max-width: 768px) {
        .stat {
            padding: 0.75rem 0.5rem;
        }
    }
    
    .stat-icon {
        font-size: 1.5rem;
        display: block;
        margin-bottom: 0.25rem;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 900;
        color: #fff;
        line-height: 1;
    }
    
    .stat-label {
        font-size: 0.7rem;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }
    
    @media (max-width: 768px) {
        .stat-icon {
            font-size: 1.25rem;
        }
        .stat-value {
            font-size: 1.5rem;
        }
        .stat-label {
            font-size: 0.65rem;
        }
    }
    
    /* Chat Messages */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 0.75rem 0 !important;
        border: 1px solid rgba(139, 92, 246, 0.15) !important;
    }
    
    @media (max-width: 768px) {
        .stChatMessage {
            padding: 0.75rem !important;
            margin: 0.5rem 0 !important;
        }
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0a0a0a !important;
        border-right: 1px solid rgba(139, 92, 246, 0.2) !important;
    }
    
    [data-testid="stSidebar"] h3 {
        color: #fff !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        margin: 1.5rem 0 0.75rem 0 !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid rgba(139, 92, 246, 0.3) !important;
    }
    
    /* File Uploaders - Cleaner */
    [data-testid="stFileUploader"] section {
        background: rgba(139, 92, 246, 0.05) !important;
        border: 2px dashed rgba(139, 92, 246, 0.3) !important;
        border-radius: 12px !important;
        padding: 1.25rem 0.75rem !important;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(139, 92, 246, 0.6) !important;
        background: rgba(139, 92, 246, 0.08) !important;
    }
    
    /* Buttons */
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #8b5cf6, #6366f1) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 1.25rem !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        width: 100% !important;
        transition: all 0.3s !important;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3) !important;
    }
    
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4) !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(139, 92, 246, 0.08) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        font-weight: 600 !important;
        padding: 0.75rem !important;
    }
    
    /* Chat Input */
    .stChatInputContainer {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(139, 92, 246, 0.3) !important;
        border-radius: 12px !important;
    }
    
    .stChatInputContainer:focus-within {
        border-color: rgba(139, 92, 246, 0.6) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1) !important;
    }
    
    /* Hide defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Success/Info */
    .stSuccess {
        background: rgba(34, 197, 94, 0.1) !important;
        border-left: 3px solid #22c55e !important;
        border-radius: 8px !important;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        border-left: 3px solid #3b82f6 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
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
    markdown = f"# GeminiFlow Chat\n\n"
    markdown += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    for i, msg in enumerate(st.session_state.messages, 1):
        markdown += f"## Message {i}\n\n**User:** {msg['user']}\n\n**Assistant:** {msg['bot']}\n\n---\n\n"
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
                context += f"\nUser: {msg['user']}\nAssistant: {msg['bot'][:200]}...\n"
        
        if pdf_text:
            context += f"\n\n=== Document ===\n{pdf_text[:8000]}"
        
        prompt = f"Use markdown tables for data. Show calculations step-by-step.\n\n{context}\n\nUser: {question}\nAssistant:"
        
        config = {
            "temperature": st.session_state.temperature,
            "max_output_tokens": st.session_state.max_tokens,
        }
        
        if image:
            response = model.generate_content([prompt, image], generation_config=config)
        else:
            response = model.generate_content(prompt, generation_config=config)
        
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

# Hero - Clean & Simple
st.markdown("""
<div class="hero">
    <div class="hero-logo">✨</div>
    <h1 class="hero-title">GeminiFlow</h1>
    <p class="hero-subtitle">Excel Export • Image Analysis • PDF Processing</p>
</div>
""", unsafe_allow_html=True)

# Stats - Clean Grid
st.markdown(f"""
<div class="stats">
    <div class="stat">
        <span class="stat-icon">💬</span>
        <div class="stat-value">{len(st.session_state.messages)}</div>
        <div class="stat-label">Messages</div>
    </div>
    <div class="stat">
        <span class="stat-icon">🖼️</span>
        <div class="stat-value">{'1' if st.session_state.uploaded_image else '0'}</div>
        <div class="stat-label">Images</div>
    </div>
    <div class="stat">
        <span class="stat-icon">📄</span>
        <div class="stat-value">{'1' if st.session_state.uploaded_pdf else '0'}</div>
        <div class="stat-label">Documents</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar - Clean & Organized
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    with st.expander("🎛️ Model Config"):
        st.session_state.temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        st.session_state.max_tokens = st.slider("Max Tokens", 256, 8192, 2048, 256)
    
    st.markdown("### 📤 Upload")
    
    uploaded_image = st.file_uploader("📸 Image", type=['png', 'jpg', 'jpeg', 'webp'])
    if uploaded_image:
        st.session_state.uploaded_image = uploaded_image
        st.success(f"✅ {uploaded_image.name}")
        img = process_image(uploaded_image)
        if img:
            st.image(img, use_container_width=True)
        if st.button("🗑️ Remove", key="rm_img"):
            st.session_state.uploaded_image = None
            st.rerun()
    
    uploaded_pdf = st.file_uploader("📄 PDF", type=['pdf'])
    if uploaded_pdf:
        st.session_state.uploaded_pdf = uploaded_pdf
        st.success(f"✅ {uploaded_pdf.name}")
        if st.session_state.pdf_text is None:
            with st.spinner("📖 Reading..."):
                text, pages = extract_pdf_text(uploaded_pdf)
                if text:
                    st.session_state.pdf_text = text
                    st.info(f"📑 {pages} pages")
        if st.button("🗑️ Remove", key="rm_pdf"):
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
    
    if st.session_state.messages:
        st.markdown("### 📥 Export")
        st.download_button("💬 Markdown", export_chat_markdown(),
                         f"chat_{datetime.now().strftime('%Y%m%d')}.md", "text/markdown", use_container_width=True)
        st.download_button("📊 JSON", export_chat_json(),
                         f"chat_{datetime.now().strftime('%Y%m%d')}.json", "application/json", use_container_width=True)

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
        
        Upload files via sidebar and ask me anything!
        """)

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message("user", avatar="👤"):
        st.markdown(msg["user"])
    
    with st.chat_message("assistant", avatar="✨"):
        st.markdown(msg["bot"])
        
        if '|' in msg["bot"] and '-|-' in msg["bot"]:
            excel_data = create_excel_from_response(msg["bot"])
            if excel_data:
                st.download_button("📥 Excel", excel_data,
                                 f"table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 key=f"xl_{i}", use_container_width=True)

# Chat Input
if prompt := st.chat_input("💭 Ask me anything..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    image_data = None
    if st.session_state.uploaded_image:
        image_data = process_image(st.session_state.uploaded_image)
    
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("✨ Thinking..."):
            response = get_gemini_response(prompt, st.session_state.messages,
                                         image=image_data, pdf_text=st.session_state.pdf_text)
        st.markdown(response)
        
        if '|' in response and '-|-' in response:
            excel_data = create_excel_from_response(response)
            if excel_data:
                st.download_button("📥 Excel", excel_data,
                                 f"table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 key="xl_new", use_container_width=True)
    
    st.session_state.messages.append({"user": prompt, "bot": response, "timestamp": datetime.now().isoformat()})
    st.rerun()