"""
Reset Neo4j database and reload data
Run this script to clear and reload all company data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connections import neo4j_conn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_neo4j():
    """Clear all company data from Neo4j"""
    try:
        neo4j_conn.connect()
        
        with neo4j_conn.driver.session() as session:
            logger.info("Clearing all Company nodes...")
            result = session.run("MATCH (c:Company) DETACH DELETE c")
            logger.info("Neo4j database cleared!")
            
            # Get count
            count_result = session.run("MATCH (c:Company) RETURN count(c) as count")
            count = list(count_result)[0]['count']
            logger.info(f"Companies in database: {count}")
            
        return True
    except Exception as e:
        logger.error(f"Failed to reset Neo4j: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print(" NEO4J DATABASE RESET")
    print("="*60)
    print("\nThis will delete all Company nodes from Neo4j.")
    print("The backend will automatically reload data on next restart.\n")
    
    confirm = input("Are you sure? Type 'yes' to confirm: ")
    
    if confirm.lower() == 'yes':
        if reset_neo4j():
            print("\n✅ Neo4j database reset successfully!")
            print("\nRestart the backend to reload 500 companies automatically.")
        else:
            print("\n❌ Failed to reset database.")
    else:
        print("\nCancelled.")

