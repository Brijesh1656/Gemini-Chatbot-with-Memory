from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import time
from PIL import Image
import PyPDF2
from datetime import datetime, timezone, timedelta
import json
import re
import pandas as pd
from io import BytesIO

# Indian Standard Time (IST) timezone
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_time():
    """Get current time in Indian Standard Time"""
    return datetime.now(IST)

# Load environment variables
load_dotenv()

# Get API key (handle secrets.toml not existing)
api_key = None
try:
    if hasattr(st, 'secrets') and 'GOOGLE_API_KEY' in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    pass

if not api_key:
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
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS with Glassmorphism & Advanced Animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Animated Background */
    .main {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        position: relative;
        overflow: hidden;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Floating orbs background effect */
    .main::before {
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: 
            radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(99, 102, 241, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(168, 85, 247, 0.2) 0%, transparent 50%);
        animation: floatOrbs 20s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }
    
    @keyframes floatOrbs {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        33% { transform: translate(30px, -30px) rotate(120deg); }
        66% { transform: translate(-20px, 20px) rotate(240deg); }
    }
    
    /* Glassmorphism Chat Messages */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border-radius: 20px;
        padding: 24px;
        margin: 12px 0;
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeInUp 0.5s ease-out;
    }
    
    .stChatMessage:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px 0 rgba(99, 102, 241, 0.5);
        border-color: rgba(168, 85, 247, 0.4);
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    [data-testid="stChatMessageContent"] {
        color: #f0f0f0;
        font-size: 15px;
        line-height: 1.7;
        font-weight: 400;
    }
    
    /* Stunning Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(17, 24, 39, 0.95) 0%, rgba(31, 41, 55, 0.95) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(139, 92, 246, 0.3);
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 200px;
        background: linear-gradient(180deg, rgba(139, 92, 246, 0.2) 0%, transparent 100%);
        pointer-events: none;
    }
    
    /* Animated Title */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #00f2fe 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        margin-bottom: 0.5rem;
        animation: gradientText 3s ease infinite, glow 2s ease-in-out infinite;
        letter-spacing: -1px;
        text-shadow: 0 0 40px rgba(139, 92, 246, 0.5);
    }
    
    @keyframes gradientText {
        0%, 100% { background-position: 0% center; }
        50% { background-position: 100% center; }
    }
    
    @keyframes glow {
        0%, 100% { filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.7)); }
        50% { filter: drop-shadow(0 0 40px rgba(168, 85, 247, 0.9)); }
    }
    
    h2 {
        color: #c4b5fd;
        font-weight: 700;
        font-size: 1.5rem;
        margin-top: 1.5rem;
    }
    
    h3 {
        background: linear-gradient(135deg, #a78bfa 0%, #c4b5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        margin-top: 1.5rem;
    }
    
    /* Premium Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    /* Download Button Styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
        box-shadow: 0 8px 25px rgba(245, 87, 108, 0.6);
    }
    
    /* Premium File Uploader */
    [data-testid="stFileUploader"] {
        background: rgba(139, 92, 246, 0.08);
        border: 2px dashed rgba(139, 92, 246, 0.5);
        border-radius: 16px;
        padding: 20px;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        background: rgba(139, 92, 246, 0.15);
        border-color: rgba(168, 85, 247, 0.8);
        box-shadow: 0 8px 30px rgba(139, 92, 246, 0.3);
    }
    
    /* Chat Input with Glow Effect */
    .stChatInputContainer {
        border-radius: 16px;
        border: 2px solid rgba(139, 92, 246, 0.5);
        background: rgba(38, 39, 48, 0.7);
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(139, 92, 246, 0.2);
        transition: all 0.3s ease;
    }
    
    .stChatInputContainer:focus-within {
        border-color: rgba(168, 85, 247, 1);
        box-shadow: 0 8px 40px rgba(139, 92, 246, 0.5);
        transform: translateY(-2px);
    }
    
    /* Metrics with Gradient */
    [data-testid="stMetricValue"] {
        font-size: 26px;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    [data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.7);
        font-weight: 600;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Expander with Glass Effect */
    .streamlit-expanderHeader {
        background: rgba(139, 92, 246, 0.15);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        font-weight: 600;
        border: 1px solid rgba(139, 92, 246, 0.3);
        transition: all 0.3s ease;
        padding: 12px 16px;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(139, 92, 246, 0.25);
        border-color: rgba(168, 85, 247, 0.6);
        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.3);
    }
    
    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.5), transparent);
        margin: 24px 0;
    }
    
    /* Code blocks */
    code {
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 6px;
        padding: 2px 6px;
        color: #c4b5fd;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.2);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Caption styling */
    .caption {
        color: rgba(255, 255, 255, 0.5);
        font-size: 12px;
        font-weight: 500;
    }
    
    /* Info boxes */
    [data-testid="stMarkdownContainer"] p {
        color: rgba(255, 255, 255, 0.85);
    }
    
    /* Success/Warning/Error boxes */
    .stAlert {
        border-radius: 12px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Image containers */
    [data-testid="stImage"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease;
    }
    
    [data-testid="stImage"]:hover {
        transform: scale(1.02);
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Bounce animation for welcome emoji */
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-20px); }
    }
    
    /* Fade in animation */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* Pulse animation for notifications */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Shake animation for errors */
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
    /* Slide in from left */
    @keyframes slideInLeft {
        from {
            transform: translateX(-100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    /* Slide in from right */
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    /* User messages slide from right */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        animation: slideInRight 0.4s ease-out;
    }
    
    /* Assistant messages slide from left */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        animation: slideInLeft 0.4s ease-out;
    }
    
    /* Hover effect for sidebar items */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        transition: transform 0.2s ease;
    }
    
    /* Link styling */
    a {
        color: #8b5cf6;
        text-decoration: none;
        transition: color 0.3s ease;
    }
    
    a:hover {
        color: #a78bfa;
        text-decoration: underline;
    }
    
    /* Textarea focus effect */
    textarea:focus {
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.5) !important;
    }
    
    /* Success message animation */
    .stSuccess {
        animation: slideInRight 0.5s ease-out;
    }
    
    /* Warning message animation */
    .stWarning {
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* Error message animation */
    .stError {
        animation: shake 0.5s ease-in-out;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
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
        "export_time": get_ist_time().isoformat(),
        "message_count": len(st.session_state.messages),
        "messages": st.session_state.messages
    }
    return json.dumps(export_data, indent=2)

def export_chat_markdown():
    """Export chat as markdown"""
    markdown = f"# Gemini AI Chat Session\n\n"
    markdown += f"**Date:** {get_ist_time().strftime('%Y-%m-%d %H:%M:%S')} IST\n"
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
    st.session_state.session_start = get_ist_time()
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 2048

# Header with Modern Design
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem; animation: fadeIn 1s ease-in;'>
    <h1 style='margin-bottom: 0.5rem;'>🌟 GeminiFlow</h1>
    <p style='color: rgba(255,255,255,0.7); font-size: 18px; font-weight: 500; letter-spacing: 2px;'>
        <span style='color: #667eea;'>●</span> Excel Export 
        <span style='color: #764ba2;'>●</span> Image Analysis 
        <span style='color: #f093fb;'>●</span> PDF Processing
    </p>
    <p style='color: rgba(255,255,255,0.5); font-size: 14px; margin-top: 8px; font-style: italic;'>
        Experience AI-powered assistance like never before
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 20px 0; margin-bottom: 20px;'>
        <h2 style='font-size: 24px; font-weight: 700; margin: 0;'>🎛️ Control Hub</h2>
        <p style='color: rgba(255,255,255,0.5); font-size: 12px; margin-top: 5px;'>Customize your experience</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📊 Session Stats", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💬 Messages", len(st.session_state.messages))
        with col2:
            duration = get_ist_time() - st.session_state.session_start
            mins = duration.seconds // 60
            st.metric("⏱️ Duration", f"{mins}m")
    
    st.divider()
    
    with st.expander("⚡ Quick Prompts"):
        st.markdown("**Click to use:**")
        quick_prompts = {
            "📊 Excel Table": "Create a markdown table with this data in Excel-ready format with proper calculations",
            "🔢 Math Solution": "Solve this step-by-step showing all calculations clearly",
            "📈 Financial Analysis": "Analyze this financial data and present in a professional table format",
            "📋 Summarize PDF": "Summarize the key points from this document in bullet points",
            "🖼️ Extract Data": "Extract all numerical data from this image and organize in a table"
        }
        for label, prompt in quick_prompts.items() :
            if st.button(label, key=f"quick_{label}", use_container_width=True):
                st.info(f"💡 '{prompt}'\n\nNow add your details!")
    
    st.divider()
    
    with st.expander("⚙️ Model Settings"):
        st.session_state.temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        st.session_state.max_tokens = st.slider("Max Tokens", 256, 8192, 2048, 256)
    
    st.divider()
    
    st.markdown("### 📁 File Upload Zone")
    st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 12px; margin-bottom: 10px;'>Drag & drop or click to browse</p>", unsafe_allow_html=True)
    
    uploaded_image = st.file_uploader("🖼️ Upload Image", type=['png', 'jpg', 'jpeg', 'webp', 'gif'])
    if uploaded_image:
        st.session_state.uploaded_image = uploaded_image
        st.success(f"✅ {uploaded_image.name}")
        st.caption(f"📦 {get_file_size(uploaded_image)}")
        img = process_image(uploaded_image)
        if img:
            st.image(img, use_container_width=True)
            st.caption(f"📐 {img.width}x{img.height}")
        if st.button("🗑️ Remove Image"):
            st.session_state.uploaded_image = None
            st.rerun()
    
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
                    word_count = len(text.split())
                    st.info(f"📑 {pages} pages • {word_count:,} words")
        else:
            word_count = len(st.session_state.pdf_text.split())
            st.info(f"📑 {word_count:,} words extracted")
        if st.button("🗑️ Remove PDF"):
            st.session_state.uploaded_pdf = None
            st.session_state.pdf_text = None
            st.rerun()
    
    st.divider()
    
    st.markdown("### ⚡ Quick Actions")
    st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 12px; margin-bottom: 10px;'>Manage your session</p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear", help="Clear chat history"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 Reset", help="Reset everything"):
            st.session_state.messages = []
            st.session_state.uploaded_image = None
            st.session_state.uploaded_pdf = None
            st.session_state.pdf_text = None
            st.session_state.session_start = get_ist_time()
            st.rerun()
    
    if st.session_state.messages:
        st.markdown("### 📥 Export Options")
        st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 12px; margin-bottom: 10px;'>Download your conversation</p>", unsafe_allow_html=True)
        has_tables = any('|' in msg['bot'] and '-|-' in msg['bot'] for msg in st.session_state.messages)
        if has_tables:
            st.caption("💡 Excel buttons appear below table responses")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("� TXT", data=export_chat_markdown(),
                             file_name=f"chat_{get_ist_time().strftime('%Y%m%d_%H%M%S')}.md",
                             mime="text/markdown", use_container_width=True)
        with col2:
            st.download_button("📊 JSON", data=export_chat_json(),
                             file_name=f"chat_{get_ist_time().strftime('%Y%m%d_%H%M%S')}.json",
                             mime="application/json", use_container_width=True)
    
    st.divider()
    
    with st.expander("🤖 About"):
        st.markdown("""
        **Model:** gemini-2.0-flash-exp
        
        **Features:**
        - 💬 Chat & Q&A
        - 📊 Excel Export (auto)
        - 🔢 Math Solutions
        - 🖼️ Image Analysis
        - 📄 PDF Processing
        """)

