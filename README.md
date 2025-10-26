# GeminiFlow

# ✨ GeminiFlow

> Multi-Modal AI Chat Platform with Excel Export & Document Processing

A powerful AI assistant powered by Google's Gemini 2.0 Flash that combines conversational AI with advanced document processing, image analysis, and automatic Excel export capabilities for data-driven workflows.

## 🚀 Live Demo
Check out the live app here 👉 [GeminiFlow on Streamlit](https://geminiflow.streamlit.app/)

---

## ✨ Features

### 💬 Advanced Chat Interface
- **Multi-Turn Conversations**: Context-aware responses with conversation history
- **Streaming Responses**: Real-time text generation with typing animation
- **Quick Prompts**: Pre-configured prompts for common tasks
- **Session Management**: Track conversation duration and message count
- **Smart Context Handling**: Maintains up to 5 previous messages for context

### 📊 Excel Auto-Export
- **Automatic Table Detection**: Identifies markdown tables in responses
- **One-Click Excel Download**: Instant conversion to formatted .xlsx files
- **Smart Formatting**: Auto-adjusts column widths based on content
- **Professional Styling**: Clean, organized spreadsheets ready for business use
- **Raw Data Access**: Copy markdown tables directly

### 🖼️ Image Analysis
- **Multi-Format Support**: PNG, JPG, JPEG, WebP, GIF
- **Smart Resizing**: Automatic compression for large images (max 4096px)
- **Visual Preview**: In-sidebar image display with dimensions
- **Data Extraction**: Extract text, numbers, and patterns from images
- **Chart Analysis**: Understand graphs, diagrams, and visual data

### 📄 PDF Processing
- **Multi-Page Support**: Handle documents of any length
- **Progress Tracking**: Real-time extraction progress for large files
- **Smart Truncation**: Optimizes long documents for AI processing (8000 chars)
- **Word Count Stats**: See pages and word count instantly
- **Text Extraction**: Pull content from complex PDFs

### ⚙️ Customization Options
- **Temperature Control**: Adjust creativity (0.0-1.0)
- **Token Limits**: Control response length (256-8192 tokens)
- **Model Settings**: Fine-tune AI behavior
- **Export Options**: JSON, Markdown, Excel formats

### 📥 Export & Sharing
- **Chat History (Markdown)**: Complete conversation in .md format
- **JSON Export**: Structured data with timestamps
- **Excel Tables**: Individual table downloads
- **Professional Formatting**: Ready-to-share reports

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Google API Key (Gemini 2.0)
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Brijesh1656/GeminiFlow.git
cd GeminiFlow
```

2. **Install required packages**
```bash
pip install streamlit google-generativeai python-dotenv Pillow PyPDF2 pandas openpyxl
```

3. **Set up your API key**

Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

Or use Streamlit secrets (`.streamlit/secrets.toml`):
```toml
GOOGLE_API_KEY = "your_google_gemini_api_key_here"
```

Get your API key: [Google AI Studio](https://makersuite.google.com/app/apikey)

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

---

## 📖 Usage Guide

### 1. Start Chatting
- Type your message in the chat input at the bottom
- Press Enter or click Send
- Watch AI respond in real-time with streaming text

### 2. Upload Files (Optional)
- **Images**: Use sidebar to upload PNG, JPG, GIF, WebP
- **PDFs**: Upload documents for summarization or analysis
- Files attach automatically to your next message

### 3. Use Quick Prompts
- Click Quick Prompts in sidebar for templates
- Customize the prompt with your specific data
- Great for Excel tables, math problems, analysis

### 4. Get Excel Tables
- Ask for data in "markdown table format"
- AI generates formatted tables automatically
- Click "📥 Excel" button below response
- Download instantly as .xlsx file

### 5. Adjust Settings
- **Temperature**: Higher = more creative, Lower = more focused
- **Max Tokens**: Control response length
- Experiment to find your perfect settings

### 6. Export Your Work
- **Chat History**: Download full conversation (Markdown/JSON)
- **Individual Tables**: Excel files for each data table
- **Raw Data**: Copy markdown for other tools

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Streamlit** | Web application framework and UI |
| **Google Gemini 2.0** | Advanced multi-modal AI model |
| **PyPDF2** | PDF text extraction and processing |
| **Pillow (PIL)** | Image processing and optimization |
| **Pandas** | Data manipulation and DataFrame creation |
| **OpenPyXL** | Excel file generation and formatting |
| **Python-dotenv** | Environment variable management |

---

## 🎯 Use Cases

### 📊 Data Analysis
- Convert text data to Excel-ready tables
- Extract numerical data from images/PDFs
- Generate formatted financial reports

### 🔢 Problem Solving
- Step-by-step math solutions with tables
- Physics/chemistry calculations
- Engineering computations with formulas

### 📄 Document Processing
- Summarize long PDFs quickly
- Extract key points from reports
- Analyze contracts and legal documents

### 🖼️ Visual Analysis
- Extract data from charts and graphs
- Analyze infographics and diagrams
- OCR-like text extraction from images

### 💼 Business Applications
- Generate professional data tables
- Create formatted Excel reports
- Analyze financial statements
- Process invoices and receipts

---

## ⚠️ Disclaimer

**This application is for educational and productivity purposes.**

- Requires valid Google Gemini API key
- Subject to Google's API usage policies and quotas
- AI responses should be verified for critical applications
- Not a substitute for professional advice in specialized fields

---

## 🐛 Known Issues

- **Large PDFs**: Files over 100 pages may take time to process
- **API Quotas**: Free tier has rate limits (handle gracefully)
- **Complex Tables**: Some nested tables may need manual adjustment
- **Image Quality**: Low-resolution images may reduce accuracy

---

## 📈 Roadmap

### Feature Ideas
- [ ] Voice input/output support
- [ ] Multi-language conversation support
- [ ] Code execution environment
- [ ] Advanced chart visualization
- [ ] Collaborative chat sessions
- [ ] Custom prompt templates library
- [ ] Integration with Google Drive
- [ ] Mobile-responsive design
- [ ] Chat branching and versioning
- [ ] API endpoint for external apps

---

## 👨‍💻 Author

**Brijesh Singh**

- GitHub: [@Brijesh1656](https://github.com/Brijesh1656)
- LinkedIn: [brijesh-singh-b84275307](https://linkedin.com/in/brijesh-singh-b84275307)
- Email: brijesh7146@gmail.com
- Location: Hyderabad, India

### About Me
BBA (Business Analytics) student passionate about leveraging AI and data science to solve real-world problems. Experienced in Python, machine learning, and building intelligent applications.

---

## 🎓 Related Projects

Check out my other AI and data science projects:
- **[FinVision](https://github.com/Brijesh1656/FinVision)** - AI-powered financial document analysis with risk detection
- **[Stock Analysis Pro](https://github.com/Brijesh1656/Stock-Analysis-Pro)** - Technical analysis platform with AI insights and backtesting

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Add comments for complex logic
- Test with various file types
- Update documentation for new features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Google for Gemini 2.0 Flash API
- Streamlit community for excellent framework
- Open-source contributors
- All users providing feedback and suggestions

---

## 📞 Support

For support, questions, or feedback:
- **Email**: brijesh7146@gmail.com
- **Issues**: Open an issue on GitHub
- **LinkedIn**: Message me directly

---

## 💡 Tips & Tricks

### Getting Better Results
1. **Be Specific**: "Create a table with columns: Name, Age, Score" works better than "make a table"
2. **Request Formats**: Explicitly ask for "Excel-ready format" or "markdown table"
3. **Step-by-Step**: Add "show calculations step-by-step" for math problems
4. **Context Matters**: Upload PDFs/images before asking questions about them

### Excel Export
- Tables must use markdown format with `|` separators
- Include a header row with `|---|---|` separator
- AI automatically formats for Excel compatibility
- Download appears immediately below table responses

### File Handling
- **Images**: Under 10MB work best
- **PDFs**: First 8000 characters used (usually 10-15 pages)
- **Multiple Files**: Upload one of each type (1 image + 1 PDF)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ and ☕ by Brijesh Singh

</div>
