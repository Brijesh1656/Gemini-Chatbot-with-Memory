# ✨ Gemini AI Assistant

A powerful, modern Streamlit application that brings Google's Gemini 2.0 Flash to life with support for text conversations, image analysis, and PDF document processing.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🌟 Features

### 💬 Intelligent Chat
- Context-aware conversations with memory
- Natural language processing
- Typing animation effects
- Chat history export

### 🖼️ Image Analysis
- Upload and analyze images (PNG, JPG, JPEG, WEBP)
- Visual question answering
- Object detection and description
- Text extraction from images

### 📄 PDF Processing
- Multi-page PDF support
- Automatic text extraction
- Document summarization
- Contextual Q&A about uploaded documents

### 🎨 Modern UI
- Beautiful dark theme interface
- Responsive design
- Real-time session statistics
- File size and page count indicators
- Smooth animations and transitions

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/gemini-ai-assistant.git
cd gemini-ai-assistant
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up your API key**

Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_api_key_here
```

Or use Streamlit secrets (`.streamlit/secrets.toml`):
```toml
GOOGLE_API_KEY = "your_api_key_here"
```

4. **Run the application**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📦 Dependencies

```txt
streamlit>=1.28.0
google-generativeai>=0.3.0
python-dotenv>=1.0.0
Pillow>=10.0.0
PyPDF2>=3.0.0
```

Create a `requirements.txt` file with the above content.

## 🎯 Usage

### Basic Chat
1. Simply type your message in the chat input
2. Press Enter to send
3. View AI responses in real-time

### Image Analysis
1. Click **"Upload Image"** in the sidebar
2. Select an image file
3. Ask questions about the image:
   - "Describe this image"
   - "What objects do you see?"
   - "Extract text from this image"

### PDF Processing
1. Click **"Upload PDF"** in the sidebar
2. Wait for automatic text extraction
3. Ask questions about the document:
   - "Summarize this document"
   - "What are the key points?"
   - "Find information about [topic]"

### Session Management
- **Clear Chat**: Remove conversation history
- **Reset All**: Clear everything including uploaded files
- **Download Chat**: Export conversation as text file

## 🔧 Configuration

### API Configuration
The app automatically looks for your API key in:
1. Streamlit secrets (production)
2. `.env` file (development)

### Model Settings
Currently using `gemini-2.0-flash-exp`. To change:
```python
model = genai.GenerativeModel("your-model-name")
```

### Context Window
By default, the app keeps the last 5 messages in context. Adjust in the code:
```python
for msg in history[-5:]:  # Change 5 to your preferred number
```

## 📊 Features in Detail

### Session Statistics
- Real-time message count
- Session duration tracking
- File upload indicators

### Error Handling
- API quota exceeded warnings
- Safety filter notifications
- File processing error messages
- Graceful degradation

### File Support
- **Images**: PNG, JPG, JPEG, WEBP
- **Documents**: PDF with multi-page support
- **Size Display**: Human-readable file sizes
- **Preview**: Image thumbnails in sidebar

## 🎨 Customization

### Theme Colors
Edit the CSS in the `st.markdown()` section:
```python
# Main accent color (purple)
color: #8b5cf6;  # Change to your preferred color

# Gradient backgrounds
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Layout
Modify the `st.set_page_config()` settings:
```python
st.set_page_config(
    page_title="Your Title",
    page_icon="🎯",
    layout="wide",  # or "centered"
    initial_sidebar_state="expanded"  # or "collapsed"
)
```

## 🐛 Troubleshooting

### API Key Issues
```
⚠️ GOOGLE_API_KEY not found!
```
**Solution**: Ensure your `.env` file exists and contains the correct API key.

### Quota Exceeded
```
⚠️ API quota exceeded
```
**Solution**: Wait a few minutes or upgrade your API plan.

### PDF Reading Errors
```
Error reading PDF: ...
```
**Solution**: Ensure the PDF is not corrupted or password-protected.

### Image Processing Errors
**Solution**: Check that the image format is supported and not corrupted.

## 📝 Example Prompts

### General Chat
- "Explain quantum computing in simple terms"
- "Write a haiku about spring"
- "What's the capital of France?"

### Image Analysis
- "What's in this image?"
- "Describe the colors and composition"
- "Read any text visible in this image"

### PDF Questions
- "Summarize the main points of this document"
- "What does section 3 say about [topic]?"
- "Create a bullet-point summary"

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Gemini API for the AI capabilities
- Streamlit for the amazing web framework
- The open-source community for the dependencies

## 👨‍💻 Developer

**Brijesh Singh**
- 🎓 BBA (Business Analytics) Student at Roots Collegium, Osmania University
- 📍 Hyderabad, India
- 📧 brijesh7146@gmail.com
- 💼 [LinkedIn](https://linkedin.com/in/brijesh-singh-b84275307)
- 🐙 [GitHub](https://github.com/Brijesh1656)

Passionate about leveraging data and machine learning to deliver business insights and drive decision-making. Experienced in Python, SQL, and data visualization.

### Other Projects
- **[Stock Analysis Pro](https://github.com/Brijesh1656)** - Full-stack stock analysis with AI-powered chart pattern recognition
- More projects on my [GitHub profile](https://github.com/Brijesh1656)

## 📧 Contact & Support

For questions, feedback, or collaboration:
- 📮 Email: brijesh7146@gmail.com
- 💬 Open an issue on GitHub
- 🔗 Connect on [LinkedIn](https://linkedin.com/in/brijesh-singh-b84275307)

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Custom system prompts
- [ ] Conversation branches
- [ ] Export to multiple formats
- [ ] Video analysis support
- [ ] Real-time collaboration

---

**Built with ❤️ using Streamlit and Google Gemini**
