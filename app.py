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
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stChatMessage {
        background-color: rgba(38, 39, 48, 0.8);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid rgba(250, 250, 250, 0.1);
    }
    [data-testid="stChatMessageContent"] {
        color: #fafafa;
        font-size: 15px;
        line-height: 1.6;
    }
    [data-testid="stSidebar"] {
        background-color: #1a1d24;
        border-right: 1px solid rgba(250, 250, 250, 0.1);
    }
    h1 {
        color: #8b5cf6;
        text-align: center;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem;
    }
    h3 {
        color: #a78bfa;
        margin-top: 1.5rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        padding: 10px;
        font-weight: 600;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    [data-testid="stFileUploader"] {
        background-color: rgba(139, 92, 246, 0.05);
        border: 2px dashed rgba(139, 92, 246, 0.3);
        border-radius: 10px;
        padding: 15px;
    }
    .stChatInputContainer {
        border-radius: 10px;
        border: 2px solid rgba(139, 92, 246, 0.3);
        background-color: rgba(38, 39, 48, 0.6);
    }
    [data-testid="stMetricValue"] {
        font-size: 22px;
        font-weight: 700;
        color: #8b5cf6;
    }
    .streamlit-expanderHeader {
        background-color: rgba(139, 92, 246, 0.1);
        border-radius: 8px;
        font-weight: 600;
    }
    hr {
        border: none;
        height: 1px;
        background: rgba(250, 250, 250, 0.1);
        margin: 20px 0;
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

# Header
st.title("✨ GeminiFlow")
st.markdown("<p style='text-align: center; color: rgba(250,250,250,0.6); font-size: 16px;'>Excel Export • Image Analysis • PDF Processing • Powered by Gemini 2.0</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎛️ Control Center")
    
    with st.expander("📊 Session Stats", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", len(st.session_state.messages))
        with col2:
            duration = datetime.now() - st.session_state.session_start
            mins = duration.seconds // 60
            st.metric("Duration", f"{mins}m")
    
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
        for label, prompt in quick_prompts.items():
            if st.button(label, key=f"quick_{label}", use_container_width=True):
                st.info(f"💡 '{prompt}'\n\nNow add your details!")
    
    st.divider()
    
    with st.expander("⚙️ Model Settings"):
        st.session_state.temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        st.session_state.max_tokens = st.slider("Max Tokens", 256, 8192, 2048, 256)
    
    st.divider()
    
    st.markdown("### 📁 Upload Files")
    
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
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 Reset All"):
            st.session_state.messages = []
            st.session_state.uploaded_image = None
            st.session_state.uploaded_pdf = None
            st.session_state.pdf_text = None
            st.session_state.session_start = datetime.now()
            st.rerun()
    
    if st.session_state.messages:
        st.markdown("### 📥 Export")
        has_tables = any('|' in msg['bot'] and '-|-' in msg['bot'] for msg in st.session_state.messages)
        if has_tables:
            st.caption("💡 Excel buttons appear below table responses")
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("💬 Chat (TXT)", data=export_chat_markdown(),
                             file_name=f"geminiflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                             mime="text/markdown", use_container_width=True)
        with col2:
            st.download_button("📊 Chat (JSON)", data=export_chat_json(),
                             file_name=f"geminiflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                             mime="application/json", use_container_width=True)
    
    st.divider()
    
    with st.expander("🤖 About GeminiFlow"):
        st.markdown("""
        **Model:** Gemini 2.0 Flash
        
        **Features:**
        - 💬 Multi-turn conversations
        - 📊 Auto Excel export
        - 🔢 Math & calculations
        - 🖼️ Image analysis
        - 📄 PDF processing
        
        **Created by:** Brijesh Singh
        """)

# Main chat
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="✨"):
            st.markdown("""
            👋 **Welcome to GeminiFlow!**
            
            Your AI-powered productivity assistant with:
            - 📊 **Excel Auto-Export** - Tables convert instantly
            - 🔢 **Math Solutions** - Step-by-step calculations
            - 🖼️ **Image Analysis** - Extract data from visuals
            - 📄 **PDF Processing** - Summarize & analyze documents
            
            **💡 Quick Tips:**
            - Ask for "markdown table format" for Excel
            - Use Quick Prompts in the sidebar
            - Excel downloads appear automatically
            
            Ready to flow? Let's begin! 🚀
            """)
    
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
                                         file_name=f"geminiflow_data_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
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
if prompt := st.chat_input("💭 Message GeminiFlow..."):
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
                                     file_name=f"geminiflow_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                     key="excel_current")
            with col_b:
                with st.expander("📋 Copy Raw"):
                    st.code(response, language="markdown")
        elif '```' in response:
            with st.expander("📋 Copy Raw"):
                st.code(response, language="markdown")
        
        st.caption(f"🕒 {datetime.now().strftime('%I:%M %p')}")
    
    st.session_state.messages.append({
        "user": prompt, "bot": response,
        "has_image": st.session_state.uploaded_image is not None,
        "has_pdf": st.session_state.uploaded_pdf is not None,
        "timestamp": datetime.now().isoformat()
    })
    st.rerun()

# Footer
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    with st.expander("💡 Tips"):
        st.markdown("""
        - Be specific and clear
        - Upload files before asking
        - Use Quick Prompts
        - Clear chat for new topics
        """)

with col2:
    with st.expander("📊 Excel Export"):
        st.markdown("""
        **Auto Excel Download:**
        - Ask for "table format"
        - Click "📥 Excel" below response
        - Downloads formatted table
        - Ready for immediate use
        """)

with col3:
    with st.expander("🎯 Best Practices"):
        st.markdown("""
        - Request "Excel-ready format"
        - Ask for "step-by-step"
        - Use "show all formulas"
        - Specify "markdown table"
        """)

st.markdown("""
<div style='text-align: center; padding: 20px; opacity: 0.6;'>
    <p>GeminiFlow • Powered by Google Gemini 2.0 • Created by Brijesh Singh</p>
</div>
""", unsafe_allow_html=True)
