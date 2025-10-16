from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import time
from PIL import Image
import PyPDF2
from datetime import datetime

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
    """Extract text from PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text, len(pdf_reader.pages)
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None, 0

def process_image(image_file):
    """Process uploaded image"""
    try:
        return Image.open(image_file)
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
    
    # File uploads
    st.markdown("### 📁 Upload Files")
    
    # Image upload
    uploaded_image = st.file_uploader(
        "🖼️ Upload Image",
        type=['png', 'jpg', 'jpeg', 'webp'],
        help="PNG, JPG, JPEG, WEBP supported"
    )
    
    if uploaded_image:
        st.session_state.uploaded_image = uploaded_image
        st.success(f"✅ {uploaded_image.name}")
        st.caption(f"📦 {get_file_size(uploaded_image)}")
        
        img = Image.open(uploaded_image)
        st.image(img, use_container_width=True)
        
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
                    st.info(f"📑 {pages} pages extracted")
        
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
        chat_export = f"Gemini AI Chat\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n{'='*50}\n\n"
        for i, msg in enumerate(st.session_state.messages, 1):
            chat_export += f"[{i}] You: {msg['user']}\n"
            chat_export += f"    AI: {msg['bot']}\n\n"
        
        st.download_button(
            "📥 Download Chat",
            data=chat_export,
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.divider()
    
    # Model info
    with st.expander("🤖 About"):
        st.markdown("""
        **Model:** gemini-2.0-flash-exp
        
        **Features:**
        - 💬 Chat & Q&A
        - 🖼️ Image analysis
        - 📄 PDF processing
        - 🧠 Context memory
        """)

# Get AI response
def get_gemini_response(question, history, image=None, pdf_text=None):
    """Generate response from Gemini"""
    try:
        # Build context
        context = ""
        
        # Add recent history (last 5 messages)
        if history:
            context += "Previous conversation:\n"
            for msg in history[-5:]:
                context += f"User: {msg['user']}\nAI: {msg['bot']}\n\n"
        
        # Add PDF context
        if pdf_text:
            context += f"\n[Document content]\n{pdf_text[:3000]}...\n\n"
        
        # Build prompt
        full_prompt = context + f"User: {question}\nAI:"
        
        # Generate
        if image:
            response = model.generate_content([full_prompt, image])
        else:
            response = model.generate_content(full_prompt)
        
        return response.text
    
    except Exception as e:
        error = str(e)
        if "quota" in error.lower():
            return "⚠️ API quota exceeded. Please check your quota or wait a few minutes."
        elif "safety" in error.lower():
            return "⚠️ Response blocked by safety filters. Try rephrasing your question."
        else:
            return f"❌ Error: {error}"

# Main chat area
chat_container = st.container()

with chat_container:
    # Welcome message
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="✨"):
            st.markdown("""
            👋 **Welcome!**
            
            I can help you with:
            - 💬 Answering questions
            - 🖼️ Analyzing images
            - 📄 Reading PDFs
            - 🔍 Finding information
            
            Upload files in the sidebar or start chatting!
            """)
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["user"])
            
            # Show context used
            tags = []
            if msg.get("has_image"):
                tags.append("🖼️")
            if msg.get("has_pdf"):
                tags.append("📄")
            
            if tags:
                st.caption(" ".join(tags))
        
        with st.chat_message("assistant", avatar="✨"):
            st.markdown(msg["bot"])

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
        with st.spinner("Thinking..."):
            response = get_gemini_response(
                prompt,
                st.session_state.messages,
                image=image_data,
                pdf_text=st.session_state.pdf_text
            )
        
        # Simulate typing effect
        placeholder = st.empty()
        full_text = ""
        
        for chunk in response.split():
            full_text += chunk + " "
            placeholder.markdown(full_text + "▌")
            time.sleep(0.02)
        
        placeholder.markdown(response)
    
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
    with st.expander("💡 Tips"):
        st.markdown("""
        - Be specific with questions
        - Upload files before asking
        - Use context from PDFs
        - Clear chat for new topics
        """)

with col2:
    with st.expander("🖼️ Image Tips"):
        st.markdown("""
        - "Describe this image"
        - "What text is in this?"
        - "Analyze this chart"
        - "What objects do you see?"
        """)

with col3:
    with st.expander("📄 PDF Tips"):
        st.markdown("""
        - "Summarize this"
        - "What are key points?"
        - "Find info about X"
        - "Explain section Y"
        """)

# Footer
st.markdown("""
<div style='text-align: center; padding: 20px; opacity: 0.6;'>
    <p>Powered by Google Gemini 2.0 Flash • Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
