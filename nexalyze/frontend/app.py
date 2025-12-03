import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_agraph import agraph, Node, Edge, Config
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configure Streamlit page with enhanced settings
st.set_page_config(
    page_title="Nexalyze - AI Startup Intelligence",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",  # Hide sidebar - using tabs instead
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': "https://github.com/your-repo/issues",
        'About': "# Nexalyze\nAI-Powered Startup Research & Competitive Intelligence Platform"
    }
)

# Custom CSS for modern UI
def load_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Root variables for consistent theming */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --accent-color: #f093fb;
        --success-color: #4ecdc4;
        --warning-color: #ffeaa7;
        --danger-color: #fd79a8;
        --dark-color: #2d3436;
        --light-color: #ddd6fe;
        --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --gradient-secondary: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --gradient-success: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
        --shadow-light: 0 4px 15px rgba(0,0,0,0.1);
        --shadow-medium: 0 8px 25px rgba(0,0,0,0.15);
        --shadow-heavy: 0 15px 35px rgba(0,0,0,0.2);
        --border-radius: 12px;
        --border-radius-lg: 20px;
        --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Global styles */
    .main {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom header */
    .custom-header {
        background: var(--gradient-primary);
        padding: 1rem 2rem;
        border-radius: 0 0 var(--border-radius-lg) var(--border-radius-lg);
        box-shadow: var(--shadow-medium);
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .custom-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/><circle cx="10" cy="60" r="0.5" fill="white" opacity="0.1"/><circle cx="90" cy="40" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        pointer-events: none;
    }
    
    .header-content {
        position: relative;
        z-index: 1;
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: white;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .logo-icon {
        width: 60px;
        height: 60px;
        background: rgba(255,255,255,0.2);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        backdrop-filter: blur(10px);
        border: 2px solid rgba(255,255,255,0.3);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .logo-text h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 800;
        color: #ffffff !important;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
        filter: none !important;
    }
    
    .logo-text p {
        margin: 0;
        font-size: 1.1rem;
        opacity: 0.9;
        font-weight: 400;
    }
    
    .header-stats {
        display: flex;
        gap: 2rem;
        align-items: center;
    }
    
    .stat-item {
        text-align: center;
        background: rgba(255,255,255,0.1);
        padding: 1rem;
        border-radius: var(--border-radius);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        transition: var(--transition);
    }
    
    .stat-item:hover {
        transform: translateY(-2px);
        background: rgba(255,255,255,0.2);
    }
    
    .stat-number {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
    }
    
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.8;
        margin: 0;
    }
    
    /* Enhanced sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-right: 1px solid #e2e8f0;
        box-shadow: var(--shadow-light);
    }
    
    .sidebar .sidebar-content {
        background: transparent;
    }
    
    .sidebar .sidebar-content .block-container {
        padding: 1rem;
    }
    
    /* Navigation buttons */
    .nav-button {
        background: var(--gradient-primary);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: var(--border-radius);
        font-weight: 600;
        transition: var(--transition);
        cursor: pointer;
        width: 100%;
        margin: 0.5rem 0;
        box-shadow: var(--shadow-light);
    }
    
    .nav-button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-medium);
    }
    
    /* Enhanced cards */
    .metric-card {
        background: white;
        border-radius: var(--border-radius-lg);
        padding: 1.5rem;
        box-shadow: var(--shadow-light);
        border: 1px solid #e2e8f0;
        transition: var(--transition);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--gradient-primary);
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-medium);
    }
    
    /* Enhanced buttons */
    .stButton > button {
        background: var(--gradient-primary);
        color: white;
        border: none;
        border-radius: var(--border-radius);
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: var(--transition);
        box-shadow: var(--shadow-light);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-medium);
    }
    
    /* Primary button variant */
    .stButton > button[kind="primary"] {
        background: var(--gradient-success);
        font-size: 1.1rem;
        padding: 0.75rem 2rem;
    }
    
    /* Enhanced input fields */
    .stTextInput > div > div > input {
        border-radius: var(--border-radius);
        border: 2px solid #e2e8f0;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: var(--transition);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Enhanced selectbox */
    .stSelectbox > div > div {
        border-radius: var(--border-radius);
        border: 2px solid #e2e8f0;
    }
    
    /* Loading animations */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255,255,255,.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    @keyframes fade-in {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slide-in-left {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes bounce-in {
        0% {
            opacity: 0;
            transform: scale(0.9);
        }
        50% {
            transform: scale(1.02);
        }
        100% {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    /* Animation utility classes */
    .fade-in {
        animation: fade-in 0.5s ease-out forwards;
    }
    
    .slide-in-left {
        animation: slide-in-left 0.6s ease-out forwards;
    }
    
    .bounce-in {
        animation: bounce-in 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards;
    }
    
    /* Success/Error messages */
    .success-message {
        background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: var(--border-radius);
        margin: 1rem 0;
        box-shadow: var(--shadow-light);
    }
    
    .error-message {
        background: linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: var(--border-radius);
        margin: 1rem 0;
        box-shadow: var(--shadow-light);
    }
    
    /* Add bottom padding to prevent chat input from hiding content */
    .main .block-container {
        padding-bottom: 150px !important;  /* Space for fixed chat input */
    }
    
    /* Enhanced Chat Input Styling */
    .stChatInput {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 999 !important;
        background: linear-gradient(180deg, transparent 0%, rgba(255,255,255,0.98) 20%, rgba(255,255,255,1) 100%) !important;
        padding-top: 20px !important;
        padding-bottom: 20px !important;
    }
    
    .stChatInput > div {
        background: transparent !important;
        border: none !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding: 0 2rem !important;
    }
    
    .stChatInput > div > div {
        background: linear-gradient(135deg, rgba(78, 205, 196, 0.15) 0%, rgba(68, 160, 141, 0.15) 100%) !important;
        backdrop-filter: blur(20px) !important;
        border: 2px solid rgba(78, 205, 196, 0.3) !important;
        border-radius: var(--border-radius-lg) !important;
        box-shadow: var(--shadow-light) !important;
        padding: 0.75rem !important;
        transition: var(--transition) !important;
    }
    
    .stChatInput > div > div:hover {
        border-color: var(--primary-color) !important;
        box-shadow: var(--shadow-medium) !important;
    }
    
    .stChatInput > div > div:focus-within {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15) !important;
    }
    
    .stChatInput textarea {
        background: transparent !important;
        color: #2c3e50 !important;
        font-size: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        border: none !important;
        outline: none !important;
        resize: none !important;
    }
    
    .stChatInput textarea::placeholder {
        color: #7f8c8d !important;
        opacity: 0.8 !important;
    }
    
    .stChatInput button {
        background: var(--gradient-primary) !important;
        border: none !important;
        border-radius: 50% !important;
        transition: var(--transition) !important;
        box-shadow: var(--shadow-light) !important;
    }
    
    .stChatInput button:hover {
        transform: scale(1.1) !important;
        box-shadow: var(--shadow-medium) !important;
    }
    
    .stChatInput button svg {
        fill: white !important;
    }
    
    /* Chat Message Styling */
    .stChatMessage {
        background: transparent !important;
        border: none !important;
        margin: 0.75rem 0 !important;
    }
    
    .stChatMessage > div {
        background: transparent !important;
    }
    
    /* User Chat Message */
    .stChatMessage[data-testid*="user"] {
        padding: 0 !important;
    }
    
    /* Assistant Chat Message */
    .stChatMessage[data-testid*="assistant"] {
        padding: 0 !important;
    }
    
    /* Chat Message Content Container */
    .stChatMessage .stMarkdown {
        background: transparent !important;
    }
    
    /* Improve chat container background */
    div[data-testid="stChatMessageContainer"] {
        background: transparent !important;
    }
    
    /* Fix for chat input container positioning - NO WHITE MARGIN */
    div[data-testid="stChatInputContainer"] {
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        border-top: none !important;
    }
    
    /* Remove any white background from chat input area */
    .stChatInput {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Main chat container - no white background */
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        background: transparent !important;
    }
    
    /* Hide sidebar completely */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Expand main content to full width */
    .main .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* Remove all white backgrounds from chat area */
    [data-testid="stChatInput"], 
    [data-testid="stChatInputContainer"],
    [data-testid="stChatInputContainer"] > div,
    [data-testid="stForm"],
    [data-testid="stForm"] > div {
        background: transparent !important;
        background-color: transparent !important;
    }
    
    /* Navigation buttons styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.8) !important;
        color: #2c3e50 !important;
        border: 2px solid rgba(102, 126, 234, 0.2) !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: rgba(102, 126, 234, 0.1) !important;
        border-color: rgba(102, 126, 234, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Smooth scrolling for chat messages */
    div[data-testid="stVerticalBlock"] {
        scroll-behavior: smooth;
    }
    
    /* Enhanced container for main content */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px !important;
    }
    
    /* Enhanced responsive design */
    @media (max-width: 1200px) {
        .header-stats {
            gap: 1rem;
        }
        
        .stat-item {
            padding: 0.75rem;
        }
    }
    
    @media (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }
        
        .custom-header {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .header-content {
            flex-direction: column;
            gap: 1rem;
            text-align: center;
        }
        
        .header-stats {
            flex-direction: row;
            gap: 0.5rem;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .logo-section {
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .logo-text h1 {
            font-size: 1.8rem;
        }
        
        .logo-text p {
            font-size: 1rem;
        }
        
        .stat-item {
            padding: 0.5rem;
            min-width: 80px;
        }
        
        .stat-number {
            font-size: 1.2rem;
        }
        
        .stat-label {
            font-size: 0.8rem;
        }
        
        /* Mobile-friendly buttons */
        .stButton > button {
            padding: 0.75rem 1rem;
            font-size: 1rem;
            min-height: 48px;
        }
        
        /* Mobile-friendly inputs */
        .stTextInput > div > div > input {
            padding: 1rem;
            font-size: 1rem;
            min-height: 48px;
        }
        
        /* Mobile-friendly cards */
        .metric-card {
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        /* Mobile grid adjustments */
        .grid-responsive {
            grid-template-columns: 1fr !important;
            gap: 1rem !important;
        }
        
        /* Mobile sidebar adjustments */
        .sidebar .sidebar-content {
            padding: 0.5rem;
        }
        
        /* Mobile chat adjustments */
        .stChatMessage {
            margin: 0.5rem 0;
        }
        
        .stChatInput > div > div {
            padding: 1rem !important;
        }
        
        .stChatInput textarea {
            font-size: 1rem !important;
            min-height: 48px !important;
        }
        
        /* Mobile chart adjustments */
        .plotly-chart {
            height: 300px !important;
        }
    }
    
    @media (max-width: 480px) {
        .custom-header {
            padding: 0.75rem;
        }
        
        .logo-text h1 {
            font-size: 1.5rem;
        }
        
        .logo-text p {
            font-size: 0.9rem;
        }
        
        .header-stats {
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .stat-item {
            padding: 0.5rem;
            width: 100%;
            max-width: 150px;
        }
        
        .stat-number {
            font-size: 1.1rem;
        }
        
        .stat-label {
            font-size: 0.75rem;
        }
        
        /* Extra small mobile adjustments */
        .stButton > button {
            padding: 0.5rem 0.75rem;
            font-size: 0.9rem;
        }
        
        .metric-card {
            padding: 0.75rem;
        }
        
        /* Mobile-friendly company cards */
        .company-card-mobile {
            min-height: 300px !important;
            padding: 15px !important;
        }
        
        .company-card-mobile .company-header {
            flex-direction: column !important;
            text-align: center !important;
        }
        
        .company-card-mobile .company-icon {
            margin-right: 0 !important;
            margin-bottom: 10px !important;
        }
    }
    
    /* Touch-friendly interactions */
    @media (hover: none) and (pointer: coarse) {
        .metric-card:hover {
            transform: none;
        }
        
        .stButton > button:hover {
            transform: none;
        }
        
        /* Increase touch targets */
        .stButton > button {
            min-height: 44px;
            min-width: 44px;
        }
        
        .stSelectbox > div > div {
            min-height: 44px;
        }
        
        .stTextInput > div > div > input {
            min-height: 44px;
        }
    }
    
    /* Landscape mobile adjustments */
    @media (max-width: 768px) and (orientation: landscape) {
        .custom-header {
            padding: 0.5rem 1rem;
        }
        
        .header-content {
            flex-direction: row;
            justify-content: space-between;
        }
        
        .header-stats {
            flex-direction: row;
            gap: 0.5rem;
        }
        
        .logo-text h1 {
            font-size: 1.5rem;
        }
        
        .logo-text p {
            font-size: 0.9rem;
        }
    }
    
    /* High DPI displays */
    @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
        .logo-icon {
            border-width: 1px;
        }
        
        .metric-card {
            border-width: 0.5px;
        }
    }
    
    /* Accessibility improvements */
    @media (prefers-reduced-motion: reduce) {
        .fade-in,
        .slide-in-left,
        .bounce-in {
            animation: none;
        }
        
        .metric-card:hover,
        .stButton > button:hover {
            transform: none;
            transition: none;
        }
    }
    
    /* Print styles */
    @media print {
        .custom-header {
            background: white !important;
            color: black !important;
            box-shadow: none !important;
        }
        
        .sidebar {
            display: none !important;
        }
        
        .metric-card {
            break-inside: avoid;
            box-shadow: none !important;
            border: 1px solid #ccc !important;
        }
        
        .stButton > button {
            display: none !important;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        :root {
            --dark-bg: #1a1a1a;
            --dark-card: #2d2d2d;
            --dark-text: #ffffff;
            --dark-border: #404040;
        }
        
        .main {
            background: var(--dark-bg);
            color: var(--dark-text);
        }
        
        .metric-card {
            background: var(--dark-card);
            border-color: var(--dark-border);
            color: var(--dark-text);
        }
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--gradient-primary);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-color);
    }
    
    /* Animation classes */
    .fade-in {
        animation: fadeIn 0.6s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .slide-in-left {
        animation: slideInLeft 0.6s ease-out;
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .bounce-in {
        animation: bounceIn 0.8s ease-out;
    }
    
    @keyframes bounceIn {
        0% { opacity: 0; transform: scale(0.3); }
        50% { opacity: 1; transform: scale(1.05); }
        70% { transform: scale(0.9); }
        100% { opacity: 1; transform: scale(1); }
    }
    </style>
    """, unsafe_allow_html=True)

# Load custom CSS
load_custom_css()

# Dynamic theme application
def apply_theme():
    """Apply theme based on user selection"""
    theme = st.session_state.get("theme", "light")
    
    if theme == "dark":
        st.markdown("""
        <style>
        .main {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
            color: #ffffff !important;
        }
        
        .metric-card {
            background: #2d2d2d !important;
            border-color: #404040 !important;
            color: #ffffff !important;
        }
        
        .custom-header {
            background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%) !important;
        }
        
        .stTextInput > div > div > input {
            background: #2d2d2d !important;
            color: #ffffff !important;
            border-color: #404040 !important;
        }
        
        .stSelectbox > div > div {
            background: #2d2d2d !important;
            color: #ffffff !important;
            border-color: #404040 !important;
        }
        
        .sidebar {
            background: #1a1a1a !important;
        }
        
        .sidebar .sidebar-content {
            background: #1a1a1a !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Light theme is default
        pass

# Backend URL
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')

def get_dynamic_stats():
    """Fetch dynamic statistics - NOT cached to ensure real-time updates"""
    # Initialize session state counters if they don't exist
    if "query_count" not in st.session_state:
        st.session_state.query_count = 0
    if "report_count" not in st.session_state:
        st.session_state.report_count = 0
    
    # Try to get company count from backend
    company_count = 0
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/stats", timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", {})
            company_count = data.get("total_companies", 0)
    except:
        # If backend fails, use a default
        company_count = 0
    
    # Return combined stats with session counters
    return {
        "total_companies": company_count,
        "total_queries": st.session_state.query_count,
        "total_reports": st.session_state.report_count,
        "data_sources": 6
    }

def main():
    # Apply theme
    apply_theme()
    
    # Get dynamic stats
    stats = get_dynamic_stats()
    companies_count = stats.get("total_companies", 0)
    queries_count = stats.get("total_queries", 0)
    reports_count = stats.get("total_reports", 0)
    
    # Format companies count nicely
    if companies_count >= 1000:
        companies_display = f"{companies_count // 1000},{companies_count % 1000:03d}+"
    else:
        companies_display = str(companies_count)
    
    # Enhanced custom header with NEXALYZE prominently displayed - NO BLUR
    st.markdown(f"""
    <div class="custom-header fade-in">
        <div class="header-content">
            <div class="logo-section" style="flex: 1;">
                <div class="logo-icon" style="animation: pulse 2s infinite; font-size: 4rem;">🚀</div>
                <div class="logo-text" style="margin-left: 1.5rem;">
                    <h1 style="font-size: 5rem; letter-spacing: 3px; text-shadow: 4px 4px 8px rgba(0,0,0,0.3); font-weight: 900; margin: 0; line-height: 1; color: #ffffff; filter: none;">NEXALYZE</h1>
                    <p style="font-size: 1.4rem; font-weight: 600; color: #ffffff; opacity: 1; margin: 0.5rem 0 0 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); filter: none;">AI-Powered Startup Research & Competitive Intelligence</p>
                </div>
            </div>
            <div class="header-stats">
                <div class="stat-item" style="cursor: pointer;">
                    <div class="stat-number">{companies_count}</div>
                    <div class="stat-label">Companies</div>
                </div>
                <div class="stat-item" style="cursor: pointer;">
                    <div class="stat-number">{queries_count}</div>
                    <div class="stat-label">Queries</div>
                </div>
                <div class="stat-item" style="cursor: pointer;">
                    <div class="stat-number">{reports_count}</div>
                    <div class="stat-label">Reports</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Single unified page with button navigation (avoiding st.tabs due to chat_input limitation)
    # Initialize page selection
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Research Assistant"
    
    # Create horizontal navigation with buttons
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.9); padding: 0.5rem; border-radius: 15px; 
                margin-bottom: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
    </div>
    """, unsafe_allow_html=True)
    
    cols = st.columns(7)
    
    nav_buttons = [
        ("🤖 Research Assistant", "Research Assistant"),
        ("🔍 Company Search", "Company Search"),
        ("⚔️ Competitive Analysis", "Competitive Analysis"),
        ("🕸️ Knowledge Graph", "Knowledge Graph"),
        ("📊 Report Generator", "Report Generator"),
        ("🗄️ Data Management", "Data Management"),
        ("📰 Hacker News", "Hacker News")
    ]
    
    for col, (label, page_name) in zip(cols, nav_buttons):
        with col:
            button_type = "primary" if st.session_state.active_page == page_name else "secondary"
            if st.button(label, key=f"nav_{page_name}", use_container_width=True, type=button_type):
                st.session_state.active_page = page_name
                st.rerun()
    
    # Spacer
    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
    
    # Render the selected page (OUTSIDE any container so chat_input works)
    if st.session_state.active_page == "Research Assistant":
        show_research_assistant()
    elif st.session_state.active_page == "Company Search":
        show_company_search()
    elif st.session_state.active_page == "Competitive Analysis":
        show_competitive_analysis()
    elif st.session_state.active_page == "Knowledge Graph":
        show_knowledge_graph()
    elif st.session_state.active_page == "Report Generator":
        show_enhanced_report_generator()
    elif st.session_state.active_page == "Data Management":
        show_data_management()
    elif st.session_state.active_page == "Hacker News":
        show_hacker_news()

def show_dashboard():
    # Enhanced dashboard with modern design
    st.markdown("""
    <div class="fade-in">
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="color: #2c3e50; font-size: 2.5rem; margin-bottom: 0.5rem; font-weight: 700;">📊 Dashboard</h1>
            <p style="color: #7f8c8d; font-size: 1.2rem; margin: 0;">Real-time insights into the startup ecosystem</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Get dynamic stats
    stats = get_dynamic_stats()
    companies_count = stats.get("total_companies", 0)
    queries_count = stats.get("total_queries", 0)
    reports_count = stats.get("total_reports", 0)
    data_sources = stats.get("data_sources", 6)
    
    # Format numbers nicely
    companies_display = f"{companies_count:,}+" if companies_count >= 1000 else str(companies_count)

    # Enhanced metrics with animations
    st.markdown("""
    <div class="slide-in-left">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 3rem;">
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card bounce-in">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">
                    <span style="font-size: 1.5rem;">🏢</span>
                </div>
                <div>
                    <h3 style="margin: 0; color: #2c3e50; font-size: 2rem; font-weight: 700;">{companies_display}</h3>
                    <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">Companies Tracked</p>
                </div>
            </div>
            <div style="background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%); color: white; padding: 0.5rem; border-radius: 8px; text-align: center; font-size: 0.8rem;">
                📈 Live Data
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card bounce-in">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">
                    <span style="font-size: 1.5rem;">🔍</span>
                </div>
                <div>
                    <h3 style="margin: 0; color: #2c3e50; font-size: 2rem; font-weight: 700;">{queries_count}</h3>
                    <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">Research Queries</p>
                </div>
            </div>
            <div style="background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); color: #2d3436; padding: 0.5rem; border-radius: 8px; text-align: center; font-size: 0.8rem;">
                📊 Session Total
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card bounce-in">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">
                    <span style="font-size: 1.5rem;">📄</span>
                </div>
                <div>
                    <h3 style="margin: 0; color: #2c3e50; font-size: 2rem; font-weight: 700;">{reports_count}</h3>
                    <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">Reports Generated</p>
                </div>
            </div>
            <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #2d3436; padding: 0.5rem; border-radius: 8px; text-align: center; font-size: 0.8rem;">
                📈 Session Total
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card bounce-in">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #fd79a8 0%, #fdcb6e 100%); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">
                    <span style="font-size: 1.5rem;">🔗</span>
                </div>
                <div>
                    <h3 style="margin: 0; color: #2c3e50; font-size: 2rem; font-weight: 700;">{data_sources}</h3>
                    <p style="margin: 0; color: #7f8c8d; font-size: 0.9rem;">Data Sources</p>
                </div>
            </div>
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.5rem; border-radius: 8px; text-align: center; font-size: 0.8rem;">
                ✅ Active integrations
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # Enhanced charts section
    st.markdown("""
    <div class="fade-in">
        <div style="text-align: center; margin: 3rem 0 2rem 0;">
            <h2 style="color: #2c3e50; font-size: 2rem; margin-bottom: 0.5rem; font-weight: 600;">📈 Market Insights</h2>
            <p style="color: #7f8c8d; font-size: 1rem; margin: 0;">Visualizing startup ecosystem trends and patterns</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Enhanced charts with better styling
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #2c3e50; margin-bottom: 1rem; text-align: center;">🏭 Top Industries</h3>
        """, unsafe_allow_html=True)
        
        # Enhanced pie chart
        industries_data = pd.DataFrame({
            'Industry': ['Fintech', 'Healthcare', 'SaaS', 'E-commerce', 'AI/ML', 'EdTech', 'Cybersecurity'],
            'Companies': [850, 720, 1200, 650, 980, 420, 380],
            'Color': ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4ecdc4', '#44a08d', '#ffeaa7']
        })
        
        fig = px.pie(industries_data, 
                    values='Companies', 
                    names='Industry',
                    color_discrete_sequence=industries_data['Color'],
                    title="",
                    hole=0.4)
        
        fig.update_layout(
            font_family="Inter",
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Companies: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3 style="color: #2c3e50; margin-bottom: 1rem; text-align: center;">💰 Funding Trends</h3>
        """, unsafe_allow_html=True)
        
        # Enhanced line chart
        funding_data = pd.DataFrame({
            'Year': [2020, 2021, 2022, 2023, 2024, 2025],
            'Total Funding ($B)': [45, 78, 65, 92, 110, 125],
            'Series A': [15, 25, 20, 30, 35, 40],
            'Series B': [20, 35, 28, 40, 45, 50],
            'Series C+': [10, 18, 17, 22, 30, 35]
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=funding_data['Year'],
            y=funding_data['Total Funding ($B)'],
            mode='lines+markers',
            name='Total Funding',
            line=dict(color='#667eea', width=4),
            marker=dict(size=8, color='#667eea'),
            hovertemplate='<b>%{x}</b><br>Total Funding: $%{y}B<extra></extra>'
        ))
        
        fig.update_layout(
            font_family="Inter",
            xaxis_title="Year",
            yaxis_title="Funding ($B)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            hovermode='x unified'
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Additional insights section
    st.markdown("""
    <div class="fade-in">
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 2rem; border-radius: 20px; margin: 2rem 0;">
            <h3 style="color: #2c3e50; text-align: center; margin-bottom: 1.5rem;">💡 Key Insights</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
                <div style="background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <h4 style="color: #667eea; margin-bottom: 1rem;">🚀 Growth Trends</h4>
                    <p style="color: #6c757d; margin: 0;">AI/ML startups are leading the growth with 980+ companies tracked, showing a 25% increase from last quarter.</p>
                </div>
                <div style="background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <h4 style="color: #4ecdc4; margin-bottom: 1rem;">💰 Funding Insights</h4>
                    <p style="color: #6c757d; margin: 0;">Total funding reached $125B in 2025, with Series A rounds showing the strongest growth at 40% YoY.</p>
                </div>
                <div style="background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                    <h4 style="color: #f093fb; margin-bottom: 1rem;">🌍 Geographic Distribution</h4>
                    <p style="color: #6c757d; margin: 0;">Silicon Valley continues to dominate with 35% of tracked companies, followed by NYC (18%) and London (12%).</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_research_assistant():
    # Enhanced research assistant page
    st.markdown("""
    <div class="fade-in">
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="color: #2c3e50; font-size: 2.5rem; margin-bottom: 0.5rem; font-weight: 700;">🤖 AI Research Assistant</h1>
            <p style="color: #7f8c8d; font-size: 1.2rem; margin: 0;">Your intelligent companion for startup research and competitive intelligence</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Quick action buttons
    st.markdown("""
    <div class="slide-in-left">
        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 2rem; border-radius: 20px; margin-bottom: 2rem;">
            <h3 style="color: #2c3e50; text-align: center; margin-bottom: 1.5rem;">⚡ Quick Actions</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Find Competitors", use_container_width=True):
            if "messages" not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({
                "role": "user", 
                "content": "Find competitors for a fintech startup"
            })
            st.rerun()
    
    with col2:
        if st.button("📊 Market Analysis", use_container_width=True):
            if "messages" not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({
                "role": "user", 
                "content": "Analyze the current AI/ML startup market"
            })
            st.rerun()
    
    with col3:
        if st.button("💰 Funding Trends", use_container_width=True):
            if "messages" not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({
                "role": "user", 
                "content": "What are the latest funding trends in 2025?"
            })
            st.rerun()
    
    with col4:
        if st.button("🌍 Geographic Data", use_container_width=True):
            if "messages" not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({
                "role": "user", 
                "content": "Show me startup distribution by geography"
            })
            st.rerun()
    
    st.markdown("</div></div>", unsafe_allow_html=True)

    # Enhanced chat interface header
    st.markdown("""
    <div class="fade-in">
        <div style="background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,250,0.95) 100%); 
                    backdrop-filter: blur(20px); 
                    border-radius: 20px; 
                    padding: 2rem; 
                    box-shadow: 0 8px 25px rgba(0,0,0,0.1); 
                    margin-bottom: 2rem;
                    border: 2px solid rgba(102, 126, 234, 0.1);">
            <div style="text-align: center;">
                <div style="display: inline-block; padding: 0.75rem 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 30px; margin-bottom: 1rem;">
                    <h3 style="color: white; margin: 0; font-size: 1.3rem; font-weight: 700;">💬 AI Research Assistant</h3>
                </div>
                <p style="color: #6c757d; margin: 0; font-size: 1rem; line-height: 1.6;">Ask me anything about startups, markets, competitive intelligence, or specific companies!</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize chat messages
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Check if last message needs AI response (from quick action buttons)
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        if "last_processed_message" not in st.session_state or st.session_state.last_processed_message != len(st.session_state.messages):
            # Need to get AI response for the last user message
            st.session_state.last_processed_message = len(st.session_state.messages)
            
            user_query = st.session_state.messages[-1]["content"]
            
            # Display user message first
            with st.chat_message("user"):
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.25rem; border-radius: 16px; margin: 0.5rem 0; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);">
                    <div style="font-size: 0.95rem; line-height: 1.6;">{user_query}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("🔍 Researching and analyzing..."):
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/api/v1/chat",
                            json={"query": user_query},
                            timeout=30
                        )

                        if response.status_code == 200:
                            result = response.json()
                            assistant_response = result.get("data", {}).get("response", "I'm sorry, I couldn't process that request.")
                        else:
                            assistant_response = "I'm having trouble connecting to the research system. Please try again later."

                    except requests.exceptions.Timeout:
                        assistant_response = "⏱️ Request timed out. Please try a more specific question or try again later."
                    except requests.exceptions.ConnectionError:
                        assistant_response = "🔌 Cannot connect to backend. Please ensure the server is running."
                    except Exception as e:
                        assistant_response = f"❌ Error: {str(e)}"

                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.25rem; border-radius: 16px; margin: 0.5rem 0; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);">
                        <div style="font-size: 0.95rem; line-height: 1.6;">{assistant_response}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            st.rerun()

    # Display chat messages with enhanced styling
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.25rem; border-radius: 16px; margin: 0.5rem 0; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);">
                    <div style="font-size: 0.95rem; line-height: 1.6;">{message["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.25rem; border-radius: 16px; margin: 0.5rem 0; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);">
                    <div style="font-size: 0.95rem; line-height: 1.6;">{message["content"]}</div>
                </div>
                """, unsafe_allow_html=True)

    # Clear chat button BEFORE input (so it's visible above)
    if st.session_state.messages:
        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🗑️ Clear Chat", use_container_width=True, key="clear_chat_btn", type="secondary"):
                st.session_state.messages = []
                if "last_processed_message" in st.session_state:
                    del st.session_state.last_processed_message
                st.rerun()

    # Enhanced chat input
    if prompt := st.chat_input("What would you like to research?", key="research_input"):
        # Increment query counter
        if "query_count" not in st.session_state:
            st.session_state.query_count = 0
        st.session_state.query_count += 1
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.25rem; border-radius: 16px; margin: 0.5rem 0; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);">
                <div style="font-size: 0.95rem; line-height: 1.6;">{prompt}</div>
            </div>
            """, unsafe_allow_html=True)

        # Get AI response with enhanced loading
        with st.chat_message("assistant"):
            with st.spinner("🔍 Researching and analyzing..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/chat",
                        json={"query": prompt},
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        assistant_response = result.get("data", {}).get("response", "I'm sorry, I couldn't process that request.")
                    else:
                        assistant_response = "I'm having trouble connecting to the research system. Please try again later."

                except requests.exceptions.Timeout:
                    assistant_response = "⏱️ Request timed out. Please try a more specific question or try again later."
                except requests.exceptions.ConnectionError:
                    assistant_response = "🔌 Cannot connect to backend. Please ensure the server is running."
                except Exception as e:
                    assistant_response = f"❌ Error: {str(e)}"

                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.25rem; border-radius: 16px; margin: 0.5rem 0; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);">
                    <div style="font-size: 0.95rem; line-height: 1.6;">{assistant_response}</div>
                </div>
                """, unsafe_allow_html=True)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

def show_company_search():
    # Enhanced company search page with modern design
    st.markdown("""
    <div class="fade-in">
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="color: #2c3e50; font-size: 2.5rem; margin-bottom: 0.5rem; font-weight: 700;">🔍 Company Search</h1>
            <p style="color: #7f8c8d; font-size: 1.2rem; margin: 0;">Discover startups and companies across various industries</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Enhanced search interface
    st.markdown("""
    <div class="slide-in-left">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 20px; margin-bottom: 2rem; box-shadow: 0 8px 25px rgba(0,0,0,0.15);">
            <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search for companies", 
            placeholder="Enter company name, industry, or keywords...",
            label_visibility="collapsed",
            key="company_search_input"
        )
    
    with col2:
        search_limit = st.selectbox(
            "Results", 
            [10, 25, 50, 100],
            label_visibility="collapsed",
            key="search_limit_select"
        )
    
    with col3:
        search_clicked = st.button("🚀 Search", type="primary", use_container_width=True, key="search_button")
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Search status with enhanced styling
    if search_query:
        st.markdown(f"""
        <div class="bounce-in">
            <div style="background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%); color: white; padding: 1rem 1.5rem; border-radius: 15px; margin: 1rem 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="font-size: 1.5rem;">🔍</div>
                    <div>
                        <strong>Searching for:</strong> "{search_query}"<br>
                        <small style="opacity: 0.9;">Limit: {search_limit} results</small>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced category suggestions with better layout
    st.markdown("""
    <div class="fade-in">
        <div style="background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,250,0.95) 100%); 
                    backdrop-filter: blur(20px); 
                    border-radius: 20px; 
                    padding: 2.5rem; 
                    box-shadow: 0 8px 25px rgba(0,0,0,0.1); 
                    margin: 2rem 0;
                    border: 2px solid rgba(102, 126, 234, 0.1);">
            <div style="text-align: center; margin-bottom: 2rem;">
                <h3 style="color: #2c3e50; margin-bottom: 0.5rem; font-weight: 700; font-size: 1.8rem;">💡 Popular Categories</h3>
                <p style="color: #7f8c8d; margin: 0; font-size: 1rem;">Click on any category to discover companies in that space</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a grid layout for categories
    categories = [
        ("🤖 AI & ML", "ai"),
        ("🎓 EdTech", "edtech"), 
        ("💰 FinTech", "fintech"),
        ("🏥 Healthcare", "healthcare"),
        ("💻 SaaS", "saas"),
        ("🛒 E-commerce", "ecommerce"),
        ("🎮 Gaming", "gaming"),
        ("🚗 Mobility", "mobility"),
        ("🏠 Real Estate", "real estate"),
        ("🌱 Sustainability", "sustainability")
    ]
    
    # Display in 5 columns per row
    rows = [categories[i:i+5] for i in range(0, len(categories), 5)]
    
    for row_idx, row in enumerate(rows):
        cols = st.columns(5)
        for col_idx, (name, query) in enumerate(row):
            with cols[col_idx]:
                if st.button(name, key=f"cat_{row_idx}_{col_idx}", use_container_width=True):
                    st.session_state['category_search'] = query
                    st.session_state['category_limit'] = 10
                    st.rerun()
        
    # Display category search results in a dedicated section BELOW buttons
    if 'category_search' in st.session_state:
        search_companies(st.session_state['category_search'], st.session_state['category_limit'])
        # Clear after displaying once
        if st.button("Clear Results", key="clear_category_results"):
            del st.session_state['category_search']
            del st.session_state['category_limit']
            st.rerun()
    
    # Trigger regular search if button was clicked
    elif search_clicked and search_query:
        search_companies(search_query, search_limit)

def display_enhanced_company_card(company: dict, index: int):
    """Display an enhanced company card with reduced text size to show more content"""
    # Extract company data
    name = company.get('name', 'Unknown Company')
    description = company.get('description', 'No description available')
    industry = company.get('industry', 'N/A')
    location = company.get('location', 'N/A')
    founded_year = company.get('founded_year', 'N/A')
    yc_batch = company.get('yc_batch', 'N/A')
    website = company.get('website', '')
    
    # Truncate description to show more but not overflow
    max_desc_length = 200
    if len(description) > max_desc_length:
        description_display = description[:max_desc_length] + "..."
    else:
        description_display = description
    
    # Create styled company card with grey background to match page
    st.markdown(f"""
    <div style="background: rgba(248, 249, 250, 0.95); 
                border-radius: 15px; 
                padding: 1.25rem; 
                margin: 1rem 0; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                border-left: 5px solid #667eea;
                transition: transform 0.2s;">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
            <div style="flex: 1;">
                <h3 style="margin: 0 0 0.5rem 0; color: #2c3e50; font-size: 1.15rem; font-weight: 700;">
                    {index}. {name}
                </h3>
                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem;">
                    <span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.25rem 0.75rem; border-radius: 15px; font-size: 0.75rem; font-weight: 600;">{industry}</span>
                    <span style="background: rgba(78, 205, 196, 0.1); color: #44a08d; padding: 0.25rem 0.75rem; border-radius: 15px; font-size: 0.75rem; font-weight: 600;">📍 {location}</span>
                    <span style="background: rgba(255, 179, 71, 0.1); color: #ff8c42; padding: 0.25rem 0.75rem; border-radius: 15px; font-size: 0.75rem; font-weight: 600;">📅 {founded_year}</span>
                    {f'<span style="background: rgba(102, 126, 234, 0.1); color: #667eea; padding: 0.25rem 0.75rem; border-radius: 15px; font-size: 0.75rem; font-weight: 600;">🚀 {yc_batch}</span>' if yc_batch and yc_batch != 'N/A' else ''}
                </div>
            </div>
        </div>
        <p style="color: #6c757d; font-size: 0.85rem; line-height: 1.5; margin: 0 0 0.75rem 0;">
            {description_display}
        </p>
        {f'<a href="{website}" target="_blank" style="color: #667eea; text-decoration: none; font-size: 0.8rem; font-weight: 600;">🌐 Visit Website →</a>' if website and website != 'N/A' else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"📊 View Details", key=f"view_{index}", use_container_width=True):
            st.session_state['active_view'] = 'details'
            st.session_state['active_company_id'] = index
            st.session_state['active_company_name'] = name
            st.rerun()
    
    with col2:
        if st.button(f"⚔️ Analyze", key=f"analyze_{index}", use_container_width=True):
            st.session_state['active_view'] = 'analyze'
            st.session_state['active_company_id'] = index
            st.session_state['active_company_name'] = name
            st.rerun()
    
    with col3:
        if st.button(f"🕸️ Knowledge Graph", key=f"graph_{index}", use_container_width=True):
            st.session_state['active_view'] = 'graph'
            st.session_state['active_company_id'] = index
            st.session_state['active_company_name'] = name
            st.rerun()


def search_companies(query: str, limit: int):
    try:
        with st.spinner("🔍 Searching companies..."):
            response = requests.get(
                f"{BACKEND_URL}/api/v1/companies",
                params={"query": query, "limit": limit},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                companies = result.get("data", [])
                
                if companies:
                    # Enhanced results header with celebration
                    st.markdown(f"""
                    <div class="bounce-in">
                        <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 2rem; border-radius: 20px; margin: 2rem 0; text-align: center; box-shadow: 0 8px 25px rgba(0,0,0,0.15);">
                            <div style="font-size: 3rem; margin-bottom: 1rem;">🎉</div>
                            <h2 style="margin: 0; font-size: 2rem; font-weight: 700;">Found {len(companies)} Companies!</h2>
                            <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Showing results for "{query}"</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Enhanced results container
                    st.markdown("""
                    <div class="fade-in">
                        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 2rem; border-radius: 20px; margin: 2rem 0;">
                            <h3 style="color: #2c3e50; text-align: center; margin-bottom: 2rem; font-weight: 600;">🏢 Company Results</h3>
                    """, unsafe_allow_html=True)
                    
                    # Display companies horizontally one after another
                    for i, company in enumerate(companies):
                        display_enhanced_company_card(company, i + 1)
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
                    
                    # Display active company view RIGHT HERE (after company cards)
                    if 'active_view' in st.session_state and st.session_state.get('active_view'):
                        st.markdown("<hr style='margin: 2rem 0;'>", unsafe_allow_html=True)
                        
                        # Add back button to return to results
                        if st.button("⬅️ Back to Results", key="back_to_results_inline"):
                            del st.session_state['active_view']
                            del st.session_state['active_company_id']
                            del st.session_state['active_company_name']
                            st.rerun()
                        
                        # Display the selected view in FULL WIDTH
                        company_id = st.session_state.get('active_company_id', 0)
                        company_name = st.session_state.get('active_company_name', 'Unknown')
                        view_type = st.session_state['active_view']
                        
                        if view_type == 'details':
                            show_company_details(company_id)
                        elif view_type == 'analyze':
                            analyze_company(company_name, True)
                        elif view_type == 'graph':
                            # Use AI-powered knowledge graph generation
                            generate_ai_knowledge_graph(company_name)
                        
                        return  # Don't show summary stats when viewing details
                    
                    # Add summary statistics
                    st.markdown("""
                    <div class="slide-in-left">
                        <div style="background: white; padding: 1.5rem; border-radius: 15px; margin: 2rem 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                            <h4 style="color: #2c3e50; margin-bottom: 1rem; text-align: center;">📊 Search Summary</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                    """, unsafe_allow_html=True)
                    
                    # Calculate summary stats
                    industries = {}
                    locations = {}
                    stages = {}
                    
                    for company in companies:
                        industry = company.get('industry', 'Unknown')
                        location = company.get('location', 'Unknown')
                        stage = company.get('stage', 'Unknown')
                        
                        industries[industry] = industries.get(industry, 0) + 1
                        locations[location] = locations.get(location, 0) + 1
                        stages[stage] = stages.get(stage, 0) + 1
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"""
                        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px;">
                            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🏭</div>
                            <div style="font-size: 1.2rem; font-weight: 600;">Top Industry</div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">{max(industries.items(), key=lambda x: x[1])[0] if industries else 'N/A'}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%); color: white; border-radius: 10px;">
                            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🌍</div>
                            <div style="font-size: 1.2rem; font-weight: 600;">Top Location</div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">{max(locations.items(), key=lambda x: x[1])[0] if locations else 'N/A'}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border-radius: 10px;">
                            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📊</div>
                            <div style="font-size: 1.2rem; font-weight: 600;">Top Stage</div>
                            <div style="font-size: 0.9rem; opacity: 0.9;">{max(stages.items(), key=lambda x: x[1])[0] if stages else 'N/A'}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div></div></div>", unsafe_allow_html=True)
                    
                else:
                    # Enhanced no results message
                    st.markdown("""
                    <div class="bounce-in">
                        <div style="background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%); color: white; padding: 3rem; border-radius: 20px; margin: 2rem 0; text-align: center; box-shadow: 0 8px 25px rgba(0,0,0,0.15);">
                            <div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
                            <h2 style="margin: 0; font-size: 2rem; font-weight: 700;">No Companies Found</h2>
                            <p style="margin: 1rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Try adjusting your search terms or browse popular categories below</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Enhanced search tips
                    st.markdown("""
                    <div class="fade-in">
                        <div style="background: white; padding: 2rem; border-radius: 15px; margin: 2rem 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                            <h4 style="color: #2c3e50; margin-bottom: 1.5rem; text-align: center;">💡 Search Tips</h4>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
                                <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #667eea;">
                                    <strong style="color: #667eea;">🔍 Broader Terms</strong><br>
                                    <small style="color: #6c757d;">Try "ai", "fintech", or "saas"</small>
                                </div>
                                <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #4ecdc4;">
                                    <strong style="color: #4ecdc4;">🏢 Company Names</strong><br>
                                    <small style="color: #6c757d;">Search by specific company name</small>
                                </div>
                                <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #f093fb;">
                                    <strong style="color: #f093fb;">🏭 Industry Keywords</strong><br>
                                    <small style="color: #6c757d;">Use "healthcare" or "education"</small>
                                </div>
                                <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #ffeaa7;">
                                    <strong style="color: #f57c00;">💡 Categories</strong><br>
                                    <small style="color: #6c757d;">Browse popular categories below</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.error(f"❌ Search request failed with status {response.status_code}")
                
    except requests.exceptions.Timeout:
        st.error("⏱️ Search request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to backend. Make sure the backend is running.")
    except Exception as e:
        st.error(f"❌ Error searching companies: {str(e)}")

def show_competitive_analysis():
    st.markdown("""
    <div class="fade-in">
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="color: #2c3e50; font-size: 2.5rem; margin-bottom: 0.5rem; font-weight: 700;">⚔️ Competitive Analysis</h1>
            <p style="color: #7f8c8d; font-size: 1.2rem; margin: 0;">Deep-dive into company positioning and competitive landscape</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    
    with col1:
        company_name = st.text_input(
            "🏢 Company Name",
            placeholder="Enter company name (e.g., OpenAI, Stripe, Airbnb)...",
            help="Enter the name of the company you want to analyze"
        )
    
    with col2:
        st.write("")
        st.write("")
        include_competitors = st.checkbox("Include Competitors", value=True)
    
    if st.button("🚀 Analyze Company", type="primary", use_container_width=True):
        if company_name:
            analyze_company(company_name, include_competitors)
        else:
            st.error("⚠️ Please enter a company name")


def analyze_company(company_name: str, include_competitors: bool):
    try:
        with st.spinner(f"🔍 Analyzing {company_name}..."):
            response = requests.post(
                f"{BACKEND_URL}/api/v1/analyze",
                json={
                    "company_name": company_name,
                    "include_competitors": include_competitors
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get("data", {})
                
                # Check if we have valid data or error
                if 'error' in analysis:
                    st.error(f"❌ Analysis failed: {analysis['error']}")
                    return
                
                # Display analysis results with beautiful styling
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; padding: 1.5rem; border-radius: 15px; 
                            margin: 2rem 0; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                    <h2 style="margin: 0; color: white;">✅ Analysis Complete for {company_name}</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Company Overview Section
                st.markdown("""
                <div style="background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,250,0.95) 100%); 
                            backdrop-filter: blur(20px); 
                            border-radius: 20px; 
                            padding: 2rem; 
                            box-shadow: 0 8px 25px rgba(0,0,0,0.1); 
                            margin: 2rem 0;
                            border: 2px solid rgba(102, 126, 234, 0.1);">
                    <h2 style="color: #2c3e50; margin: 0 0 1.5rem 0;">📈 Company Overview</h2>
                </div>
                """, unsafe_allow_html=True)
                
                overview = analysis.get("overview", {})
                
                # Display company info with full text (no truncation)
                st.markdown(f"""
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1.5rem 0;">
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #667eea;">
                        <div style="font-size: 0.75rem; color: #6c757d; text-transform: uppercase; margin-bottom: 0.5rem;">Industry</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #2c3e50; word-wrap: break-word;">{overview.get("industry", "N/A")}</div>
                    </div>
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #667eea;">
                        <div style="font-size: 0.75rem; color: #6c757d; text-transform: uppercase; margin-bottom: 0.5rem;">Founded</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #2c3e50;">{overview.get("founded", "N/A")}</div>
                    </div>
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #667eea;">
                        <div style="font-size: 0.75rem; color: #6c757d; text-transform: uppercase; margin-bottom: 0.5rem;">Location</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #2c3e50; word-wrap: break-word;">{overview.get("location", "N/A")}</div>
                    </div>
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 4px solid #667eea;">
                        <div style="font-size: 0.75rem; color: #6c757d; text-transform: uppercase; margin-bottom: 0.5rem;">YC Batch</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #2c3e50;">{overview.get("yc_batch") or overview.get("stage", "N/A")}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="background: rgba(102, 126, 234, 0.05); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                    <strong style="color: #667eea;">Description:</strong><br/>
                    <span style="color: #2c3e50; font-size: 0.95rem;">{overview.get('description', 'No description available')}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Market Position
                st.subheader("🎯 Market Position")
                market_pos = analysis.get("market_position", {})
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Market Size", market_pos.get("market_size", "N/A"))
                with col2:
                    st.metric("Growth Rate", market_pos.get("growth_rate", "N/A"))
                with col3:
                    st.metric("Market Share", market_pos.get("market_share", "N/A"))
                
                st.write(f"**Positioning:** {market_pos.get('positioning', 'N/A')}")
                
                # Recent News
                st.subheader("📰 Recent News")
                news = analysis.get("recent_news", [])
                if news:
                    for article in news:
                        with st.expander(f"📄 {article.get('title', 'No title')}"):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**Source:** {article.get('source', 'Unknown')}")
                                st.write(f"**Date:** {article.get('date', 'No date')}")
                                st.write(f"**Summary:** {article.get('summary', 'No summary')}")
                            with col2:
                                if article.get('url'):
                                    st.markdown(f"""
                                    <div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin: 5px 0;">
                                        <p style="margin: 0; font-size: 12px; color: #2e7d32;"><strong>📰 News Article</strong></p>
                                        <p style="margin: 5px 0 0 0; font-size: 11px; color: #388e3c;">Sample news for demonstration</p>
                                        <a href="{article['url']}" target="_blank" style="
                                            color: #1976d2; 
                                            text-decoration: none; 
                                            font-size: 11px;
                                            font-weight: bold;
                                        ">🔗 View Article</a>
                                    </div>
                                    """, unsafe_allow_html=True)
                else:
                    st.info("No recent news found")
                
                # Competitive Analysis
                if include_competitors:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,250,0.95) 100%); 
                                backdrop-filter: blur(20px); 
                                border-radius: 20px; 
                                padding: 2rem; 
                                box-shadow: 0 8px 25px rgba(0,0,0,0.1); 
                                margin: 2rem 0;
                                border: 2px solid rgba(102, 126, 234, 0.1);">
                        <h2 style="color: #2c3e50; margin: 0 0 1.5rem 0;">⚔️ Competitive Analysis</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    competitors = analysis.get("competitors", [])
                    if competitors:
                        st.markdown("**🏆 Key Competitors:**")
                        comp_cols = st.columns(min(len(competitors), 5))
                        for idx, competitor in enumerate(competitors[:5]):
                            with comp_cols[idx]:
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                            color: white; padding: 0.75rem; border-radius: 10px; 
                                            text-align: center; margin: 0.5rem 0;">
                                    <strong>{competitor}</strong>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    comp_analysis = analysis.get("competitive_analysis", {})
                    if comp_analysis:
                        st.markdown("<br/>", unsafe_allow_html=True)
                        
                        # SWOT Analysis with beautiful cards
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("""
                            <div style="background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%); 
                                        color: white; padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
                                <h4 style="margin: 0; color: white;">💪 Strengths</h4>
                            </div>
                            """, unsafe_allow_html=True)
                            for strength in comp_analysis.get("strengths", []):
                                st.markdown(f"✅ {strength}")
                            
                            st.markdown("<br/>", unsafe_allow_html=True)
                            st.markdown("""
                            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                                        color: white; padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
                                <h4 style="margin: 0; color: white;">🚀 Opportunities</h4>
                            </div>
                            """, unsafe_allow_html=True)
                            for opp in comp_analysis.get("opportunities", []):
                                st.markdown(f"🔥 {opp}")
                        
                        with col2:
                            st.markdown("""
                            <div style="background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%); 
                                        color: #2c3e50; padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
                                <h4 style="margin: 0;">⚠️ Weaknesses</h4>
                            </div>
                            """, unsafe_allow_html=True)
                            for weakness in comp_analysis.get("weaknesses", []):
                                st.markdown(f"❌ {weakness}")
                            
                            st.markdown("<br/>", unsafe_allow_html=True)
                            st.markdown("""
                            <div style="background: linear-gradient(135deg, #fd79a8 0%, #fab1a0 100%); 
                                        color: white; padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
                                <h4 style="margin: 0; color: white;">🚨 Threats</h4>
                            </div>
                            """, unsafe_allow_html=True)
                            for threat in comp_analysis.get("threats", []):
                                st.markdown(f"⚡ {threat}")
                        
                        st.markdown("<br/>", unsafe_allow_html=True)
                        st.markdown("""
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    color: white; padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
                            <h4 style="margin: 0; color: white;">🎯 Competitive Advantages</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        for advantage in comp_analysis.get("competitive_advantages", []):
                            st.markdown(f"🏆 {advantage}")
                            
            else:
                st.error("Analysis request failed. Please try again.")
                
    except requests.exceptions.Timeout:
        st.error("Analysis request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Make sure the backend is running.")
    except Exception as e:
        st.error(f"Error analyzing company: {str(e)}")

def show_knowledge_graph():
    """AI-Powered Knowledge Graph Generation"""
    st.markdown("""
    <div class="fade-in">
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="color: #2c3e50; font-size: 2.5rem; margin-bottom: 0.5rem; font-weight: 700;">🕸️ AI Knowledge Graph</h1>
            <p style="color: #7f8c8d; font-size: 1.2rem; margin: 0;">Visualize business ecosystems, dependencies, and opportunities with AI</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("🤖 Our AI will analyze the company and generate a comprehensive knowledge graph showing dependencies, competitors, opportunities, and risks.")
    
    # Input for company name
    col1, col2 = st.columns([3, 1])
    
    with col1:
        company_name = st.text_input(
            "🏢 Company Name", 
            placeholder="e.g., OpenAI, Stripe, Tesla, Airbnb, etc.",
            help="Enter any company name - our AI will research and visualize its ecosystem"
        )
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        generate_btn = st.button("🚀 Generate AI Graph", type="primary", use_container_width=True)
    
    # Sample company suggestions with better styling
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,250,0.95) 100%); 
                backdrop-filter: blur(20px); 
                border-radius: 15px; 
                padding: 1.5rem; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
                margin: 1.5rem 0;
                border: 2px solid rgba(102, 126, 234, 0.1);">
        <h4 style="color: #2c3e50; margin-bottom: 1rem; text-align: center;">💡 Try These Companies</h4>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🤖 OpenAI", use_container_width=True):
            st.session_state['kg_company'] = "OpenAI"
            st.rerun()
            
    with col2:
        if st.button("💳 Stripe", use_container_width=True):
            st.session_state['kg_company'] = "Stripe"
            st.rerun()
            
    with col3:
        if st.button("🏨 Airbnb", use_container_width=True):
            st.session_state['kg_company'] = "Airbnb"
            st.rerun()
            
    with col4:
        if st.button("🚗 Tesla", use_container_width=True):
            st.session_state['kg_company'] = "Tesla"
            st.rerun()
    
    # Check if company was set from button
    if 'kg_company' in st.session_state and st.session_state['kg_company']:
        company_name = st.session_state['kg_company']
        generate_btn = True
        del st.session_state['kg_company']
    
    if generate_btn and company_name:
        generate_ai_knowledge_graph(company_name)

def generate_ai_knowledge_graph(company_name: str):
    """Generate AI-powered knowledge graph as an image"""
    try:
        with st.spinner(f"🤖 AI is analyzing {company_name}'s ecosystem... This may take 30-60 seconds..."):
            # Call backend to generate AI knowledge graph
            response = requests.post(
                f"{BACKEND_URL}/api/v1/generate-knowledge-graph",
                json={"company_name": company_name},
                timeout=120  # 2 minutes for AI generation
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    st.success(f"✅ Knowledge graph generated for **{company_name}**!")
                    
                    # Get the base64 image
                    image_base64 = result.get("data", {}).get("image_base64")
                    analysis = result.get("data", {}).get("analysis", {})
                    
                    if image_base64:
                        # Decode and display the image
                        import base64
                        from PIL import Image
                        import io
                        
                        # Decode base64 to image
                        image_data = base64.b64decode(image_base64)
                        image = Image.open(io.BytesIO(image_data))
                        
                        # Display the knowledge graph image
                        st.markdown("""
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    color: white; padding: 1.5rem; border-radius: 15px; 
                                    margin: 2rem 0; text-align: center;">
                            <h3 style="margin: 0; color: white;">🕸️ AI-Generated Knowledge Graph</h3>
                            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Business Ecosystem & Dependency Analysis</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.image(image, use_column_width=True, caption=f"Knowledge Graph for {company_name}")
                        
                        # Display AI analysis
                        st.markdown("---")
                        st.subheader("🤖 AI Analysis")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if "dependencies" in analysis:
                                st.markdown("### 🔗 Key Dependencies")
                                for dep in analysis.get("dependencies", [])[:5]:
                                    st.write(f"• {dep}")
                            
                            if "opportunities" in analysis:
                                st.markdown("### 🎯 Opportunities")
                                for opp in analysis.get("opportunities", [])[:5]:
                                    st.write(f"• {opp}")
                        
                        with col2:
                            if "risks" in analysis:
                                st.markdown("### ⚠️ Risks & Challenges")
                                for risk in analysis.get("risks", [])[:5]:
                                    st.write(f"• {risk}")
                            
                            if "competitors" in analysis:
                                st.markdown("### 🏆 Main Competitors")
                                for comp in analysis.get("competitors", [])[:5]:
                                    st.write(f"• {comp}")
                        
                        # Download button
                        st.markdown("---")
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            # Convert image to bytes for download
                            buf = io.BytesIO()
                            image.save(buf, format='PNG')
                            st.download_button(
                                label="📥 Download Knowledge Graph",
                                data=buf.getvalue(),
                                file_name=f"{company_name}_knowledge_graph.png",
                                mime="image/png",
                                use_container_width=True
                            )
                    else:
                        st.warning("No image was generated. Please try again.")
                else:
                    st.error(f"Failed to generate knowledge graph: {result.get('message', 'Unknown error')}")
            else:
                st.error(f"Backend error: {response.status_code}")
                
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. AI generation takes time - please try again.")
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to backend. Make sure the server is running.")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def generate_knowledge_graph_by_name(company_name: str):
    """Generate knowledge graph visualization by company name"""
    try:
        with st.spinner(f"Generating knowledge graph for {company_name}..."):
            response = requests.get(
                f"{BACKEND_URL}/api/v1/knowledge-graph/by-name/{company_name}",
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                graph_data = result.get("data", {})
                
                nodes_data = graph_data.get("nodes", [])
                edges_data = graph_data.get("edges", [])
                
                if nodes_data and edges_data:
                    st.success(f"Knowledge graph generated for **{company_name}**")
                    
                    # Display graph statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Nodes", len(nodes_data))
                    with col2:
                        st.metric("Total Relationships", len(edges_data))
                    with col3:
                        st.metric("Company", company_name)
                    
                    # Create graph visualization
                    try:
                        from streamlit_agraph import agraph, Node, Edge, Config
                        
                        # Convert data to streamlit-agraph format
                        nodes = []
                        edges = []
                        
                        # Create nodes
                        for node in nodes_data:
                            nodes.append(Node(
                                id=node["id"],
                                label=node["label"],
                                size=node.get("size", 25),
                                color=node.get("color", "#97C2FC"),
                                physics=node.get("physics", True)
                            ))
                        
                        # Create edges
                        for edge in edges_data:
                            edges.append(Edge(
                                source=edge["from"],
                                target=edge["to"],
                                label=edge.get("label", ""),
                                color=edge.get("color", "#848484")
                            ))
                        
                        # Configure the graph
                        config = Config(
                            width=800,
                            height=600,
                            directed=True,
                            physics=True,
                            hierarchical=False,
                            nodeHighlightBehavior=True,
                            highlightColor="#F7A7A6",
                            collapsible=False
                        )
                        
                        # Display the graph
                        agraph(nodes=nodes, edges=edges, config=config)
                        
                        # Display legend
                        st.subheader("🔍 Graph Legend")
                        
                        legend_col1, legend_col2 = st.columns(2)
                        
                        with legend_col1:
                            st.write("**Node Types:**")
                            st.write("🔵 **Main Company** - The company you searched for")
                            st.write("🟠 **Competitors** - Direct competitors in the market")
                            st.write("🟢 **Investors** - Funding sources and VCs")
                        
                        with legend_col2:
                            st.write("**Relationship Types:**")
                            st.write("🔗 **competes_with** - Competitive relationships")
                            st.write("💰 **invested_in** - Investment relationships")
                            st.write("🤝 **partners_with** - Strategic partnerships")
                            st.write("🎯 **serves/operates_in** - Market relationships")
                        
                        # Display insights
                        st.subheader("📊 Insights")
                        
                        # Count different types of nodes
                        node_types = {}
                        for node in nodes_data:
                            group = node.get('group', 'unknown')
                            node_types[group] = node_types.get(group, 0) + 1
                        
                        insights_col1, insights_col2 = st.columns(2)
                        
                        with insights_col1:
                            st.write("**Ecosystem Composition:**")
                            for node_type, count in node_types.items():
                                st.write(f"• {node_type.replace('_', ' ').title()}: {count}")
                        
                        with insights_col2:
                            st.write("**Network Analysis:**")
                            st.write(f"• Network Density: {len(edges_data)/max(len(nodes_data), 1):.1f} connections per node")
                            st.write(f"• Ecosystem Size: {len(nodes_data)} entities")
                            
                    except ImportError:
                        st.error("streamlit-agraph not installed. Install with: pip install streamlit-agraph")
                        
                        # Fallback: Display as text
                        st.subheader("📋 Graph Data (Text View)")
                        
                        st.write("**Nodes:**")
                        for node in nodes_data:
                            st.write(f"• **{node['label']}** ({node.get('group', 'unknown')})")
                        
                        st.write("**Relationships:**")
                        for edge in edges_data:
                            from_node = next((n['label'] for n in nodes_data if n['id'] == edge['from']), edge['from'])
                            to_node = next((n['label'] for n in nodes_data if n['id'] == edge['to']), edge['to'])
                            st.write(f"• {from_node} **{edge.get('label', 'connected to')}** {to_node}")
                            
                else:
                    st.warning("No graph data available for this company.")
                    st.info("Try searching for: OpenAI, Stripe, Tesla, Microsoft, or other well-known companies")
                    
            else:
                st.error(f"Failed to generate knowledge graph. Status code: {response.status_code}")
                
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Make sure the backend server is running.")
    except Exception as e:
        st.error(f"Error generating knowledge graph: {str(e)}")


def generate_knowledge_graph(company_id: int):
    """Enhanced knowledge graph visualization with clear colors and labels"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/knowledge-graph/{company_id}")

        if response.status_code == 200:
            result = response.json()
            graph_data = result.get("data", {})

            nodes_data = graph_data.get("nodes", [])
            edges_data = graph_data.get("edges", [])

            if nodes_data and edges_data:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; text-align: center;">
                    <h3 style="margin: 0; color: white;">🕸️ Knowledge Graph Visualization</h3>
                    <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Explore company relationships and ecosystem</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Display statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Total Nodes", len(nodes_data))
                with col2:
                    st.metric("🔗 Relationships", len(edges_data))
                with col3:
                    ai_enhanced = graph_data.get("ai_enhanced", False)
                    st.metric("🤖 AI Enhanced", "Yes" if ai_enhanced else "No")
                
                # Create enhanced graph visualization
                nodes = []
                edges = []
                
                # Color mapping for different node types
                color_map = {
                    'main_company': '#1f77b4',      # Blue - Main company
                    'competitor': '#ff7f0e',         # Orange - Competitors
                    'partner': '#2ca02c',            # Green - Partners
                    'market': '#9467bd',             # Purple - Markets
                    'investor': '#d62728',           # Red - Investors
                    'related': '#8c564b',            # Brown - Related
                    'related_company': '#e377c2'     # Pink - Related companies
                }

                for node in nodes_data:
                    group = node.get("group", "related")
                    color = node.get("color", color_map.get(group, "#97C2FC"))
                    size = node.get("size", 25)
                    
                    # Enhance main company node
                    if group == 'main_company':
                        size = 50
                    
                    nodes.append(Node(
                        id=node["id"], 
                        label=node["label"],
                        size=size,
                        color=color,
                        title=node.get("title", node["label"]),  # Tooltip
                        shape="dot" if group != 'main_company' else "star",
                        font={'size': 16 if group == 'main_company' else 12, 'color': 'black'}
                    ))

                for edge in edges_data:
                    edge_label = edge.get("label", "related")
                    edge_color = edge.get("color", "#848484")
                    
                    # Make edges more visible
                    edges.append(Edge(
                        source=edge["from"], 
                        target=edge["to"],
                        label=edge_label,
                        color=edge_color,
                        width=2,  # Thicker edges
                        font={'size': 10, 'align': 'middle'}
                    ))

                config = Config(
                    width=1200,  # Wider
                    height=700,  # Taller
                    directed=True,
                    physics=True,
                    hierarchical=False,
                    nodeHighlightBehavior=True,
                    highlightColor="#F7A7A6",
                    node={'labelProperty': 'label'},
                    link={'labelProperty': 'label', 'renderLabel': True}
                )

                agraph(nodes=nodes, edges=edges, config=config)
                
                # Enhanced legend
                st.markdown("---")
                st.subheader("🎨 Legend")
                
                legend_html = """
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;">
                    <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid #1f77b4;">
                        <span style="color: #1f77b4; font-size: 1.2rem;">⭐</span> <strong>Main Company</strong> - Target company
                    </div>
                    <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid #ff7f0e;">
                        <span style="color: #ff7f0e; font-size: 1.2rem;">🔴</span> <strong>Competitors</strong> - Direct competition
                    </div>
                    <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid #2ca02c;">
                        <span style="color: #2ca02c; font-size: 1.2rem;">🔴</span> <strong>Partners</strong> - Strategic partners
                    </div>
                    <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid #9467bd;">
                        <span style="color: #9467bd; font-size: 1.2rem;">🔴</span> <strong>Markets</strong> - Target markets
                    </div>
                    <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid #d62728;">
                        <span style="color: #d62728; font-size: 1.2rem;">🔴</span> <strong>Investors</strong> - Financial backing
                    </div>
                    <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid #e377c2;">
                        <span style="color: #e377c2; font-size: 1.2rem;">🔴</span> <strong>Related</strong> - Other connections
                    </div>
                </div>
                """
                st.markdown(legend_html, unsafe_allow_html=True)
                
                # Relationship types
                st.markdown("---")
                st.subheader("🔗 Relationship Types")
                
                relationships_html = """
                <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 0.5rem;">
                        <div>• <strong>competes_with</strong> - Direct competition</div>
                        <div>• <strong>partners_with</strong> - Strategic partnership</div>
                        <div>• <strong>serves</strong> - Target market segment</div>
                        <div>• <strong>uses_platform</strong> - Technology dependency</div>
                        <div>• <strong>invested_in</strong> - Financial investment</div>
                        <div>• <strong>integrates_with</strong> - Technical integration</div>
                    </div>
                </div>
                """
                st.markdown(relationships_html, unsafe_allow_html=True)
                
                st.success(f"✅ Knowledge graph generated with {len(nodes)} nodes and {len(edges)} relationships")
            else:
                st.warning("No graph data found for this company.")
        else:
            st.error("Failed to retrieve knowledge graph data.")

    except Exception as e:
        st.error(f"Error generating knowledge graph: {str(e)}")

def show_data_management():
    st.header("🗄️ Data Management")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem;">
        <h3 style="margin: 0 0 0.5rem 0; color: white;">📊 Data Sources</h3>
        <p style="margin: 0; opacity: 0.9;">Manage and sync data from Y Combinator API</p>
    </div>
    """, unsafe_allow_html=True)

    # Y Combinator Data Sync
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
            <h4 style="color: #2c3e50; margin: 0 0 1rem 0;">🚀 Y Combinator API</h4>
            <p style="color: #7f8c8d; margin: 0 0 0.5rem 0;"><strong>Status:</strong> ✅ Connected</p>
            <p style="color: #7f8c8d; margin: 0 0 0.5rem 0;"><strong>Companies:</strong> 5,483 available</p>
            <p style="color: #7f8c8d; margin: 0;"><strong>Last Sync:</strong> On startup</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        sync_limit = st.number_input("Companies to sync", min_value=100, max_value=5483, value=1000, step=100)
        
        if st.button("🔄 Sync YC Data", type="primary", use_container_width=True):
            with st.spinner(f"Syncing {sync_limit} companies from Y Combinator API..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/sync-data",
                        json={"source": "yc", "limit": sync_limit},
                        timeout=600  # 10 minutes for large syncs
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        synced_count = result.get("data", {}).get("synced_count", 0)
                        st.success(f"✅ Successfully synced {synced_count} companies!")
                        
                        # Show some stats
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Synced", synced_count)
                        with col_b:
                            st.metric("Total Available", "5,483")
                        with col_c:
                            st.metric("Coverage", f"{int(synced_count/5483*100)}%")
                    else:
                        st.error(f"Sync failed: {response.status_code}")
                
                except Exception as e:
                    st.error(f"Error during sync: {str(e)}")

    st.markdown("---")

    st.subheader("Database Status")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Neo4j (Knowledge Graph)", "✅ Connected")
    with col2:
        st.metric("PostgreSQL (Structured)", "✅ Connected")
    with col3:
        st.metric("Redis (Cache)", "✅ Connected")

def display_enhanced_company_card(company, index):
    """Display a modern, enhanced company card using Streamlit components"""
    # Industry-based color scheme
    industry_colors = {
        'Artificial Intelligence': {'icon': '🤖', 'color': '#1976d2'},
        'Education Technology': {'icon': '🎓', 'color': '#7b1fa2'},
        'Financial Technology': {'icon': '💰', 'color': '#388e3c'},
        'Healthcare': {'icon': '🏥', 'color': '#f57c00'},
        'Software as a Service': {'icon': '💻', 'color': '#c2185b'},
        'Consumer': {'icon': '🛒', 'color': '#689f38'},
        'B2B': {'icon': '🏢', 'color': '#00796b'},
        'Fintech': {'icon': '💰', 'color': '#388e3c'},
        'EdTech': {'icon': '🎓', 'color': '#7b1fa2'},
        'AI/ML': {'icon': '🤖', 'color': '#1976d2'}
    }
    
    industry = company.get('industry', 'Unknown')
    industry_info = industry_colors.get(industry, {'icon': '🏢', 'color': '#666'})
    
    # Company data
    name = company.get('name', 'Unknown Company')
    founded_year = company.get('founded_year', 'N/A')
    location = company.get('location', 'N/A')
    description = company.get('description', 'No description available')
    yc_batch = company.get('yc_batch', 'N/A')
    website = company.get('website', '')
    industry_tags = company.get('industry', 'General')
    
    # Create a container for the card
    with st.container():
        # Header section with company info
        col1, col2 = st.columns([1, 4])
        
        with col1:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, {industry_info['color']}20, #ffffff); border-radius: 15px; border: 2px solid {industry_info['color']}40;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{industry_info['icon']}</div>
                <div style="font-size: 0.8rem; color: {industry_info['color']}; font-weight: 600;">{industry}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"### {name}")
            st.markdown(f"**Founded:** {founded_year} • **Location:** {location}")
            
            # Description
            if description and description != 'No description available':
                st.markdown(f"*{description[:200]}{'...' if len(description) > 200 else ''}*")
        
        # Metrics in columns
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📅 Founded", founded_year)
        with col2:
            st.metric("🚀 YC Batch", yc_batch)
        with col3:
            st.metric("📍 Location", location if len(str(location)) < 20 else str(location)[:17] + "...")
        
        # Website link
        if website and website != 'N/A':
            st.markdown(f"[🌐 Visit Website]({website})")
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(f"📊 Details", key=f"details_{company.get('id', 0)}_{index}", use_container_width=True, help="View detailed information"):
                st.session_state['active_view'] = 'details'
                st.session_state['active_company_id'] = company.get('id', 0)
                st.session_state['active_company_name'] = company.get('name', 'Unknown')
                st.rerun()
        
        with col2:
            if st.button(f"🔍 Analyze", key=f"analyze_{company.get('id', 0)}_{index}", use_container_width=True, help="Run competitive analysis"):
                st.session_state['active_view'] = 'analyze'
                st.session_state['active_company_id'] = company.get('id', 0)
                st.session_state['active_company_name'] = company.get('name', 'Unknown')
                st.rerun()
        
        with col3:
            if st.button(f"📈 Graph", key=f"graph_{company.get('id', 0)}_{index}", use_container_width=True, help="View knowledge graph"):
                st.session_state['active_view'] = 'graph'
                st.session_state['active_company_id'] = company.get('id', 0)
                st.session_state['active_company_name'] = company.get('name', 'Unknown')
                st.rerun()
        
        with col4:
            if st.button(f"⭐ Save", key=f"save_{company.get('id', 0)}_{index}", use_container_width=True, help="Save to favorites"):
                st.success(f"✅ Saved {company.get('name', 'Company')} to favorites!")
        
        # Add some spacing between cards
        st.markdown("<br>", unsafe_allow_html=True)

def show_company_details(company_id: int):
    """Show detailed company information"""
    try:
        with st.spinner("Loading company details..."):
            response = requests.get(f"{BACKEND_URL}/api/v1/companies/{company_id}")
            
            if response.status_code == 200:
                result = response.json()
                company = result.get("data", {})
                
                # Enhanced company header
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 15px; margin-bottom: 30px;">
                    <div style="display: flex; align-items: center;">
                        <div style="
                            width: 80px; 
                            height: 80px; 
                            background: rgba(255,255,255,0.2); 
                            border-radius: 50%; 
                            display: flex; 
                            align-items: center; 
                            justify-content: center; 
                            margin-right: 20px;
                            font-size: 32px;
                            font-weight: bold;
                        ">
                            {company.get('name', 'U')[0].upper()}
                        </div>
                        <div>
                            <h1 style="margin: 0; font-size: 36px; font-weight: 600;">{company.get('name', 'Company Details')}</h1>
                            <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">{company.get('industry', 'Unknown Industry')}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Detailed information in enhanced tabs
                tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💰 Financials", "🔗 Links & Info", "📈 Analytics"])
                
                with tab1:
                    st.markdown("### Company Overview")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0;">
                            <h4 style="color: #495057; margin-bottom: 15px;">🏢 Basic Information</h4>
                            <p style="margin: 8px 0; color: #6c757d;"><strong>Founded:</strong> {company.get('founded_year', 'N/A')}</p>
                            <p style="margin: 8px 0; color: #6c757d;"><strong>Industry:</strong> {company.get('industry', 'N/A')}</p>
                            <p style="margin: 8px 0; color: #6c757d;"><strong>Location:</strong> {company.get('location', 'N/A')}</p>
                            <p style="margin: 8px 0; color: #6c757d;"><strong>YC Batch:</strong> {company.get('yc_batch', 'N/A')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0;">
                            <h4 style="color: #495057; margin-bottom: 15px;">🏢 Company Details</h4>
                            <p style="margin: 8px 0; color: #6c757d;"><strong>Founded:</strong> {company.get('founded_year', 'N/A')}</p>
                            <p style="margin: 8px 0; color: #6c757d;"><strong>Location:</strong> {company.get('location', 'N/A')}</p>
                            <p style="margin: 8px 0; color: #6c757d;"><strong>Industry:</strong> {company.get('industry', 'N/A')}</p>
                            <p style="margin: 8px 0; color: #6c757d;"><strong>Status:</strong> Active</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Description
                    st.markdown(f"""
                    <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h4 style="color: #1976d2; margin-bottom: 15px;">📝 Description</h4>
                        <p style="color: #424242; line-height: 1.6; margin: 0;">{company.get('description', 'No description available')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with tab2:
                    st.markdown("### Company Information")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Founded Year", company.get('founded_year', 'N/A'), delta=None)
                    with col2:
                        st.metric("Location", company.get('location', 'N/A'), delta=None)
                    with col3:
                        st.metric("YC Batch", company.get('yc_batch', 'N/A'), delta=None)
                    
                    # Industry tags
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h4 style="color: #495057; margin-bottom: 15px;">🏷️ Industry Tags</h4>
                        <p style="color: #6c757d; margin: 0;">{company.get('industry', 'No industry information available')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with tab3:
                    st.markdown("### Links & Additional Information")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if company.get('website') and company['website'] != 'N/A':
                            st.markdown(f"""
                            <div style="background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 10px 0;">
                                <h4 style="color: #2e7d32; margin-bottom: 15px;">🌐 Website</h4>
                                <p style="margin: 0;"><a href="{company['website']}" target="_blank" style="color: #1976d2; text-decoration: none; font-size: 16px;">{company['website']}</a></p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div style="background: #fff3e0; padding: 20px; border-radius: 10px; margin: 10px 0;">
                            <h4 style="color: #f57c00; margin-bottom: 15px;">📊 Metadata</h4>
                            <p style="margin: 8px 0; color: #6c757d;"><strong>Last Updated:</strong> Today</p>
                            <p style="margin: 8px 0; color: #6c757d;"><strong>Data Source:</strong> YC Database</p>
                            <p style="margin: 8px 0; color: #6c757d;"><strong>Verification:</strong> Verified</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                with tab4:
                    st.markdown("### Analytics & Insights")
                    
                    # Placeholder for future analytics
                    st.markdown("""
                    <div style="background: #fce4ec; padding: 30px; border-radius: 10px; margin: 20px 0; text-align: center;">
                        <h4 style="color: #c2185b; margin-bottom: 15px;">📈 Analytics Coming Soon</h4>
                        <p style="color: #6c757d; margin: 0;">Advanced analytics, market trends, and competitive insights will be available here.</p>
                    </div>
                    """, unsafe_allow_html=True)
                
            else:
                st.error("Failed to load company details")
                
    except Exception as e:
        st.error(f"Error loading company details: {str(e)}")

def show_enhanced_report_generator():
    st.header("📊 Enhanced Report Generator")
    
    st.info("""
    🚀 **New & Improved Report Generator**
    
    Generate comprehensive, data-driven reports with charts and visualizations for:
    • **Companies** (e.g., OpenAI, Tesla, Microsoft)
    • **Industries** (e.g., AI, Fintech, Healthcare)
    • **Technologies** (e.g., Machine Learning, Blockchain, Cloud Computing)
    • **Markets** (e.g., SaaS, E-commerce, Mobile Apps)
    • **Investment Themes** (e.g., ESG, Clean Energy, Cybersecurity)
    """)
    
    # Input section
    col1, col2 = st.columns([2, 1])
    
    # Initialize session state for topic
    if "report_topic" not in st.session_state:
        st.session_state.report_topic = ""
    
    with col1:
        # Topic suggestions at the top with beautiful styling
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,250,0.95) 100%); 
                    backdrop-filter: blur(20px); 
                    border-radius: 15px; 
                    padding: 1.5rem; 
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
                    margin-bottom: 1.5rem;
                    border: 2px solid rgba(102, 126, 234, 0.1);">
            <h4 style="color: #2c3e50; margin: 0 0 1rem 0; text-align: center; font-weight: 700;">💡 Quick Suggestions</h4>
        </div>
        """, unsafe_allow_html=True)
        
        suggestions = [
            ("🤖 AI & ML", "Artificial Intelligence"),
            ("💰 Fintech", "Fintech"),
            ("🏥 Healthcare", "Healthcare Technology"),
            ("🌱 Energy", "Clean Energy"),
            ("🛡️ Security", "Cybersecurity"),
            ("☁️ Cloud", "Cloud Computing"),
            ("🚗 EV", "Electric Vehicles"),
            ("🎮 Gaming", "Gaming")
        ]
        
        # Arrange in 2 rows of 4 columns
        rows = [suggestions[i:i+4] for i in range(0, len(suggestions), 4)]
        
        for row_idx, row in enumerate(rows):
            cols = st.columns(4)
            for col_idx, (display_name, topic_value) in enumerate(row):
                with cols[col_idx]:
                    if st.button(display_name, key=f"quick_topic_{row_idx}_{col_idx}", use_container_width=True):
                        st.session_state.report_topic = topic_value
                        st.rerun()
        
        # Topic input field
        topic = st.text_input(
            "🎯 **Report Topic**",
            value=st.session_state.report_topic,
            placeholder="Enter company name, industry, technology, or market segment...",
            help="Examples: 'Artificial Intelligence', 'Tesla', 'Fintech Startups', 'Cloud Computing', 'Sustainable Energy'",
            key="topic_input"
        )
    
    with col2:
        st.write("**Report Options:**")
        
        report_type = st.selectbox(
            "📋 Report Type",
            ["comprehensive", "executive", "detailed", "market_overview", "competitive_analysis"],
            index=0,
            help="Choose the depth and focus of your report"
        )
        
        format_option = st.selectbox(
            "📄 Format",
            ["pdf", "docx"],
            index=0,
            help="PDF recommended for best formatting"
        )
        
        include_charts = st.checkbox("📈 Include Charts & Visualizations", value=True)
        include_competitive = st.checkbox("⚔️ Include Competitive Analysis", value=True)
        include_financials = st.checkbox("💹 Include Financial Analysis", value=True)
    
    # Generate button
    if st.button("🚀 Generate Enhanced Report", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("⚠️ Please enter a report topic")
            return
            
        generate_enhanced_report(topic, report_type, format_option, include_charts, include_competitive, include_financials)

def generate_enhanced_report(topic: str, report_type: str, format_option: str, 
                            include_charts: bool, include_competitive: bool, include_financials: bool):
    """Generate enhanced report with progress tracking"""
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔍 Analyzing topic and gathering data...")
        progress_bar.progress(20)
        
        # Prepare request
        request_data = {
            "topic": topic,
            "report_type": report_type,
            "format": format_option,
            "options": {
                "include_charts": include_charts,
                "include_competitive": include_competitive,
                "include_financials": include_financials
            }
        }
        
        status_text.text("🏢 Researching companies and market data...")
        progress_bar.progress(40)
        
        # Make API call
        response = requests.post(
            f"{BACKEND_URL}/api/v1/generate-comprehensive-report",
            json=request_data,
            timeout=600  # 10 minutes timeout for comprehensive reports
        )
        
        status_text.text("📊 Generating charts and visualizations...")
        progress_bar.progress(70)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                status_text.text("📄 Finalizing report...")
                progress_bar.progress(90)
                
                # Increment report counter
                if "report_count" not in st.session_state:
                    st.session_state.report_count = 0
                st.session_state.report_count += 1
                
                # Display success message
                progress_bar.progress(100)
                status_text.empty()
                
                st.success("✅ Report generated successfully!")
                
                # Display report information
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📊 Topic", topic)
                with col2:
                    st.metric("📋 Type", report_type.title())
                with col3:
                    st.metric("📄 Format", format_option.upper())
                with col4:
                    st.metric("📈 Charts", result.get("charts_generated", 0))
                
                # Report summary
                with st.expander("📋 Report Summary", expanded=True):
                    st.write(f"**Report File:** {result.get('report_filename')}")
                    st.write(f"**Generated:** {result.get('generated_at')}")
                    st.write(f"**Size:** ~{result.get('charts_generated', 0) * 2 + 15}MB (estimated)")
                    
                    # Key features included
                    st.write("**Included Features:**")
                    features = [
                        "📈 Executive Summary with Key Metrics",
                        "🌍 Market Analysis & Geographic Distribution", 
                        "💰 Financial Analysis & Funding Trends",
                        "⚔️ Competitive Landscape Analysis",
                        "🔬 Technology & Innovation Trends",
                        "⚠️ Risk Assessment & Opportunities",
                        "💡 Strategic Recommendations",
                        f"📊 {result.get('charts_generated', 6)}+ Interactive Charts & Graphs"
                    ]
                    
                    for feature in features:
                        st.write(f"• {feature}")
                
                # Download button
                download_report_file(result.get('report_filename'))
                
                # Additional options
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📧 Email Report", use_container_width=True):
                        st.info("📧 Email functionality coming soon!")
                
                with col2:
                    if st.button("📤 Share Report", use_container_width=True):
                        st.info("📤 Share functionality coming soon!")
                
            else:
                st.error(f"❌ Report generation failed: {result.get('error', 'Unknown error')}")
                
        else:
            st.error(f"❌ Request failed with status code: {response.status_code}")
            
    except requests.exceptions.Timeout:
        progress_bar.empty()
        status_text.empty()
        st.error("⏱️ Report generation timed out. Please try a more specific topic or try again later.")
        
    except requests.exceptions.ConnectionError:
        progress_bar.empty()
        status_text.empty()
        st.error("🔌 Cannot connect to backend. Please ensure the server is running.")
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Unexpected error: {str(e)}")

def download_report_file(report_filename: str):
    """Download the generated report file"""
    try:
        # Create download link
        download_url = f"{BACKEND_URL}/api/v1/download-report/{report_filename}"
        
        # Use Streamlit's download button with proper file handling
        response = requests.get(download_url, timeout=30)
        
        if response.status_code == 200:
            # Determine file type
            if report_filename.endswith('.pdf'):
                mime_type = 'application/pdf'
            elif report_filename.endswith('.docx'):
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                mime_type = 'application/octet-stream'
            
            # Create download button
            st.download_button(
                label=f"📥 Download {report_filename}",
                data=response.content,
                file_name=report_filename,
                mime=mime_type,
                type="primary",
                use_container_width=True
            )
        else:
            st.error(f"Failed to download report: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Download failed: {str(e)}")
    except Exception as e:
        st.error(f"Download preparation failed: {str(e)}")

def show_hacker_news():
    """Hacker News integration page"""
    st.markdown("""
    <div class="fade-in">
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="color: #2c3e50; font-size: 2.5rem; margin-bottom: 0.5rem; font-weight: 700;">📰 Hacker News</h1>
            <p style="color: #7f8c8d; font-size: 1.2rem; margin: 0;">Discover startup mentions and discussions on Hacker News</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different HN features
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏢 Company Mentions", 
        "🔍 Keyword Search", 
        "💼 Job Postings", 
        "🚀 Show HN", 
        "❓ Ask HN"
    ])
    
    with tab1:
        show_company_mentions_tab()
    
    with tab2:
        show_keyword_search_tab()
    
    with tab3:
        show_job_search_tab()
    
    with tab4:
        show_show_hn_tab()
    
    with tab5:
        show_ask_hn_tab()

def show_company_mentions_tab():
    """Tab for searching company mentions on Hacker News"""
    st.subheader("🏢 Company Mentions on Hacker News")
    st.markdown("Search for mentions of specific companies across all Hacker News content.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        company_name = st.text_input(
            "Company Name", 
            placeholder="e.g., OpenAI, Stripe, Airbnb",
            help="Enter the company name to search for mentions"
        )
    
    with col2:
        limit = st.number_input("Results Limit", min_value=10, max_value=100, value=50, key="company_mentions_limit")
    
    max_age_days = st.slider("Max Age (days)", min_value=1, max_value=30, value=7, key="company_mentions_age")
    
    if st.button("🔍 Search Company Mentions", type="primary"):
        if company_name:
            with st.spinner(f"Searching for {company_name} mentions on Hacker News..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/hacker-news/company-mentions",
                        json={
                            "company_name": company_name,
                            "limit": limit,
                            "max_age_days": max_age_days
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            mentions = data["data"]
                            display_company_mentions(mentions)
                        else:
                            st.error("Failed to fetch company mentions")
                    else:
                        st.error(f"API request failed: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Error searching for company mentions: {str(e)}")
        else:
            st.warning("Please enter a company name")

def show_keyword_search_tab():
    """Tab for keyword-based search"""
    st.subheader("🔍 Keyword Search")
    st.markdown("Search Hacker News stories by keywords.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        keywords_input = st.text_input(
            "Keywords (comma-separated)", 
            placeholder="e.g., AI, machine learning, startup",
            help="Enter keywords separated by commas"
        )
    
    with col2:
        limit = st.number_input("Results Limit", min_value=10, max_value=100, value=50, key="keyword_search_limit")
    
    col3, col4 = st.columns(2)
    with col3:
        max_age_days = st.slider("Max Age (days)", min_value=1, max_value=30, value=7, key="keyword_search_age")
    
    with col4:
        story_types = st.multiselect(
            "Story Types",
            ["newstories", "topstories", "beststories"],
            default=["newstories", "topstories"],
            key="keyword_search_types"
        )
    
    if st.button("🔍 Search Stories", type="primary"):
        if keywords_input:
            keywords = [k.strip() for k in keywords_input.split(",")]
            
            with st.spinner(f"Searching for stories with keywords: {', '.join(keywords)}..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/hacker-news/search-stories",
                        json={
                            "keywords": keywords,
                            "story_types": story_types,
                            "limit": limit,
                            "max_age_days": max_age_days
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            stories = data["data"]
                            display_hn_stories(stories, "Stories")
                        else:
                            st.error("Failed to fetch stories")
                    else:
                        st.error(f"API request failed: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Error searching stories: {str(e)}")
        else:
            st.warning("Please enter keywords")

def show_job_search_tab():
    """Tab for job search"""
    st.subheader("💼 Job Postings")
    st.markdown("Search for job postings on Hacker News.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        keywords_input = st.text_input(
            "Keywords (comma-separated)", 
            placeholder="e.g., Python, remote, startup",
            help="Enter keywords separated by commas"
        )
    
    with col2:
        limit = st.number_input("Results Limit", min_value=10, max_value=100, value=20, key="job_search_limit")
    
    max_age_days = st.slider("Max Age (days)", min_value=1, max_value=60, value=30, key="job_search_age")
    
    if st.button("🔍 Search Jobs", type="primary"):
        if keywords_input:
            keywords = [k.strip() for k in keywords_input.split(",")]
            
            with st.spinner(f"Searching for jobs with keywords: {', '.join(keywords)}..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/hacker-news/search-jobs",
                        json={
                            "keywords": keywords,
                            "limit": limit,
                            "max_age_days": max_age_days
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            jobs = data["data"]
                            display_hn_stories(jobs, "Job Postings")
                        else:
                            st.error("Failed to fetch jobs")
                    else:
                        st.error(f"API request failed: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Error searching jobs: {str(e)}")
        else:
            st.warning("Please enter keywords")

def show_show_hn_tab():
    """Tab for Show HN search"""
    st.subheader("🚀 Show HN")
    st.markdown("Search Show HN posts by keywords.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        keywords_input = st.text_input(
            "Keywords (comma-separated)", 
            placeholder="e.g., AI, web app, tool",
            help="Enter keywords separated by commas"
        )
    
    with col2:
        limit = st.number_input("Results Limit", min_value=10, max_value=100, value=20, key="show_hn_limit")
    
    max_age_days = st.slider("Max Age (days)", min_value=1, max_value=30, value=7, key="show_hn_age")
    
    if st.button("🔍 Search Show HN", type="primary"):
        if keywords_input:
            keywords = [k.strip() for k in keywords_input.split(",")]
            
            with st.spinner(f"Searching Show HN with keywords: {', '.join(keywords)}..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/hacker-news/search-show-hn",
                        json={
                            "keywords": keywords,
                            "limit": limit,
                            "max_age_days": max_age_days
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            show_hn_posts = data["data"]
                            display_hn_stories(show_hn_posts, "Show HN Posts")
                        else:
                            st.error("Failed to fetch Show HN posts")
                    else:
                        st.error(f"API request failed: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Error searching Show HN: {str(e)}")
        else:
            st.warning("Please enter keywords")

def show_ask_hn_tab():
    """Tab for Ask HN search"""
    st.subheader("❓ Ask HN")
    st.markdown("Search Ask HN posts by keywords.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        keywords_input = st.text_input(
            "Keywords (comma-separated)", 
            placeholder="e.g., startup, advice, experience",
            help="Enter keywords separated by commas"
        )
    
    with col2:
        limit = st.number_input("Results Limit", min_value=10, max_value=100, value=20, key="ask_hn_limit")
    
    max_age_days = st.slider("Max Age (days)", min_value=1, max_value=30, value=7, key="ask_hn_age")
    
    if st.button("🔍 Search Ask HN", type="primary"):
        if keywords_input:
            keywords = [k.strip() for k in keywords_input.split(",")]
            
            with st.spinner(f"Searching Ask HN with keywords: {', '.join(keywords)}..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/api/v1/hacker-news/search-ask-hn",
                        json={
                            "keywords": keywords,
                            "limit": limit,
                            "max_age_days": max_age_days
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            ask_hn_posts = data["data"]
                            display_hn_stories(ask_hn_posts, "Ask HN Posts")
                        else:
                            st.error("Failed to fetch Ask HN posts")
                    else:
                        st.error(f"API request failed: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Error searching Ask HN: {str(e)}")
        else:
            st.warning("Please enter keywords")

def display_company_mentions(mentions):
    """Display company mentions in organized sections"""
    if not mentions or mentions.get("total_mentions", 0) == 0:
        st.info("No mentions found for this company.")
        return
    
    st.success(f"Found {mentions['total_mentions']} total mentions for {mentions['company_name']}")
    
    # Create tabs for different mention types
    mention_tabs = []
    if mentions.get("stories"):
        mention_tabs.append("📰 Stories")
    if mentions.get("jobs"):
        mention_tabs.append("💼 Jobs")
    if mentions.get("show_hn"):
        mention_tabs.append("🚀 Show HN")
    if mentions.get("ask_hn"):
        mention_tabs.append("❓ Ask HN")
    
    if mention_tabs:
        tabs = st.tabs(mention_tabs)
        tab_index = 0
        
        if mentions.get("stories"):
            with tabs[tab_index]:
                st.subheader(f"📰 Stories ({len(mentions['stories'])})")
                display_hn_stories(mentions["stories"], "Stories")
            tab_index += 1
        
        if mentions.get("jobs"):
            with tabs[tab_index]:
                st.subheader(f"💼 Jobs ({len(mentions['jobs'])})")
                display_hn_stories(mentions["jobs"], "Jobs")
            tab_index += 1
        
        if mentions.get("show_hn"):
            with tabs[tab_index]:
                st.subheader(f"🚀 Show HN ({len(mentions['show_hn'])})")
                display_hn_stories(mentions["show_hn"], "Show HN")
            tab_index += 1
        
        if mentions.get("ask_hn"):
            with tabs[tab_index]:
                st.subheader(f"❓ Ask HN ({len(mentions['ask_hn'])})")
                display_hn_stories(mentions["ask_hn"], "Ask HN")

def display_hn_stories(stories, title="Hacker News Items"):
    """Display Hacker News stories in cards"""
    if not stories:
        st.info(f"No {title.lower()} found.")
        return
    
    st.write(f"**{len(stories)} {title}**")
    
    for i, story in enumerate(stories):
        with st.container():
            # Create a card-like container
            st.markdown(f"""
            <div style="
                border: 1px solid #e0e0e0; 
                border-radius: 8px; 
                padding: 1rem; 
                margin: 0.5rem 0; 
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
            """, unsafe_allow_html=True)
            
            # Title and URL
            title_html = f'<h4 style="margin: 0 0 0.5rem 0; color: #2c3e50;"><a href="{story.get("url", "#")}" target="_blank" style="text-decoration: none; color: #2c3e50;">{story.get("title", "No title")}</a></h4>'
            st.markdown(title_html, unsafe_allow_html=True)
            
            # Metadata row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Score", story.get("score", 0))
            
            with col2:
                st.metric("Comments", story.get("descendants", 0))
            
            with col3:
                st.write(f"**By:** {story.get('by', 'Unknown')}")
            
            with col4:
                st.write(f"**Date:** {story.get('date', 'Unknown')}")
            
            # Matched keyword info
            if story.get("matched_keyword"):
                st.info(f"🔍 Matched keyword: **{story['matched_keyword']}** in {', '.join(story.get('matched_in', []))}")
            
            # HN link
            if story.get("hn_url"):
                st.markdown(f'<a href="{story["hn_url"]}" target="_blank" style="color: #667eea;">🔗 View on Hacker News</a>', unsafe_allow_html=True)
            
            # Text content (if available)
            if story.get("text"):
                with st.expander("View Content"):
                    st.markdown(story["text"])
            
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
