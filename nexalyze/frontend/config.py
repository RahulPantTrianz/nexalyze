import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')

    # Streamlit config
    PAGE_TITLE = "Nexalyze"
    PAGE_ICON = "🚀"
    LAYOUT = "wide"

config = Config()
