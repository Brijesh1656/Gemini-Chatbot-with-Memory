from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import time
from PIL import Image
import PyPDF2
import io
import functools
import random
from datetime import datetime
import json
import hashlib

# Load environment variables
load_dotenv()

# Configuration constants
MAX_PDF_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5MB
MAX_INPUT_LENGTH = 10000
MAX_PDF_PAGES = 50
DEFAULT_CONTEXT_LENGTH = 10
MAX_CONTEXT_TOKENS = 8000

class ChatbotConfig:
    """Configuration management for the chatbot"""
    def __init__(self):
        self.api_key = self._get_api_key()
        self.validate_setup()
    
    def _get_api_key(self):
        """Get API key from various sources"""
        if hasattr(st, 'secrets') and 'GOOGLE_API_KEY' in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
        return os.getenv("GOOGLE_API_KEY")
    
    def validate_setup(self):
        """Validate configuration and show warnings"""
        issues = []
        
        if not self.api_key:
            issues.append("❌ Google API key missing")
            st.error("⚠️ GOOGLE_API_KEY not found! Please add it to Streamlit secrets or .env file")
            st.stop()
        
        if not hasattr(st, 'secrets'):
            issues.append("⚠️ Using .env file (consider Streamlit secrets for production)")
        
        if issues:
            with st.sidebar:
                with st.expander("⚠️ Setup Issues", expanded=False):
                    for issue in issues:
                        st.warning(issue)

class FileProcessor:
    """Handle file processing operations"""
    
    @staticmethod
    def validate_file_size(file, max_size, file_type):
        """Validate file size"""
        if file.size > max_size:
            st.error(f"{file_type} too large. Max size: {max_size / (1024*1024):.1f}MB")
            return False
        return True
    
    @staticmethod
    def extract_pdf_text(pdf_file):
        """Extract text from uploaded PDF file with page selection"""
        try:
            if not FileProcessor.validate_file_size(pdf_file, MAX_PDF_SIZE, "PDF"):
                return None
            
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            
            # For large PDFs, allow page selection
            if total_pages > 20:
                with st.sidebar:
                    st.info(f"📄 PDF has {total_pages} pages")
                    selected_pages = st.multiselect(
                        "Select pages to analyze:",
                        range(1, total_pages + 1),
                        default=list(range(1, min(6, total_pages + 1))),
                        help="Select specific pages to avoid token limits"
                    )
                    
                    if not selected_pages:
                        st.warning("Please select at least one page")
                        return None
                
                pages_to_process = [pdf_reader.pages[i-1] for i in selected_pages]
            else:
                pages_to_process = pdf_reader.pages
            
            text = ""
            for page in pages_to_process:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            # Limit text length to avoid token issues
            if len(text) > 15000:
                text = text[:15000] + "\n\n[... Content truncated due to length ...]"
            
            return text if text.strip() else None
            
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            return None
    
    @staticmethod
    def process_image(image_file):
        """Process uploaded image file"""
        try:
            if not FileProcessor.validate_file_size(image_file, MAX_IMAGE_SIZE, "Image"):
                return None
            
            image = Image.open(image_file)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Resize if too large (keep aspect ratio)
            max_dimension = 2048
            if max(image.size) > max_dimension:
                image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
            return None

class ConversationManager:
    """Manage conversation context and history"""
    
    @staticmethod
    def sanitize_input(text):
        """Basic input sanitization"""
        if len(text) > MAX_INPUT_LENGTH:
            st.warning(f"Input too long. Truncating to {MAX_INPUT_LENGTH:,} characters.")
            return text[:MAX_INPUT_LENGTH]
        return text.strip()
    
    @staticmethod
    def manage_context(messages, max_tokens=MAX_CONTEXT_TOKENS):
        """Smart context truncation based on estimated token count"""
        if not messages:
            return []
        
        context = []
        total_chars = 0
        
        # Estimate tokens (rough: 4 chars = 1 token)
        for msg in reversed(messages):
            msg_chars = len(msg['user']) + len(msg['bot'])
            if total_chars + msg_chars > max_tokens * 4:
                break
            context.insert(0, msg)
            total_chars += msg_chars
        
        return context
    
    @staticmethod
    def export_conversation(messages):
        """Export conversation with proper formatting"""
        if not messages:
            return "No conversation to export"
        
        export_text = f"Gemini Chatbot - Conversation Export\n"
        export_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_text += "=" * 60 + "\n\n"
        
        for i, msg in enumerate(messages, 1):
            export_text += f"Message {i} - {msg.get('timestamp', 'Unknown time')}:\n"
            export_text += f"👤 User: {msg['user']}\n"
            export_text += f"🤖 Assistant: {msg['bot']}\n"
            
            if msg.get('image_used'):
                export_text += "   📎 [Image was included in this message]\n"
            if msg.get('pdf_used'):
                export_text += "   📎 [PDF document was included in this message]\n"
            
            export_text += "\n" + "-" * 40 + "\n\n"
        
        return export_text

