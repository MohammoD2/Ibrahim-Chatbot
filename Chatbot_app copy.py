import streamlit as st
from dotenv import load_dotenv
import os

# Import your chatbot function
from Chatbot import chatbot   # assuming you saved your code in chatbot.py

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(page_title="Ibrahim's Chatbot", page_icon="🤖", layout="centered")
st.title("Loyal Servant of Ibrahim ")

# --- Sidebar Settings ---
with st.sidebar:
    st.title("Chat Settings")
    def clear_chat_history():
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Assalamu alaikum 🍁 I’m Ibrahim’s chatbot, here to answer all your questions about Ibrahim and his work!"
        }]
    st.button("Clear Chat History", on_click=clear_chat_history)

# --- Initialize Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Assalamu alaikum 🍁 I’m Ibrahim’s chatbot, here to answer all your questions about Ibrahim and his work!"
    }]

# --- Display Chat Messages ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input Handling ---
if prompt := st.chat_input("Type your message..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display bot response
    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            response = chatbot(prompt, product="Ibrahim")
            st.markdown(response)

    # Append assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})
