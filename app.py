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

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Page config
st.set_page_config(
    page_title="GeminiFlow - AI Assistant",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🚀 FULLY RESPONSIVE ULTRA-MODERN DESIGN
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* Premium Dark Theme */
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
    
    /* Mobile Optimization */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.75rem !important;
        }
    }
    
    /* Glassmorphic Hero */
    .hero-section {
        position: relative;
        text-align: center;
        padding: 3rem 1.5rem;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        overflow: hidden;
    }
    
    @media (max-width: 768px) {
        .hero-section {
            padding: 2rem 1rem;
            margin-bottom: 1.5rem;
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
        background: radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
        animation: pulse 8s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    .logo-wrapper {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
        position: relative;
        z-index: 1;
    }
    
    .logo {
        font-size: 2.5rem;
    }
    
    .brand-name {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
    }
    
    @media (max-width: 768px) {
        .logo {
            font-size: 2rem;
        }
        .brand-name {
            font-size: 2rem;
        }
    }
    
    .hero-tagline {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.6);
        font-weight: 500;
        position: relative;
        z-index: 1;
        letter-spacing: 0.01em;
        line-height: 1.5;
    }
    
    @media (max-width: 768px) {
        .hero-tagline {
            font-size: 0.875rem;
        }
    }
    
    /* Premium Stat Cards - Fully Responsive */
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    @media (max-width: 768px) {
        .stat-grid {
            grid-template-columns: 1fr;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }
    }
    
    .stat-card {
        position: relative;
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(20px);
        padding: 1.5rem 1.25rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
        overflow: hidden;
    }
    
    @media (max-width: 768px) {
        .stat-card {
            padding: 1.25rem 1rem;
            border-radius: 16px;
        }
    }
    
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.6), transparent);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-4px);
        border-color: rgba(139, 92, 246, 0.3);
        background: rgba(139, 92, 246, 0.03);
        box-shadow: 0 20px 60px rgba(139, 92, 246, 0.15);
    }
    
    @media (max-width: 768px) {
        .stat-card:hover {
            transform: translateY(-2px);
        }
    }
    
    .stat-card:hover::before {
        opacity: 1;
    }
    
    .stat-icon {
        font-size: 1.25rem;
        margin-bottom: 0.75rem;
        opacity: 0.8;
    }
    
    .stat-label {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.5);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 900;
        color: #ffffff;
        line-height: 1;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    @media (max-width: 768px) {
        .stat-value {
            font-size: 1.75rem;
        }
    }
    
    .stat-delta {
        font-size: 0.813rem;
        color: #22c55e;
        font-weight: 600;
        opacity: 0.9;
    }
    
    /* Chat Messages - Mobile Optimized */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.02) !important;
        border-radius: 16px !important;
        padding: 1.25rem !important;
        margin: 1rem 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        transition: all 0.3s ease !important;
    }
    
    @media (max-width: 768px) {
        .stChatMessage {
            padding: 1rem 0.75rem !important;
            margin: 0.75rem 0 !important;
            border-radius: 12px !important;
        }
    }
    
    .stChatMessage:hover {
        background: rgba(255, 255, 255, 0.03) !important;
        border-color: rgba(139, 92, 246, 0.2) !important;
    }
    
    [data-testid="stChatMessageContent"] {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 1rem !important;
        line-height: 1.7 !important;
        font-weight: 400 !important;
    }
    
    @media (max-width: 768px) {
        [data-testid="stChatMessageContent"] {
            font-size: 0.938rem !important;
            line-height: 1.6 !important;
        }
    }
    
    /* Upload Section - Mobile Friendly */
    [data-testid="stFileUploader"] {
        background: transparent !important;
    }
    
    [data-testid="stFileUploader"] section {
        background: rgba(255, 255, 255, 0.02);
        border: 2px dashed rgba(139, 92, 246, 0.3);
        border-radius: 16px;
        padding: 2rem 1rem;
        transition: all 0.3s ease;
    }
    
    @media (max-width: 768px) {
        [data-testid="stFileUploader"] section {
            padding: 1.5rem 0.75rem;
            border-radius: 12px;
        }
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(139, 92, 246, 0.6);
        background: rgba(139, 92, 246, 0.02);
    }
    
    [data-testid="stFileUploader"] label {
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 600 !important;
        font-size: 0.938rem !important;
    }
    
    /* Premium Input Fields - Touch Optimized */
    .stTextInput > label, .stTextArea > label {
        color: rgba(255, 255, 255, 0.5) !important;
        font-weight: 600 !important;
        font-size: 0.813rem !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem !important;
    }
    
    /* Chat Input Container - Mobile Optimized */
    .stChatInputContainer {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 0.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    @media (max-width: 768px) {
        .stChatInputContainer {
            border-radius: 12px !important;
        }
    }
    
    .stChatInputContainer:focus-within {
        border-color: rgba(139, 92, 246, 0.6) !important;
        background: rgba(139, 92, 246, 0.03) !important;
        box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.1) !important;
    }
    
    /* Ultra-Modern Button - Touch Friendly */
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
        color: white;
        border: none;
        padding: 0.875rem 1.5rem;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.938rem;
        transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
        text-transform: none;
        letter-spacing: 0.02em;
        box-shadow: 0 8px 32px rgba(139, 92, 246, 0.3);
        width: 100%;
        position: relative;
        overflow: hidden;
        min-height: 44px; /* Touch target size */
    }
    
    @media (max-width: 768px) {
        .stButton > button, .stDownloadButton > button {
            padding: 0.75rem 1.25rem;
            font-size: 0.875rem;
            border-radius: 10px;
        }
    }
    
    .stButton > button::before, .stDownloadButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.6s ease;
    }
    
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 48px rgba(139, 92, 246, 0.4);
    }
    
    .stButton > button:hover::before, .stDownloadButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:active, .stDownloadButton > button:active {
        transform: translateY(0);
    }
    
    /* Sleek Expander - Mobile Optimized */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 0.875rem !important;
        transition: all 0.3s ease;
        min-height: 44px; /* Touch target */
    }
    
    @media (max-width: 768px) {
        .streamlit-expanderHeader {
            padding: 0.75rem !important;
            font-size: 0.938rem !important;
        }
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(139, 92, 246, 0.05);
        border-color: rgba(139, 92, 246, 0.2);
    }
    
    /* Premium Metrics - Responsive */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        letter-spacing: -0.02em !important;
    }
    
    @media (max-width: 768px) {
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
    }
    
    [data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.5) !important;
        font-size: 0.813rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Sidebar - Mobile Drawer Style */
    [data-testid="stSidebar"] {
        background: #000000 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
    
    [data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
    }
    
    @media (max-width: 768px) {
        [data-testid="stSidebar"] .block-container {
            padding: 1rem !important;
        }
    }
    
    /* Section Titles - Responsive */
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 1rem;
        letter-spacing: -0.02em;
    }
    
    @media (max-width: 768px) {
        .section-title {
            font-size: 1.125rem;
            margin-bottom: 0.75rem;
        }
    }
    
    /* Premium Messages - Mobile Friendly */
    .stSuccess, .stWarning, .stInfo, .stError {
        border-radius: 12px !important;
        padding: 0.875rem !important;
        backdrop-filter: blur(10px);
    }
    
    @media (max-width: 768px) {
        .stSuccess, .stWarning, .stInfo, .stError {
            padding: 0.75rem !important;
            font-size: 0.875rem !important;
        }
    }
    
    .stSuccess {
        background: rgba(34, 197, 94, 0.1) !important;
        border-left: 3px solid #22c55e !important;
        color: #fff !important;
    }
    
    .stWarning {
        background: rgba(245, 158, 11, 0.1) !important;
        border-left: 3px solid #f59e0b !important;
        color: #fff !important;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        border-left: 3px solid #3b82f6 !important;
        color: #fff !important;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border-left: 3px solid #ef4444 !important;
        color: #fff !important;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Typography - Responsive */
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }
    
    h1 { font-size: 2rem !important; }
    h2 { font-size: 1.625rem !important; }
    h3 { font-size: 1.375rem !important; }
    
    @media (max-width: 768px) {
        h1 { font-size: 1.75rem !important; }
        h2 { font-size: 1.5rem !important; }
        h3 { font-size: 1.25rem !important; }
    }
    
    p {
        color: rgba(255, 255, 255, 0.7) !important;
        line-height: 1.6 !important;
    }
    
    @media (max-width: 768px) {
        p {
            font-size: 0.938rem !important;
        }
    }
    
    /* Caption Styling */
    .stCaption {
        color: rgba(255, 255, 255, 0.4) !important;
        font-size: 0.813rem !important;
    }
    
    @media (max-width: 768px) {
        .stCaption {
            font-size: 0.75rem !important;
        }
    }
    
    /* Slider - Touch Friendly */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #8b5cf6 0%, #6366f1 100%) !important;
    }
    
    .stSlider [role="slider"] {
        width: 20px !important;
        height: 20px !important;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #8b5cf6 0%, #6366f1 100%) !important;
        border-radius: 10px;
    }
    
    .stProgress > div > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: rgba(255, 255, 255, 0.06);
        margin: 1.5rem 0;
    }
    
    /* Code blocks - Mobile Scrollable */
    code {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #8b5cf6 !important;
        padding: 0.2rem 0.4rem !important;
        border-radius: 6px !important;
        font-size: 0.875rem !important;
    }
    
    @media (max-width: 768px) {
        code {
            font-size: 0.813rem !important;
        }
    }
    
    pre {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 12px !important;
        overflow-x: auto !important;
        max-width: 100% !important;
    }
    
    /* Column Responsiveness */
    [data-testid="column"] {
        padding: 0 0.5rem !important;
    }
    
    @media (max-width: 768px) {
        [data-testid="column"] {
            padding: 0 0.25rem !important;
            width: 100% !important;
        }
    }
    
    /* Image Responsiveness */
    img {
        max-width: 100% !important;
        height: auto !important;
        border-radius: 12px;
    }
    
    /* Spinner - Mobile Optimized */
    .stSpinner > div {
        border-color: rgba(139, 92, 246, 0.3) !important;
        border-top-color: #8b5cf6 !important;
    }
    
    /* Tables - Mobile Scrollable */
    table {
        width: 100% !important;
        overflow-x: auto !important;
        display: block !important;
        font-size: 0.875rem !important;
    }
    
    @media (max-width: 768px) {
        table {
            font-size: 0.813rem !important;
        }
    }
    
    /* Chat Input - Better Mobile UX */
    [data-testid="stChatInput"] textarea {
        min-height: 44px !important;
        font-size: 1rem !important;
    }
    
    @media (max-width: 768px) {
        [data-testid="stChatInput"] textarea {
            font-size: 0.938rem !important;
        }
    }
    
    /* Prevent horizontal scroll on mobile */
    .main .block-container {
        overflow-x: hidden !important;
    }
    
    /* Better spacing on mobile */
    @media (max-width: 768px) {
        .element-container {
            margin-bottom: 0.75rem !important;
        }
        
        br {
            display: none;
        }
    }
