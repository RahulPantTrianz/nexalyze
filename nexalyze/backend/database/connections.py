import asyncio
from neo4j import GraphDatabase
import psycopg2
import redis
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jConnection:
    def __init__(self):
        self.driver = None

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            logger.info("Connected to Neo4j")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False

    def close(self):
        if self.driver:
            self.driver.close()

class PostgresConnection:
    def __init__(self):
        self.connection = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(settings.postgres_url)
            logger.info("Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False

    def close(self):
        if self.connection:
            self.connection.close()

class RedisConnection:
    def __init__(self):
        self.client = None

    def connect(self):
        try:
            self.client = redis.from_url(settings.redis_url)
            self.client.ping()
            logger.info("Connected to Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    def close(self):
        if self.client:
            self.client.close()

# Global connection instances
neo4j_conn = Neo4jConnection()
postgres_conn = PostgresConnection()
redis_conn = RedisConnection()

async def init_databases():
    """Initialize all database connections"""
    logger.info("Initializing database connections...")

    # Connect to all databases
    neo4j_connected = neo4j_conn.connect()
    postgres_connected = postgres_conn.connect()
    redis_connected = redis_conn.connect()

    if all([neo4j_connected, postgres_connected, redis_connected]):
        logger.info("All databases connected successfully!")
    else:
        logger.warning("Some database connections failed")

    return {
        "neo4j": neo4j_connected,
        "postgres": postgres_connected,
        "redis": redis_connected
    }
