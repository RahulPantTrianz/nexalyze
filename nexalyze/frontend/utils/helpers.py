import streamlit as st
import pandas as pd
from typing import Dict, Any, List

def format_currency(amount: float) -> str:
    """Format currency for display"""
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.1f}K"
    else:
        return f"${amount:.2f}"

def create_company_card(company: Dict[str, Any]):
    """Create a company information card"""
    with st.container():
        st.markdown(f"**{company.get('name', 'Unknown Company')}**")
        st.write(company.get('description', 'No description available'))

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Industry: {company.get('industry', 'N/A')}")
        with col2:
            st.write(f"Founded: {company.get('founded_year', 'N/A')}")

def safe_request(func):
    """Decorator for safe API requests"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"Request failed: {str(e)}")
            return None
    return wrapper
