import streamlit as st
import requests
from typing import List, Dict

def chat_interface(backend_url: str):
    """Reusable chat interface component"""

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask your question..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_ai_response(backend_url, prompt)
                st.markdown(response)

        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})

def get_ai_response(backend_url: str, query: str) -> str:
    """Get response from AI assistant"""
    try:
        response = requests.post(
            f"{backend_url}/api/v1/chat",
            json={"query": query}
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("data", {}).get("response", "I couldn't process that request.")
        else:
            return "I'm having trouble connecting. Please try again later."

    except Exception as e:
        return f"Error: {str(e)}"
