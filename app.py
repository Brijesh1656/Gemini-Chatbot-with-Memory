from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import time

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

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.5-flash")


# Streamlit page config
st.set_page_config(page_title="Gemini Chatbot", layout="centered")
st.title("🤖 Gemini Chatbot with Memory")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Settings")
    if st.button("🧹 Clear Chat"):
        st.session_state["messages"] = []
    st.download_button(
        "📥 Download Chat History",
        data="\n".join(
            [f"You: {m['user']}\nBot: {m['bot']}" for m in st.session_state.get("messages", [])]
        ),
        file_name="chat_history.txt",
    )

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Function to get Gemini response
def get_gemini_response(question, history):
    conversation = "\n".join(
        [f"You: {msg['user']}\nBot: {msg['bot']}" for msg in history]
    )
    full_prompt = f"{conversation}\nYou: {question}\nBot:"
    response = model.generate_content(full_prompt)
    return response.text

# Display existing chat messages in new style
for msg in st.session_state["messages"]:
    with st.chat_message("user"):
        st.markdown(msg["user"])
    with st.chat_message("assistant"):
        st.markdown(msg["bot"])

# User input in chat-style box
if prompt := st.chat_input("Type your message..."):
    # Show user message immediately
    st.chat_message("user").markdown(prompt)

    # Generate bot response
    bot_placeholder = st.chat_message("assistant").empty()
    full_response = ""

    # Simulate streaming by adding words with delay
    response = get_gemini_response(prompt, st.session_state["messages"])
    for word in response.split():
        full_response += word + " "
        bot_placeholder.markdown(full_response)
        time.sleep(0.03)  # small delay for typing effect

    # Save conversation
    st.session_state["messages"].append({"user": prompt, "bot": full_response.strip()})