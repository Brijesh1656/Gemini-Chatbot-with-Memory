from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import time
from PIL import Image
import PyPDF2
from datetime import datetime
import json

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
    page_title="Gemini AI Assistant",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Improved CSS with better readability
st.markdown("""
<style>
    /* Dark theme base */
    .main {
        background-color: #0e1117;
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: rgba(38, 39, 48, 0.8);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border: 1px solid rgba(250, 250, 250, 0.1);
    }
    
    /* User message styling */
    [data-testid="stChatMessageContent"] {
        color: #fafafa;
        font-size: 15px;
        line-height: 1.6;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1d24;
        border-right: 1px solid rgba(250, 250, 250, 0.1);
    }
    
    /* Headers */
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
    
    /* Buttons */
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
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: rgba(139, 92, 246, 0.05);
        border: 2px dashed rgba(139, 92, 246, 0.3);
        border-radius: 10px;
        padding: 15px;
    }
    
    /* Chat input */
    .stChatInputContainer {
        border-radius: 10px;
        border: 2px solid rgba(139, 92, 246, 0.3);
        background-color: rgba(38, 39, 48, 0.6);
    }
    
    /* Success/Info boxes */
    .stSuccess, .stInfo, .stWarning {
        border-radius: 8px;
        border: none;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 22px;
        font-weight: 700;
        color: #8b5cf6;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: rgba(139, 92, 246, 0.1);
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Caption text */
    .caption {
        color: rgba(250, 250, 250, 0.5);
        font-size: 13px;
    }
    
    /* Divider */
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
    """Extract text from PDF with better error handling"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        pages = len(pdf_reader.pages)
        
        # Progress indicator for large PDFs
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
    """Process uploaded image with validation"""
    try:
        img = Image.open(image_file)
        
        # Check size
        max_size = 4096
        if img.width > max_size or img.height > max_size:
            st.warning(f"⚠️ Image resized from {img.width}x{img.height} to fit limits")
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
    """Export chat history as JSON"""
    export_data = {
        "session_start": st.session_state.session_start.isoformat(),
        "export_time": datetime.now().isoformat(),
        "message_count": len(st.session_state.messages),
        "messages": st.session_state.messages
    }
    return json.dumps(export_data, indent=2)

def export_chat_markdown():
    """Export chat as formatted markdown"""
    markdown = f"# Gemini AI Chat Session\n\n"
    markdown += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    markdown += f"**Messages:** {len(st.session_state.messages)}\n\n"
    markdown += "---\n\n"
    
    for i, msg in enumerate(st.session_state.messages, 1):
        markdown += f"## Message {i}\n\n"
        markdown += f"**👤 User:**\n{msg['user']}\n\n"
        markdown += f"**✨ Assistant:**\n{msg['bot']}\n\n"
        
        if msg.get('has_image'):
            markdown += "*[Image was attached]*\n\n"
        if msg.get('has_pdf'):
            markdown += "*[PDF document was attached]*\n\n"
        
        markdown += "---\n\n"
    
    return markdown

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
if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = ""

# Header
st.title("✨ Gemini AI Assistant")
st.markdown("<p style='text-align: center; color: rgba(250,250,250,0.6); font-size: 16px;'>Your intelligent companion for text, images, and documents</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎛️ Control Center")
    
    # Session stats
    with st.expander("📊 Session Stats", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", len(st.session_state.messages))
        with col2:
            duration = datetime.now() - st.session_state.session_start
            mins = duration.seconds // 60
            st.metric("Duration", f"{mins}m")
    
    st.divider()
    
    # Quick prompts for common tasks
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
                st.session_state.quick_prompt = prompt
                st.info(f"💡 '{prompt}'\n\nNow add your specific details in the chat!")
    
    st.divider()
    
    # Model settings
    with st.expander("⚙️ Model Settings"):
        st.session_state.temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Higher values make output more random"
        )
        
        st.session_state.max_tokens = st.slider(
            "Max Response Length",
            min_value=256,
            max_value=8192,
            value=2048,
            step=256,
            help="Maximum tokens in response"
        )
    
    st.divider()
    
    # File uploads
    st.markdown("### 📁 Upload Files")
    
    # Image upload
    uploaded_image = st.file_uploader(
        "🖼️ Upload Image",
        type=['png', 'jpg', 'jpeg', 'webp', 'gif'],
        help="PNG, JPG, JPEG, WEBP, GIF supported"
    )
    
    if uploaded_image:
        st.session_state.uploaded_image = uploaded_image
        st.success(f"✅ {uploaded_image.name}")
        st.caption(f"📦 {get_file_size(uploaded_image)}")
        
        img = process_image(uploaded_image)
        if img:
            st.image(img, use_container_width=True)
            st.caption(f"📐 {img.width}x{img.height} pixels")
        
        if st.button("🗑️ Remove Image"):
            st.session_state.uploaded_image = None
            st.rerun()
    
    # PDF upload
    uploaded_pdf = st.file_uploader(
        "📄 Upload PDF",
        type=['pdf'],
        help="Upload PDF for analysis"
    )
    
    if uploaded_pdf:
        st.session_state.uploaded_pdf = uploaded_pdf
        st.success(f"✅ {uploaded_pdf.name}")
        st.caption(f"📦 {get_file_size(uploaded_pdf)}")
        
        # Extract text
        if st.session_state.pdf_text is None:
            with st.spinner("Reading PDF..."):
                text, pages = extract_pdf_text(uploaded_pdf)
                if text:
                    st.session_state.pdf_text = text
                    word_count = len(text.split())
                    st.info(f"📑 {pages} pages • {word_count:,} words")
        else:
            # Show existing PDF info
            word_count = len(st.session_state.pdf_text.split())
            st.info(f"📑 {word_count:,} words extracted")
        
        if st.button("🗑️ Remove PDF"):
            st.session_state.uploaded_pdf = None
            st.session_state.pdf_text = None
            st.rerun()
    
    st.divider()
    
    # Action buttons
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
    
    # Download chat
    if st.session_state.messages:
        st.markdown("### 📥 Export Chat")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                "📄 TXT",
                data=export_chat_markdown(),
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        with col2:
            st.download_button(
                "📊 JSON",
                data=export_chat_json(),
                file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    st.divider()
    
    # Model info
    with st.expander("🤖 About"):
        st.markdown("""
        **Model:** gemini-2.0-flash-exp
        
        **Features:**
        - 💬 Chat & Q&A
        - 📊 Excel & Data Analysis
        - 🔢 Math Problem Solving
        - 🖼️ Image analysis
        - 📄 PDF processing
        - 🧠 Context memory
        - ⚙️ Adjustable settings
        
        **Limits:**
        - Max image size: 4096x4096
        - PDF text extraction only
        - Context window: ~32K tokens
        """)

# Get AI response
def get_gemini_response(question, history, image=None, pdf_text=None):
    """Generate response from Gemini with improved context handling"""
    try:
        # Build context with better formatting
        context = ""
        
        # Add recent history (last 5 messages)
        if history:
            context += "=== Previous Conversation ===\n"
            for msg in history[-5:]:
                context += f"\nUser: {msg['user']}\n"
                context += f"Assistant: {msg['bot'][:200]}...\n" if len(msg['bot']) > 200 else f"Assistant: {msg['bot']}\n"
        
        # Add PDF context with smart truncation
        if pdf_text:
            max_pdf_chars = 8000
            truncated = pdf_text[:max_pdf_chars]
            context += f"\n\n=== Document Content ===\n{truncated}"
            if len(pdf_text) > max_pdf_chars:
                context += f"\n\n[Note: Document truncated. Total length: {len(pdf_text)} characters]"
        
        # Enhanced prompt for better formatting
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
        
        # Build final prompt
        if context:
            full_prompt = f"{formatting_instructions}\n\n{context}\n\n=== Current Question ===\nUser: {question}\nAssistant:"
        else:
            full_prompt = f"{formatting_instructions}\n\nUser: {question}\nAssistant:"
        
        # Configure generation
        generation_config = {
            "temperature": st.session_state.temperature,
            "max_output_tokens": st.session_state.max_tokens,
        }
        
        # Generate with appropriate input
        if image:
            response = model.generate_content(
                [full_prompt, image],
                generation_config=generation_config
            )
        else:
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
        
        return response.text
    
    except Exception as e:
        error = str(e)
        if "quota" in error.lower() or "resource_exhausted" in error.lower():
            return "⚠️ **API Quota Exceeded**\n\nYou've hit the rate limit. Please:\n- Wait a few minutes and try again\n- Check your quota at https://console.cloud.google.com\n- Consider upgrading your API plan"
        elif "safety" in error.lower():
            return "⚠️ **Content Filtered**\n\nThe response was blocked by safety filters. Try:\n- Rephrasing your question\n- Being more specific\n- Avoiding sensitive topics"
        elif "invalid_argument" in error.lower():
            return "⚠️ **Invalid Request**\n\nThere was an issue with the request format. This might be due to:\n- Image size too large\n- Unsupported file format\n- Context too long"
        else:
            return f"❌ **Error Occurred**\n\n```\n{error}\n```\n\nPlease try again or contact support if the issue persists."

# Main chat area
chat_container = st.container()

with chat_container:
    # Welcome message
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="✨"):
            st.markdown("""
            👋 **Welcome! I'm your Gemini AI Assistant**
            
            I can help you with:
            - 💬 **Conversations** - Ask me anything!
            - 📊 **Excel & Data** - Clean tables, formulas, calculations
            - 🔢 **Math Problems** - Step-by-step solutions
            - 🖼️ **Image Analysis** - Extract data, describe, analyze charts
            - 📄 **Document Processing** - Summarize PDFs, extract information
            - 🔍 **Research** - Find and explain complex topics
            
            **💡 Pro Tips for Best Results:**
            - For Excel/math: Ask for "markdown table format" or "Excel-ready format"
            - For calculations: Request "show all steps" or "detailed calculations"
            - Use the Quick Prompts in the sidebar for common tasks
            - Upload images/PDFs before asking questions about them
            
            Let's get started! 🚀
            """)
    
    # Display chat history
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["user"])
            
            # Show context used
            tags = []
            if msg.get("has_image"):
                tags.append("🖼️ Image")
            if msg.get("has_pdf"):
                tags.append("📄 PDF")
            
            if tags:
                st.caption(" + ".join(tags))
        
        with st.chat_message("assistant", avatar="✨"):
            st.markdown(msg["bot"])
            
            # Add copy button for tables/code
            if '|' in msg["bot"] or '```' in msg["bot"]:
                with st.expander("📋 Copy Raw Text"):
                    st.code(msg["bot"], language="markdown")
            
            # Add timestamp
            if "timestamp" in msg:
                try:
                    ts = datetime.fromisoformat(msg["timestamp"])
                    st.caption(f"🕒 {ts.strftime('%I:%M %p')}")
                except:
                    pass

