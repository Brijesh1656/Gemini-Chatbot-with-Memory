from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import time
from PIL import Image
import PyPDF2
import io
from datetime import datetime

# Load environment variables
load_dotenv()

# Get API key from Streamlit secrets or .env
if hasattr(st, 'secrets') and 'GOOGLE_API_KEY' in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ GOOGLE_API_KEY not found! Please add it to Streamlit secrets or .env file")
    st.stop()

genai.configure(api_key=api_key)

# Initialize Gemini models
text_model = genai.GenerativeModel("gemini-2.5-flash")
vision_model = genai.GenerativeModel("gemini-2.5-flash")

# Enhanced page config with custom theme
st.set_page_config(
    page_title="Gemini AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium UI/UX
st.markdown("""
<style>
    /* Main app styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Chat container */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    
    /* User message */
    [data-testid="stChatMessageContent"] {
        font-size: 16px;
        line-height: 1.6;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Headers */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        font-size: 3rem !important;
        text-align: center;
        margin-bottom: 0;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
        padding: 12px;
        transition: all 0.3s ease;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 15px;
        border: 2px dashed rgba(255, 255, 255, 0.3);
    }
    
    /* Input box */
    .stChatInputContainer {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 25px;
        padding: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    /* Success/Info messages */
    .stAlert {
        border-radius: 10px;
        border: none;
        backdrop-filter: blur(10px);
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 700;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* Divider */
    hr {
        margin: 30px 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    /* Animation for new messages */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .stChatMessage {
        animation: slideIn 0.3s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def extract_pdf_text(pdf_file):
    """Extract text from uploaded PDF file with progress indication"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        total_pages = len(pdf_reader.pages)
        
        for i, page in enumerate(pdf_reader.pages):
            text += page.extract_text() + "\n"
        
        return text, total_pages
    except Exception as e:
        st.error(f"❌ Error reading PDF: {str(e)}")
        return None, 0

def process_image(image_file):
    """Process uploaded image file"""
    try:
        image = Image.open(image_file)
        return image
    except Exception as e:
        st.error(f"❌ Error processing image: {str(e)}")
        return None

def get_file_size(file):
    """Get file size in human-readable format"""
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "uploaded_image" not in st.session_state:
    st.session_state["uploaded_image"] = None
if "uploaded_pdf" not in st.session_state:
    st.session_state["uploaded_pdf"] = None
if "pdf_text" not in st.session_state:
    st.session_state["pdf_text"] = None
if "total_tokens" not in st.session_state:
    st.session_state["total_tokens"] = 0
if "session_start" not in st.session_state:
    st.session_state["session_start"] = datetime.now()

# Header
st.title("✨ Gemini AI Assistant")
st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.8); font-size: 18px; margin-top: -20px;'>Your intelligent companion for text, images, and documents</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎛️ Control Center")
    
    # Session stats
    with st.expander("📊 Session Statistics", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", len(st.session_state["messages"]))
        with col2:
            duration = datetime.now() - st.session_state["session_start"]
            st.metric("Duration", f"{duration.seconds // 60}m")
    
    st.markdown("---")
    
    # File upload section
    st.markdown("### 📁 Upload Files")
    
    # Image upload with preview
    uploaded_image = st.file_uploader(
        "🖼️ Upload Image",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
        help="Supported formats: PNG, JPG, JPEG, GIF, BMP, WEBP"
    )
    
    if uploaded_image:
        st.session_state["uploaded_image"] = uploaded_image
        with st.container():
            st.success(f"✅ {uploaded_image.name}")
            st.caption(f"Size: {get_file_size(uploaded_image)}")
            img = Image.open(uploaded_image)
            st.image(img, use_container_width=True)
            if st.button("🗑️ Remove Image"):
                st.session_state["uploaded_image"] = None
                st.rerun()
    
    st.markdown("")
    
    # PDF upload with info
    uploaded_pdf = st.file_uploader(
        "📄 Upload PDF",
        type=['pdf'],
        help="Upload PDF documents for AI analysis"
    )
    
    if uploaded_pdf:
        st.session_state["uploaded_pdf"] = uploaded_pdf
        with st.container():
            st.success(f"✅ {uploaded_pdf.name}")
            st.caption(f"Size: {get_file_size(uploaded_pdf)}")
            
            # Extract PDF text on upload
            if st.session_state["pdf_text"] is None:
                with st.spinner("📖 Reading PDF..."):
                    text, pages = extract_pdf_text(uploaded_pdf)
                    if text:
                        st.session_state["pdf_text"] = text
                        st.info(f"📑 {pages} pages extracted")
            
            if st.button("🗑️ Remove PDF"):
                st.session_state["uploaded_pdf"] = None
                st.session_state["pdf_text"] = None
                st.rerun()
    
    st.markdown("---")
    
    # Action buttons
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Clear Chat"):
            st.session_state["messages"] = []
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset All"):
            st.session_state["messages"] = []
            st.session_state["uploaded_image"] = None
            st.session_state["uploaded_pdf"] = None
            st.session_state["pdf_text"] = None
            st.session_state["session_start"] = datetime.now()
            st.rerun()
    
    # Download chat history
    if st.session_state["messages"]:
        chat_history = f"Gemini AI Chat History\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}\n\n"
        for i, msg in enumerate(st.session_state["messages"], 1):
            chat_history += f"Message {i}\n"
            chat_history += f"You: {msg['user']}\n"
            chat_history += f"AI: {msg['bot']}\n"
            chat_history += "-" * 50 + "\n\n"
        
        st.download_button(
            "📥 Download History",
            data=chat_history,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Model info
    with st.expander("🤖 Model Info"):
        st.markdown("""
        **Current Model:**  
        `gemini-2.5-flash`
        
        **Capabilities:**
        - 💬 Natural conversation
        - 🖼️ Image analysis
        - 📄 Document processing
        - 🧠 Context awareness
        """)

# Function to get Gemini response with enhanced error handling
def get_gemini_response(question, history, image=None, pdf_text=None):
    """Get response from Gemini with optional image and PDF context"""
    try:
        # Build conversation context
        conversation = ""
        for msg in history[-10:]:  # Last 10 messages for context
            conversation += f"User: {msg['user']}\nAssistant: {msg['bot']}\n\n"
        
        # Build the full prompt
        full_prompt = ""
        
        # Add PDF context if available
        if pdf_text:
            full_prompt += f"[Document Context]\n{pdf_text[:5000]}\n\n"
        
        full_prompt += f"{conversation}User: {question}\nAssistant:"
        
        # Generate response
        if image:
            response = vision_model.generate_content([full_prompt, image])
        else:
            response = text_model.generate_content(full_prompt)
        
        return response.text
    
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower():
            return "⚠️ API quota exceeded. Please check your Google AI Studio quota or try again later."
        elif "safety" in error_msg.lower():
            return "⚠️ Content filtered by safety settings. Please rephrase your request."
        else:
            return f"❌ Error: {error_msg}\n\nPlease try again or rephrase your question."

# Main chat interface
chat_container = st.container()

with chat_container:
    # Welcome message for new sessions
    if not st.session_state["messages"]:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("""
            👋 **Welcome to Gemini AI Assistant!**
            
            I can help you with:
            - 💬 Natural conversations and questions
            - 🖼️ Analyzing images and visual content
            - 📄 Understanding and summarizing PDFs
            - 🔍 Extracting insights from documents
            
            **Get started:** Upload a file in the sidebar or just start chatting!
            """)
    
    # Display chat history
    for msg in st.session_state["messages"]:
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["user"])
            
            # Show context indicators
            indicators = []
            if msg.get("image_used"):
                indicators.append("🖼️ Image")
            if msg.get("pdf_used"):
                indicators.append("📄 PDF")
            
            if indicators:
                st.caption(f"Context: {' + '.join(indicators)}")
        
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(msg["bot"])

# Chat input
if prompt := st.chat_input("💭 Ask me anything... (Upload files first if needed)", key="chat_input"):
    # Display user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        
        # Show active context
        context_items = []
        if st.session_state["uploaded_image"]:
            context_items.append("🖼️ Image attached")
        if st.session_state["uploaded_pdf"]:
            context_items.append("📄 PDF attached")
        
        if context_items:
            st.caption(f"Using: {' + '.join(context_items)}")
    
    # Process files
    image_to_use = None
    if st.session_state["uploaded_image"]:
        image_to_use = process_image(st.session_state["uploaded_image"])
    
    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🤔 Thinking..."):
            response = get_gemini_response(
                prompt,
                st.session_state["messages"],
                image=image_to_use,
                pdf_text=st.session_state.get("pdf_text")
            )
        
        # Stream response
        message_placeholder = st.empty()
        full_response = ""
        
        words = response.split()
        for i, word in enumerate(words):
            full_response += word + " "
            if i % 3 == 0:  # Update every 3 words for smoother animation
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.02)
        
        message_placeholder.markdown(full_response)
    
    # Save to history
    st.session_state["messages"].append({
        "user": prompt,
        "bot": full_response.strip(),
        "image_used": st.session_state["uploaded_image"] is not None,
        "pdf_used": st.session_state["uploaded_pdf"] is not None,
        "timestamp": datetime.now().isoformat()
    })
    
    st.rerun()

# Footer with instructions
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    with st.expander("🖼️ Image Analysis"):
        st.markdown("""
        **What you can do:**
        - Describe images
        - Extract text (OCR)
        - Analyze charts/graphs
        - Identify objects
        - Get creative descriptions
        
        **Example questions:**
        - "What's in this image?"
        - "Read the text from this screenshot"
        - "Analyze this chart"
        """)

with col2:
    with st.expander("📄 PDF Processing"):
        st.markdown("""
        **What you can do:**
        - Summarize documents
        - Extract key points
        - Answer specific questions
        - Find information
        - Analyze content
        
        **Example questions:**
        - "Summarize this document"
        - "What are the main findings?"
        - "Find information about..."
        """)

with col3:
    with st.expander("💡 Pro Tips"):
        st.markdown("""
        **Get better results:**
        - Be specific in questions
        - Upload files before asking
        - Use both image + PDF together
        - Clear chat for new topics
        - Download history to save
        
        **Shortcuts:**
        - Press Enter to send
        - Use Clear Chat to reset
        - Download anytime
        """)

# Footer
st.markdown("""
<div style='text-align: center; padding: 20px; color: rgba(255,255,255,0.6);'>
    <p style='margin: 0;'>⚡ Powered by <strong>Google Gemini 2.5 Flash</strong></p>
    <p style='margin: 5px 0 0 0; font-size: 14px;'>Built with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
