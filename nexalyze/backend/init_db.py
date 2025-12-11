import os
import psycopg2
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def init_db():
    """Initialize the database with schema from init.sql"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL not found in environment variables")
        return

    try:
        # Connect to the database
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Read init.sql
        sql_file_path = os.path.join(os.path.dirname(__file__), "database", "init.sql")
        with open(sql_file_path, "r") as f:
            sql_script = f.read()
            
        # Execute the SQL script
        logger.info("Executing init.sql...")
        cur.execute(sql_script)
        conn.commit()
        
        logger.info("Database initialization completed successfully.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

if __name__ == "__main__":
    init_db()
