from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import time
from PIL import Image
import PyPDF2
import io

# Load environment variables
load_dotenv()

# Get API key from Streamlit secrets or .env
if hasattr(st, 'secrets') and 'GOOGLE_API_KEY' in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ GOOGLE_API_KEY not found! Please add it to Streamlit secrets")
    st.stop()

genai.configure(api_key=api_key)

# Initialize Gemini model (using gemini-pro-vision for image support)
text_model = genai.GenerativeModel("gemini-2.5-flash")
vision_model = genai.GenerativeModel("gemini-2.5-flash")

# Streamlit page config
st.set_page_config(page_title="Enhanced Gemini Chatbot", layout="wide")
st.title("🤖 Enhanced Gemini Chatbot - Text, Images & PDFs")

# Helper function to extract text from PDF
def extract_pdf_text(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

# Helper function to process image
def process_image(image_file):
    """Process uploaded image file"""
    try:
        image = Image.open(image_file)
        return image
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    # File upload section
    st.subheader("📁 Upload Files")
    
    # Image upload
    uploaded_image = st.file_uploader(
        "Upload an image",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
        help="Upload an image for analysis"
    )
    
    # PDF upload
    uploaded_pdf = st.file_uploader(
        "Upload a PDF",
        type=['pdf'],
        help="Upload a PDF document for text extraction"
    )
    
    st.divider()
    
    # Chat controls
    if st.button("🧹 Clear Chat"):
        st.session_state["messages"] = []
        st.session_state["uploaded_image"] = None
        st.session_state["uploaded_pdf"] = None
        st.rerun()
    
    st.download_button(
        "📥 Download Chat History",
        data="\n".join(
            [f"You: {m['user']}\nBot: {m['bot']}" for m in st.session_state.get("messages", [])]
        ),
        file_name="chat_history.txt",
    )
    
    st.divider()
    
    # Current uploads display
    if uploaded_image:
        st.success("🖼️ Image uploaded!")
        st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)
    
    if uploaded_pdf:
        st.success("📄 PDF uploaded!")
        st.info(f"PDF: {uploaded_pdf.name}")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "uploaded_image" not in st.session_state:
    st.session_state["uploaded_image"] = None

if "uploaded_pdf" not in st.session_state:
    st.session_state["uploaded_pdf"] = None

# Store uploaded files in session state
if uploaded_image:
    st.session_state["uploaded_image"] = uploaded_image

if uploaded_pdf:
    st.session_state["uploaded_pdf"] = uploaded_pdf

# Function to get Gemini response
def get_gemini_response(question, history, image=None, pdf_text=None):
    """Get response from Gemini with optional image and PDF context"""
    try:
        # Build conversation context
        conversation = "\n".join(
            [f"You: {msg['user']}\nBot: {msg['bot']}" for msg in history[-10:]]  # Limit to last 10 messages
        )
        
        # Build the full prompt
        full_prompt = f"{conversation}\n"
        
        # Add PDF context if available
        if pdf_text:
            full_prompt += f"\n[PDF Content]: {pdf_text[:3000]}...\n"  # Limit PDF text to avoid token limits
        
        full_prompt += f"You: {question}\nBot:"
        
        # Generate response based on whether we have an image
        if image:
            # Use vision model for image analysis
            response = vision_model.generate_content([full_prompt, image])
        else:
            # Use text model for text-only queries
            response = text_model.generate_content(full_prompt)
        
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}. Please try again."

# Display existing chat messages
for msg in st.session_state["messages"]:
    with st.chat_message("user"):
        st.markdown(msg["user"])
        # Show uploaded files info if they were part of the message
        if "image_used" in msg and msg["image_used"]:
            st.info("🖼️ Image was included with this message")
        if "pdf_used" in msg and msg["pdf_used"]:
            st.info("📄 PDF was included with this message")
    
    with st.chat_message("assistant"):
        st.markdown(msg["bot"])

# User input
if prompt := st.chat_input("Type your message... (Upload files in sidebar first)"):
    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)
        
        # Show what files are being used
        files_used = []
        if st.session_state["uploaded_image"]:
            st.info("🖼️ Using uploaded image")
            files_used.append("image")
        if st.session_state["uploaded_pdf"]:
            st.info("📄 Using uploaded PDF")
            files_used.append("pdf")
    
    # Process uploaded files
    image_to_use = None
    pdf_text = None
    
    if st.session_state["uploaded_image"]:
        image_to_use = process_image(st.session_state["uploaded_image"])
    
    if st.session_state["uploaded_pdf"]:
        pdf_text = extract_pdf_text(st.session_state["uploaded_pdf"])
    
    # Generate bot response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 Analyzing...")
        
        # Get response from Gemini
        response = get_gemini_response(
            prompt, 
            st.session_state["messages"], 
            image=image_to_use,
            pdf_text=pdf_text
        )
        
        # Display response with typing effect
        full_response = ""
        for word in response.split():
            full_response += word + " "
            message_placeholder.markdown(full_response)
            time.sleep(0.03)
    
    # Save to chat history with file usage info
    message_data = {
        "user": prompt,
        "bot": full_response.strip(),
        "image_used": st.session_state["uploaded_image"] is not None,
        "pdf_used": st.session_state["uploaded_pdf"] is not None
    }
    st.session_state["messages"].append(message_data)

# Instructions
st.markdown("---")
with st.expander("📖 How to Use"):
    st.markdown("""
    **🖼️ For Images:**
    1. Upload an image in the sidebar
    2. Ask questions like:
       - "What do you see in this image?"
       - "Analyze this chart/graph"
       - "What text is in this image?"
       - "Explain this diagram"
    
    **📄 For PDFs:**
    1. Upload a PDF in the sidebar
    2. Ask questions like:
       - "Summarize this document"
       - "What are the key points?"
       - "Answer questions about the content"
       - "Find specific information in the PDF"
    
    **💡 Pro Tips:**
    - You can use both image and PDF together
    - Clear chat to remove uploaded files
    - Files stay uploaded until you clear or upload new ones
    - Be specific in your questions for better results
    """)

st.markdown("*Powered by Google Gemini AI with Vision | Built with Streamlit*")