</style>
""", unsafe_allow_html=True)

# Helper functions (keeping all the same)
def extract_pdf_text(pdf_file):
    """Extract text from PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        pages = len(pdf_reader.pages)
        
        if pages > 10:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        for i, page in enumerate(pdf_reader.pages):
            try:
                text += page.extract_text() + "\n"
                if pages > 10:
                    progress = (i + 1) / pages
                    progress_bar.progress(progress)
                    status_text.text(f"Processing page {i+1}/{pages}")
            except Exception as e:
                st.warning(f"⚠️ Could not read page {i+1}: {str(e)}")
        
        if pages > 10:
            progress_bar.empty()
            status_text.empty()
        
        return text.strip(), pages
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None, 0

def process_image(image_file):
    """Process uploaded image"""
    try:
        img = Image.open(image_file)
        max_size = 4096
        if img.width > max_size or img.height > max_size:
            st.warning(f"⚠️ Image resized from {img.width}x{img.height}")
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

def get_file_size(file):
    """Get human-readable file size"""
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def export_chat_json():
    """Export chat as JSON"""
    export_data = {
        "session_start": st.session_state.session_start.isoformat(),
        "export_time": datetime.now().isoformat(),
        "message_count": len(st.session_state.messages),
        "messages": st.session_state.messages
    }
    return json.dumps(export_data, indent=2)

