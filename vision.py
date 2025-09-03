from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import time

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Gemini vision model
vision_model = genai.GenerativeModel("gemini-2.5-flash-image-preview")

# Streamlit page config
st.set_page_config(page_title="Gemini Vision Chatbot", layout="centered")
st.title("🖼️ Gemini Vision Chatbot with Memory")

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

# Function to get Gemini Vision response
def get_gemini_response(prompt, image, history):
    conversation = "\n".join(
        [f"You: {msg['user']}\nBot: {msg['bot']}" for msg in history]
    )
    inputs = []
    if conversation:
        inputs.append(conversation)
    if prompt:
        inputs.append(prompt)
    if image:
        inputs.append(image)

    if not inputs:
        return "Please type a message or upload an image."

    response = vision_model.generate_content(inputs)
    return response.text

# Display existing chat messages
for msg in st.session_state["messages"]:
    with st.chat_message("user"):
        st.markdown(msg["user"])
        if msg.get("image"):
            st.image(msg["image"], caption="Uploaded Image", use_column_width=True)
    with st.chat_message("assistant"):
        st.markdown(msg["bot"])

# Image uploader + chat input
uploaded_file = st.file_uploader("📤 Upload an image...", type=["jpg", "jpeg", "png"])
image = None
if uploaded_file is not None:
    image = Image.open(uploaded_file)

if prompt := st.chat_input("Type your message..."):
    # Show user message + image (if any)
    with st.chat_message("user"):
        st.markdown(prompt)
        if image:
            st.image(image, caption="Uploaded Image", use_column_width=True)

    # Generate bot response
    bot_placeholder = st.chat_message("assistant").empty()
    full_response = ""

    response = get_gemini_response(prompt, image, st.session_state["messages"])
    for word in response.split():
        full_response += word + " "
        bot_placeholder.markdown(full_response)
        time.sleep(0.03)  # typing effect

    # Save conversation
    st.session_state["messages"].append(
        {"user": prompt, "bot": full_response.strip(), "image": image if image else None}
    )