class GeminiAPI:
    """Handle Gemini API interactions"""
    
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.text_model = None
        self.vision_model = None
    
    def initialize_models(self, model_name, temperature=0.7):
        """Initialize Gemini models with configuration"""
        generation_config = {
            'temperature': temperature,
            'top_p': 0.95,
            'top_k': 64,
            'max_output_tokens': 8192,
        }
        
        self.text_model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )
        self.vision_model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )
    
    @staticmethod
    def retry_api_call(max_retries=3):
        """Decorator for API retry logic"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        error_msg = str(e).lower()
                        
                        if "quota" in error_msg or "limit" in error_msg:
                            st.error("⚠️ API quota exceeded. Please try again later.")
                            return None
                        elif "safety" in error_msg:
                            st.error("🛡️ Content filtered for safety reasons. Please rephrase your request.")
                            return None
                        elif attempt == max_retries - 1:
                            st.error(f"❌ Failed after {max_retries} attempts: {str(e)}")
                            return None
                        else:
                            wait_time = random.uniform(1, 3)
                            time.sleep(wait_time)
                
                return None
            return wrapper
        return decorator
    
    @retry_api_call(max_retries=3)
    def get_response(self, prompt, image=None):
        """Get response from Gemini with retry logic"""
        try:
            if image:
                response = self.vision_model.generate_content([prompt, image])
            else:
                response = self.text_model.generate_content(prompt)
            
            return response.text if response.text else "I apologize, but I couldn't generate a response. Please try again."
            
        except Exception as e:
            raise e  # Re-raise to be handled by retry decorator

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        "messages": [],
        "uploaded_image": None,
        "uploaded_pdf": None,
        "usage_stats": {
            "messages_sent": 0,
            "images_processed": 0,
            "pdfs_processed": 0,
            "session_start": datetime.now()
        },
        "settings": {
            "model": "gemini-2.5-flash",
            "temperature": 0.7,
            "context_length": DEFAULT_CONTEXT_LENGTH,
            "include_context": True
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def create_sidebar():
    """Create and manage the sidebar interface"""
    with st.sidebar:
        st.header("⚙️ Settings & Controls")
        
        # Model and behavior settings
        with st.expander("🧠 AI Configuration", expanded=True):
            model_choice = st.selectbox(
                "AI Model",
                ["gemini-2.5-flash", "gemini-1.5-pro"],
                index=0 if st.session_state.settings["model"] == "gemini-2.5-flash" else 1,
                help="Flash: Faster responses, Pro: More capable analysis"
            )
            
            temperature = st.slider(
                "Creativity Level", 
                0.0, 1.0, 
                st.session_state.settings["temperature"],
                help="Higher values = more creative responses"
            )
            
            context_length = st.slider(
                "Conversation Memory", 
                1, 20, 
                st.session_state.settings["context_length"],
                help="How many previous messages to remember"
            )
            
            include_context = st.checkbox(
                "Remember conversation history", 
                st.session_state.settings["include_context"]
            )
        
        # Update settings
        st.session_state.settings.update({
            "model": model_choice,
            "temperature": temperature,
            "context_length": context_length,
            "include_context": include_context
        })
        
        st.divider()
        
        # Quick action templates
        with st.expander("🚀 Quick Actions"):
            templates = {
                "📊 Analyze Data": "Analyze the data in this image/document and provide detailed insights with key findings",
                "📝 Summarize": "Provide a comprehensive summary of the main points and key information",
                "🔍 Extract Key Info": "Extract and list the most important information in an organized format",
                "🌐 Translate": "Translate any text in this image/document to English",
                "📋 Create Outline": "Create a detailed outline or structure based on this content",
                "❓ Q&A Mode": "I'll answer specific questions about this content - what would you like to know?"
            }
            
            for label, template in templates.items():
                if st.button(label, key=f"template_{label}"):
                    st.session_state["template_prompt"] = template
        
        st.divider()
        
        # File upload section
        st.subheader("📁 File Upload")
        
        uploaded_image = st.file_uploader(
            "Upload Image",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
            help=f"Max size: {MAX_IMAGE_SIZE/(1024*1024):.1f}MB"
        )
        
        uploaded_pdf = st.file_uploader(
            "Upload PDF Document",
            type=['pdf'],
            help=f"Max size: {MAX_PDF_SIZE/(1024*1024):.1f}MB"
        )
        
        # File status display
        if uploaded_image:
            st.success("🖼️ Image ready for analysis!")
            with st.expander("Image Preview"):
                st.image(uploaded_image, caption=uploaded_image.name, use_container_width=True)
        
        if uploaded_pdf:
            st.success("📄 PDF ready for analysis!")
            st.info(f"📋 File: {uploaded_pdf.name}")
        
        st.divider()
        
        # Chat management
        st.subheader("💬 Chat Management")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Clear Chat", help="Clear conversation history"):
                st.session_state["messages"] = []
                st.rerun()
        
        with col2:
            if st.button("📁 Clear Files", help="Remove uploaded files"):
                st.session_state["uploaded_image"] = None
                st.session_state["uploaded_pdf"] = None
                st.rerun()
        
        # Export functionality
        if st.session_state.get("messages"):
            export_data = ConversationManager.export_conversation(st.session_state["messages"])
            st.download_button(
                "📥 Export Chat",
                data=export_data,
                file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                help="Download conversation history"
            )
        
        st.divider()
        
        # Usage statistics
        with st.expander("📊 Session Statistics"):
            stats = st.session_state.usage_stats
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Messages", stats["messages_sent"])
                st.metric("Images", stats["images_processed"])
            with col2:
                st.metric("PDFs", stats["pdfs_processed"])
                session_time = datetime.now() - stats["session_start"]
                st.metric("Session", f"{session_time.seconds//60}min")
        
        # Return uploaded files
        return uploaded_image, uploaded_pdf

def display_chat_messages():
    """Display existing chat messages with enhanced formatting"""
    for i, msg in enumerate(st.session_state["messages"]):
        with st.chat_message("user"):
            st.markdown(msg["user"])
            
            # Show file attachments info
            attachments = []
            if msg.get("image_used"):
                attachments.append("🖼️ Image")
            if msg.get("pdf_used"):
                attachments.append("📄 PDF")
            
            if attachments:
                st.caption(f"📎 Attachments: {', '.join(attachments)}")
        
        with st.chat_message("assistant"):
            st.markdown(msg["bot"])
            
            # Show timestamp if available
            if "timestamp" in msg:
                st.caption(f"⏰ {msg['timestamp']}")

def process_user_input(prompt, gemini_api, uploaded_image, uploaded_pdf):
    """Process user input and generate response"""
    # Sanitize input
    prompt = ConversationManager.sanitize_input(prompt)
    
    # Handle template prompts
    if "template_prompt" in st.session_state:
        prompt = st.session_state["template_prompt"]
        del st.session_state["template_prompt"]
    
    # Process files
    image_to_use = None
    pdf_text = None
    
    if uploaded_image:
        image_to_use = FileProcessor.process_image(uploaded_image)
        if image_to_use:
            st.session_state.usage_stats["images_processed"] += 1
    
    if uploaded_pdf:
        pdf_text = FileProcessor.extract_pdf_text(uploaded_pdf)
        if pdf_text:
            st.session_state.usage_stats["pdfs_processed"] += 1
    
    # Build context
    context_messages = []
    if st.session_state.settings["include_context"]:
        context_messages = ConversationManager.manage_context(
            st.session_state["messages"][-st.session_state.settings["context_length"]:]
        )
    
    # Build full prompt
    full_prompt = ""
    
    # Add conversation context
    if context_messages:
        full_prompt += "Previous conversation context:\n"
        for msg in context_messages[-5:]:  # Limit to last 5 for context
            full_prompt += f"User: {msg['user']}\nAssistant: {msg['bot']}\n\n"
        full_prompt += "---\n\n"
    
    # Add PDF context
    if pdf_text:
        full_prompt += f"Document content:\n{pdf_text}\n\n---\n\n"
    
    # Add current question
    full_prompt += f"Current question: {prompt}"
    
    # Generate response
    with st.chat_message("assistant"):
        with st.status("Processing your request...", expanded=True) as status:
            if image_to_use:
                status.write("🖼️ Analyzing image...")
            if pdf_text:
                status.write("📄 Processing document...")
            status.write("🧠 Generating response...")
            
            response = gemini_api.get_response(full_prompt, image=image_to_use)
            
            if response:
                status.update(label="✅ Complete!", state="complete")
                
                # Display with typing effect
                message_placeholder = st.empty()
                displayed_response = ""
                
                # Split by sentences for better flow
                sentences = response.split('. ')
                for i, sentence in enumerate(sentences):
                    if i < len(sentences) - 1:
                        sentence += '. '
                    
                    for word in sentence.split():
                        displayed_response += word + " "
                        message_placeholder.markdown(displayed_response)
                        time.sleep(0.02)
                
                # Store message with metadata
                message_data = {
                    "user": prompt,
                    "bot": response,
                    "image_used": uploaded_image is not None,
                    "pdf_used": uploaded_pdf is not None,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
                
                st.session_state["messages"].append(message_data)
                st.session_state.usage_stats["messages_sent"] += 1
                
            else:
                status.update(label="❌ Failed", state="error")
                st.error("Failed to generate response. Please try again.")

def main():
    """Main application function"""
    # Page configuration
    st.set_page_config(
        page_title="Enhanced Gemini AI Chatbot",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize configuration and session state
    config = ChatbotConfig()
    initialize_session_state()
    
    # Initialize Gemini API
    gemini_api = GeminiAPI(config.api_key)
    gemini_api.initialize_models(
        st.session_state.settings["model"],
        st.session_state.settings["temperature"]
    )
    
    # Header
    st.title("🤖 Enhanced Gemini AI Chatbot")
    st.markdown("*Advanced AI assistant with image analysis, document processing, and intelligent conversation management*")
    
    # Create sidebar and get uploaded files
    uploaded_image, uploaded_pdf = create_sidebar()
    
    # Update session state with uploaded files
    if uploaded_image:
        st.session_state["uploaded_image"] = uploaded_image
    if uploaded_pdf:
        st.session_state["uploaded_pdf"] = uploaded_pdf
    
    # Display chat history
    display_chat_messages()
    
    # Handle user input
    if prompt := st.chat_input("Type your message... (Upload files in sidebar for analysis)"):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
            
            # Show active files
            active_files = []
            if st.session_state.get("uploaded_image"):
                active_files.append("🖼️ Image")
            if st.session_state.get("uploaded_pdf"):
                active_files.append("📄 PDF")
            
            if active_files:
                st.caption(f"📎 Using: {', '.join(active_files)}")
        
        # Process and respond
        process_user_input(
            prompt, 
            gemini_api, 
            st.session_state.get("uploaded_image"), 
            st.session_state.get("uploaded_pdf")
        )
    
    # Instructions footer
    st.markdown("---")
    with st.expander("📖 How to Use This Enhanced Chatbot", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🖼️ **Image Analysis**
            - Upload images in sidebar
            - Ask about visual content, charts, diagrams
            - Extract text from images (OCR)
            - Analyze data visualizations
            
            ### 📄 **PDF Processing**
            - Upload documents up to 10MB
            - Select specific pages for large files
            - Ask questions about content
            - Generate summaries and insights
            """)
        
        with col2:
            st.markdown("""
            ### ⚙️ **Advanced Features**
            - **Smart Context**: Remembers conversation flow
            - **Quick Actions**: Pre-built prompts for common tasks
            - **Model Selection**: Choose between speed vs capability
            - **Export Options**: Download conversation history
            
            ### 💡 **Pro Tips**
            - Use specific questions for better results
            - Combine images and PDFs for comprehensive analysis
            - Adjust creativity level in settings
            - Use Quick Actions for structured responses
            """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "*🚀 Powered by Google Gemini AI | Built with Streamlit | "
        f"Model: {st.session_state.settings['model']} | "
        f"Messages: {st.session_state.usage_stats['messages_sent']}*"
    )

if __name__ == "__main__":
    main()