# Chat input
if prompt := st.chat_input("💭 Message Gemini...", key="chat_input"):
    
    # Display user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        
        # Show what's being used
        context_tags = []
        if st.session_state.uploaded_image:
            context_tags.append("🖼️ Image")
        if st.session_state.uploaded_pdf:
            context_tags.append("📄 PDF")
        
        if context_tags:
            st.caption(" + ".join(context_tags))
    
    # Process image if uploaded
    image_data = None
    if st.session_state.uploaded_image:
        image_data = process_image(st.session_state.uploaded_image)
    
    # Generate response
    with st.chat_message("assistant", avatar="✨"):
        message_placeholder = st.empty()
        
        with st.spinner("🤔 Thinking..."):
            response = get_gemini_response(
                prompt,
                st.session_state.messages,
                image=image_data,
                pdf_text=st.session_state.pdf_text
            )
        
        # Simulate typing effect with smoother animation
        full_text = ""
        words = response.split()
        
        for i, word in enumerate(words):
            full_text += word + " "
            
            # Update every few words for smoother performance
            if i % 3 == 0 or i == len(words) - 1:
                message_placeholder.markdown(full_text + "▌")
                time.sleep(0.03)
        
        message_placeholder.markdown(response)
        
        # Add copy option for tables
        if '|' in response or '```' in response:
            with st.expander("📋 Copy Raw Text"):
                st.code(response, language="markdown")
        
        # Show timestamp
        st.caption(f"🕒 {datetime.now().strftime('%I:%M %p')}")
    
    # Save to history
    st.session_state.messages.append({
        "user": prompt,
        "bot": response,
        "has_image": st.session_state.uploaded_image is not None,
        "has_pdf": st.session_state.uploaded_pdf is not None,
        "timestamp": datetime.now().isoformat()
    })
    
    st.rerun()