def export_chat_markdown():
    """Export chat as markdown"""
    markdown = f"# GeminiFlow Chat Session\n\n"
    markdown += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    markdown += f"**Messages:** {len(st.session_state.messages)}\n\n---\n\n"
    for i, msg in enumerate(st.session_state.messages, 1):
        markdown += f"## Message {i}\n\n**👤 User:**\n{msg['user']}\n\n"
        markdown += f"**✨ Assistant:**\n{msg['bot']}\n\n"
        if msg.get('has_image'):
            markdown += "*[Image was attached]*\n\n"
        if msg.get('has_pdf'):
            markdown += "*[PDF document was attached]*\n\n"
        markdown += "---\n\n"
    return markdown

def extract_table_from_text(text):
    """Extract markdown table and convert to DataFrame"""
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
            df = pd.DataFrame(data, columns=headers)
            return df
    except:
        return None
    return None

def create_excel_from_response(response_text):
    """Create Excel file from response table"""
    df = extract_table_from_text(response_text)
    if df is None:
        return None
    
    output = BytesIO()
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
            worksheet = writer.sheets['Data']
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).apply(len).max(), len(str(col))) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = max_length
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        st.error(f"Error creating Excel: {str(e)}")
        return None

def get_gemini_response(question, history, image=None, pdf_text=None):
    """Generate response from Gemini"""
    try:
        context = ""
        
        if history:
            context += "=== Previous Conversation ===\n"
            for msg in history[-5:]:
                context += f"\nUser: {msg['user']}\n"
                context += f"Assistant: {msg['bot'][:200]}...\n" if len(msg['bot']) > 200 else f"Assistant: {msg['bot']}\n"
        
        if pdf_text:
            max_pdf_chars = 8000
            truncated = pdf_text[:max_pdf_chars]
            context += f"\n\n=== Document Content ===\n{truncated}"
            if len(pdf_text) > max_pdf_chars:
                context += f"\n\n[Note: Document truncated. Total length: {len(pdf_text)} characters]"
        
        formatting_instructions = """
IMPORTANT FORMATTING INSTRUCTIONS:
When providing responses with numerical data, tables, calculations, or Excel-related content:
1. ALWAYS use proper markdown tables with | separators and alignment
2. Format all calculations clearly showing: Formula → Calculation → Result
3. For Excel formulas, present them in code blocks or clearly formatted
4. Make tables directly copyable to Excel with proper column alignment
5. Use clear headers and organize data in rows and columns
6. Show step-by-step calculations for math problems
7. Present financial/numerical data in professional table format
8. Include units and proper number formatting

Example table format:
| Item | Formula | Calculation | Result |
|------|---------|-------------|--------|
| Sales Growth 5% | Base × 1.05 | 628 × 1.05 | 659.40 |
"""
        
        if context:
            full_prompt = f"{formatting_instructions}\n\n{context}\n\n=== Current Question ===\nUser: {question}\nAssistant:"
        else:
            full_prompt = f"{formatting_instructions}\n\nUser: {question}\nAssistant:"
        
        generation_config = {
            "temperature": st.session_state.temperature,
            "max_output_tokens": st.session_state.max_tokens,
        }
        
        if image:
            response = model.generate_content([full_prompt, image], generation_config=generation_config)
        else:
            response = model.generate_content(full_prompt, generation_config=generation_config)
        
        return response.text
    
    except Exception as e:
        error = str(e)
        if "quota" in error.lower() or "resource_exhausted" in error.lower():
            return "⚠️ **API Quota Exceeded**\n\nPlease wait and try again."
        elif "safety" in error.lower():
            return "⚠️ **Content Filtered**\n\nTry rephrasing your question."
        elif "invalid_argument" in error.lower():
            return "⚠️ **Invalid Request**\n\nCheck file size/format."
        else:
            return f"❌ **Error:** {error}"

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