# Main chat
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align: center; padding: 40px 20px; animation: fadeIn 1.5s ease-in;'>
            <div style='font-size: 80px; margin-bottom: 20px; animation: bounce 2s infinite;'>✨</div>
            <h2 style='color: #c4b5fd; font-size: 28px; margin-bottom: 15px;'>Welcome to GeminiFlow</h2>
            <p style='color: rgba(255,255,255,0.6); font-size: 16px; max-width: 600px; margin: 0 auto 30px;'>
                Your intelligent AI companion powered by Google Gemini 2.0
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.chat_message("assistant", avatar="🌟"):
            st.markdown("""
            ### 🎯 What I Can Do For You:
            
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 20px;'>
                <div style='background: rgba(102, 126, 234, 0.1); padding: 20px; border-radius: 12px; border-left: 3px solid #667eea;'>
                    <h4 style='color: #667eea; margin: 0 0 10px 0;'>📊 Excel & Data</h4>
                    <p style='color: rgba(255,255,255,0.7); font-size: 14px; margin: 0;'>Tables auto-export to Excel with perfect formatting</p>
                </div>
                <div style='background: rgba(118, 75, 162, 0.1); padding: 20px; border-radius: 12px; border-left: 3px solid #764ba2;'>
                    <h4 style='color: #a78bfa; margin: 0 0 10px 0;'>🔢 Math Problems</h4>
                    <p style='color: rgba(255,255,255,0.7); font-size: 14px; margin: 0;'>Step-by-step solutions with clear explanations</p>
                </div>
                <div style='background: rgba(240, 147, 251, 0.1); padding: 20px; border-radius: 12px; border-left: 3px solid #f093fb;'>
                    <h4 style='color: #f093fb; margin: 0 0 10px 0;'>🖼️ Image Analysis</h4>
                    <p style='color: rgba(255,255,255,0.7); font-size: 14px; margin: 0;'>Extract data, analyze charts & diagrams</p>
                </div>
                <div style='background: rgba(79, 172, 254, 0.1); padding: 20px; border-radius: 12px; border-left: 3px solid #4facfe;'>
                    <h4 style='color: #4facfe; margin: 0 0 10px 0;'>📄 PDF Processing</h4>
                    <p style='color: rgba(255,255,255,0.7); font-size: 14px; margin: 0;'>Summarize documents & extract information</p>
                </div>
            </div>
            
            ---
            
            ### 💡 Pro Tips:
            
            - 🎯 **Use Quick Prompts** in the sidebar for common tasks
            - 📊 **Request "markdown table format"** for instant Excel export
            - 🎨 **Upload files first** then ask questions about them
            - ⚡ **Be specific** for the best results
            
            <div style='text-align: center; margin-top: 30px; padding: 20px; background: rgba(139, 92, 246, 0.1); border-radius: 12px;'>
                <p style='color: #c4b5fd; font-size: 18px; font-weight: 600; margin: 0;'>
                    Ready to get started? 🚀
                </p>
                <p style='color: rgba(255,255,255,0.5); font-size: 14px; margin-top: 8px;'>
                    Type your question below or try a quick prompt!
                </p>
            </div>
            
            ---
            
            <div style='text-align: center; margin-top: 20px; padding: 15px;'>
                <p style='color: #8b5cf6; font-size: 14px; font-weight: 600; margin: 0;'>
                    ⚡ Powered by Google Gemini 2.0 Flash
                </p>
                <p style='color: rgba(255,255,255,0.5); font-size: 13px; margin-top: 5px;'>
                    Built with ❤️ by <span style='color: #a78bfa; font-weight: 600;'>Brijesh Singh</span>
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["user"])
            tags = []
            if msg.get("has_image"):
                tags.append("🖼️")
            if msg.get("has_pdf"):
                tags.append("📄")
            if tags:
                st.caption(" ".join(tags))
        
        with st.chat_message("assistant", avatar="✨"):
            st.markdown(msg["bot"])
            
            if '|' in msg["bot"] and '-|-' in msg["bot"]:
                col_a, col_b = st.columns([1, 4])
                with col_a:
                    excel_data = create_excel_from_response(msg["bot"])
                    if excel_data:
                        st.download_button("📥 Excel", data=excel_data,
                                         file_name=f"data_{i}_{get_ist_time().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                         key=f"excel_{i}")
                with col_b:
                    with st.expander("📋 Copy Raw"):
                        st.code(msg["bot"], language="markdown")
            elif '```' in msg["bot"]:
                with st.expander("📋 Copy Raw"):
                    st.code(msg["bot"], language="markdown")
            
            if "timestamp" in msg:
                try:
                    ts = datetime.fromisoformat(msg["timestamp"])
                    st.caption(f"🕒 {ts.strftime('%I:%M %p')}")
                except:
                    pass

# Chat input
if prompt := st.chat_input("💭 Message Gemini..."):
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        context_tags = []
        if st.session_state.uploaded_image:
            context_tags.append("🖼️")
        if st.session_state.uploaded_pdf:
            context_tags.append("📄")
        if context_tags:
            st.caption(" ".join(context_tags))
    
    image_data = None
    if st.session_state.uploaded_image:
        image_data = process_image(st.session_state.uploaded_image)
    
    with st.chat_message("assistant", avatar="✨"):
        message_placeholder = st.empty()
        
        with st.spinner("🤔 Thinking..."):
            response = get_gemini_response(prompt, st.session_state.messages, 
                                         image=image_data, pdf_text=st.session_state.pdf_text)
        
        full_text = ""
        words = response.split()
        for i, word in enumerate(words):
            full_text += word + " "
            if i % 3 == 0 or i == len(words) - 1:
                message_placeholder.markdown(full_text + "▌")
                time.sleep(0.03)
        message_placeholder.markdown(response)
        
        if '|' in response and '-|-' in response:
            col_a, col_b = st.columns([1, 4])
            with col_a:
                excel_data = create_excel_from_response(response)
                if excel_data:
                    st.download_button("📥 Excel", data=excel_data,
                                     file_name=f"data_{get_ist_time().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                     key="excel_current")
            with col_b:
                with st.expander("📋 Copy Raw"):
                    st.code(response, language="markdown")
        elif '```' in response:
            with st.expander("📋 Copy Raw"):
                st.code(response, language="markdown")
        
        st.caption(f"🕒 {get_ist_time().strftime('%I:%M %p')}")
    
    st.session_state.messages.append({
        "user": prompt, "bot": response,
        "has_image": st.session_state.uploaded_image is not None,
        "has_pdf": st.session_state.uploaded_pdf is not None,
        "timestamp": get_ist_time().isoformat()
    })
    st.rerun()


