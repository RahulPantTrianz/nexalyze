import streamlit as st
import requests
from components.chat import chat_interface

def show_research_page(backend_url: str):
    """Research assistant page"""
    st.header("🤖 AI Research Assistant")
    st.markdown("Ask me anything about startups, markets, or competitive intelligence!")

    # Use reusable chat component
    chat_interface(backend_url)

    # Quick action buttons
    st.markdown("---")
    st.subheader("Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Find Competitors"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Find competitors for a fintech startup"
            })
            st.rerun()

    with col2:
        if st.button("📊 Market Analysis"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Analyze the current AI/ML startup market"
            })
            st.rerun()

    with col3:
        if st.button("💰 Funding Trends"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "What are the latest funding trends in 2025?"
            })
            st.rerun()