# Hero Section
st.markdown("""
<div class="hero-section">
    <div class="logo-wrapper">
        <span class="logo">✨</span>
        <span class="brand-name">GeminiFlow</span>
    </div>
    <p class="hero-tagline">Excel Export • Image Analysis • PDF Processing<br>Powered by Gemini 2.0</p>
</div>
""", unsafe_allow_html=True)

# Stats Grid
st.markdown(f"""
<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-icon">💬</div>
        <div class="stat-label">Messages</div>
        <div class="stat-value">{len(st.session_state.messages)}</div>
        <div class="stat-delta">this session</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">🖼️</div>
        <div class="stat-label">Images</div>
        <div class="stat-value">{'1' if st.session_state.uploaded_image else '0'}</div>
        <div class="stat-delta">uploaded</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">📄</div>
        <div class="stat-label">Documents</div>
        <div class="stat-value">{'1' if st.session_state.uploaded_pdf else '0'}</div>
        <div class="stat-delta">processed</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Responsive Layout - Stack on mobile, side-by-side on desktop
# Use conditional rendering based on screen size via Streamlit columns
is_mobile = st.session_state.get('is_mobile', False)

# Sidebar for controls and files
with st.sidebar:
    st.markdown('<h3 class="section-title">⚙️ Controls</h3>', unsafe_allow_html=True)
    
    with st.expander("🎛️ Model Settings", expanded=False):
        st.session_state.temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        st.session_state.max_tokens = st.slider("Max Tokens", 256, 8192, 2048, 256)
    
    with st.expander("⚡ Quick Prompts", expanded=False):
        quick_prompts = {
            "📊 Excel Table": "Create a markdown table with this data in Excel-ready format",
            "🔢 Math Solution": "Solve this step-by-step showing all calculations",
            "📈 Analysis": "Analyze this data in a professional table format",
            "📋 Summarize": "Summarize the key points in bullet points",
            "🖼️ Extract Data": "Extract all data from this image in a table"
        }
        for label, prompt in quick_prompts.items():
            if st.button(label, key=f"quick_{label}", use_container_width=True):
                st.info(f"💡 '{prompt}'\n\nNow add your details!")
    
    st.markdown('<h3 class="section-title">📁 Files</h3>', unsafe_allow_html=True)
    
    uploaded_image = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg', 'webp', 'gif'], label_visibility="collapsed")
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
    
    uploaded_pdf = st.file_uploader("Upload PDF", type=['pdf'], label_visibility="collapsed")
    if uploaded_pdf:
        st.session_state.uploaded_pdf = uploaded_pdf
        st.success(f"✅ {uploaded_pdf.name}")
        st.caption(f"📦 {get_file_size(uploaded_pdf)}")
        if st.session_state.pdf_text is None:
            with st.spinner("Reading PDF..."):
                text, pages = extract_pdf_text(uploaded_pdf)
                if text:
                    st.session_state.pdf_text = text
                    word_count = len(text.split())
                    st.info(f"📑 {pages} pages • {word_count:,} words")
        else:
            word_count = len(st.session_state.pdf_text.split())
            st.info(f"📑 {word_count:,} words extracted")
        if st.button("🗑️ Remove PDF", use_container_width=True):
            st.session_state.uploaded_pdf = None
            st.session_state.pdf_text = None
            st.rerun()
    
    st.markdown('<h3 class="section-title">⚡ Actions</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.messages = []
            st.session_state.uploaded_image = None
            st.session_state.uploaded_pdf = None
            st.session_state.pdf_text = None
            st.session_state.session_start = datetime.now()
            st.rerun()
    
    if st.session_state.messages:
        st.markdown('<h3 class="section-title">📥 Export</h3>', unsafe_allow_html=True)
        
        st.download_button("💬 Markdown", data=export_chat_markdown(),
                         file_name=f"geminiflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                         mime="text/markdown", use_container_width=True)
        st.download_button("📊 JSON", data=export_chat_json(),
                         file_name=f"geminiflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                         mime="application/json", use_container_width=True)

# Main Chat Area
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="✨"):
            st.markdown("""
            ### 👋 Welcome to GeminiFlow!
            
            Your AI-powered productivity assistant with cutting-edge capabilities:
            
            **🎯 Core Features:**
            - 📊 **Excel Auto-Export** - Tables convert instantly to spreadsheets
            - 🔢 **Math Solutions** - Step-by-step calculations
            - 🖼️ **Image Analysis** - Extract and analyze visual data
            - 📄 **PDF Processing** - Summarize and analyze documents
            
            **💡 Pro Tips:**
            - Ask for "markdown table format" for instant Excel export
            - Use Quick Prompts in sidebar for common tasks
            - Upload images/PDFs before asking questions
            - Excel downloads appear below table responses
            
            Ready to get started? 🚀
            """)
    
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["user"])
            tags = []
            if msg.get("has_image"):
                tags.append("🖼️ Image")
            if msg.get("has_pdf"):
                tags.append("📄 PDF")
            if tags:
                st.caption(" • ".join(tags))
        
        with st.chat_message("assistant", avatar="✨"):
            st.markdown(msg["bot"])
            
            # Excel export button for tables
            if '|' in msg["bot"] and '-|-' in msg["bot"]:
                excel_data = create_excel_from_response(msg["bot"])
                if excel_data:
                    st.download_button("📥 Download Excel", data=excel_data,
                                     file_name=f"geminiflow_table_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                     key=f"excel_{i}", use_container_width=True)
                with st.expander("📋 View Raw Markdown"):
                    st.code(msg["bot"], language="markdown")
            elif '```' in msg["bot"]:
                with st.expander("📋 View Raw Code"):
                    st.code(msg["bot"], language="markdown")
            
            if "timestamp" in msg:
                try:
                    ts = datetime.fromisoformat(msg["timestamp"])
                    st.caption(f"🕒 {ts.strftime('%I:%M %p')}")
                except:
                    pass

# Chat input
if prompt := st.chat_input("💭 Message GeminiFlow..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        context_tags = []
        if st.session_state.uploaded_image:
            context_tags.append("🖼️ Image")
        if st.session_state.uploaded_pdf:
            context_tags.append("📄 PDF")
        if context_tags:
            st.caption(" • ".join(context_tags))
    
    image_data = None
    if st.session_state.uploaded_image:
        image_data = process_image(st.session_state.uploaded_image)
    
    with st.chat_message("assistant", avatar="✨"):
        message_placeholder = st.empty()
        
        with st.spinner("🤔 Thinking..."):
            response = get_gemini_response(prompt, st.session_state.messages, 
                                         image=image_data, pdf_text=st.session_state.pdf_text)
        
        # Animated typing effect
        full_text = ""
        words = response.split()
        for i, word in enumerate(words):
            full_text += word + " "
            if i % 3 == 0 or i == len(words) - 1:
                message_placeholder.markdown(full_text + "▌")
                time.sleep(0.03)
        message_placeholder.markdown(response)
        
        # Excel export for tables
        if '|' in response and '-|-' in response:
            excel_data = create_excel_from_response(response)
            if excel_data:
                st.download_button("📥 Download Excel", data=excel_data,
                                 file_name=f"geminiflow_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 key="excel_current", use_container_width=True)
            with st.expander("📋 View Raw Markdown"):
                st.code(response, language="markdown")
        elif '```' in response:
            with st.expander("📋 View Raw Code"):
                st.code(response, language="markdown")
        
        st.caption(f"🕒 {datetime.now().strftime('%I:%M %p')}")
    
    st.session_state.messages.append({
        "user": prompt, "bot": response,
        "has_image": st.session_state.uploaded_image is not None,
        "has_pdf": st.session_state.uploaded_pdf is not None,
        "timestamp": datetime.now().isoformat()
    })
    st.rerun()

# Footer - Responsive
st.divider()

# Stack columns on mobile
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    with st.expander("💡 Usage Tips"):
        st.markdown("""
        - Be specific in your requests
        - Upload files first before asking
        - Use Quick Prompts for common tasks
        - Clear chat when switching topics
        """)

with col2:
    with st.expander("📊 Excel Export"):
        st.markdown("""
        1. Ask for "table format"
        2. Wait for AI response
        3. Click "📥 Download Excel"
        4. File downloads automatically
        """)

with col3:
    with st.expander("🎯 Best Practices"):
        st.markdown("""
        - Request "Excel-ready format"
        - Ask for "step-by-step" math
        - Use "show all formulas"
        - Specify "markdown table"
        """)

st.markdown("""
<div style='text-align: center; padding: 1rem; opacity: 0.5;'>
    <p style='color: rgba(255, 255, 255, 0.6); font-size: 0.875rem;'>
        GeminiFlow • Powered by Google Gemini 2.0 Flash<br>
        Created by Brijesh Singh
    </p>
</div>
""", unsafe_allow_html=True)