# Footer with tips
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    with st.expander("💡 General Tips"):
        st.markdown("""
        - **Be specific** with your questions
        - **Upload files first** before asking about them
        - **Use context** from previous messages
        - **Clear chat** when changing topics
        - **Adjust temperature** for creativity vs accuracy
        """)

with col2:
    with st.expander("📊 Data & Excel"):
        st.markdown("""
        **For better formatting:**
        - Ask for "markdown table format"
        - Request "Excel-ready format"
        - Say "show calculations clearly"
        - Ask for "step-by-step with formulas"
        - Use "create a table with..."
        - Request "formatted for copying to Excel"
        - Try Quick Prompts in sidebar
        """)

with col3:
    with st.expander("📄 PDF Processing"):
        st.markdown("""
        **What you can ask:**
        - "Summarize this document"
        - "What are the key points?"
        - "Find information about [topic]"
        - "Explain section X"
        - "List all mentioned [items]"
        - "Compare sections Y and Z"
        """)

# Keyboard shortcuts info
with st.expander("⌨️ Pro Tips & Best Practices"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Efficiency:**
        - Use specific file names for context
        - Break complex questions into parts
        - Reference previous answers
        - Use Quick Prompts for common tasks
        - Upload before asking questions
        """)
    
    with col2:
        st.markdown("""
        **For Math/Excel:**
        - Always request "table format"
        - Ask for "step-by-step calculations"
        - Use "Excel-ready" in your prompt
        - Request "show all formulas"
        - Ask to "organize in columns"
        """)

# Footer
st.markdown("""
<div style='text-align: center; padding: 20px; opacity: 0.6;'>
    <p>Powered by Google Gemini 2.0 Flash • Built with Streamlit</p>
    <p style='font-size: 12px;'>⚡ Fast • 🧠 Smart • 📊 Excel-Ready • 🔒 Secure</p>
</div>
""", unsafe_allow_html=True)