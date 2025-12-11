"""
Production-Ready Database Connections
Provides robust connection management with retry logic, health checks, and pooling
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import json

from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable, SessionExpired
import psycopg2
from psycopg2 import pool
import redis

from config.settings import settings

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """
    Neo4j connection manager with connection pooling, retry logic,
    and health monitoring.
    """
    
    def __init__(self):
        self.driver: Optional[Driver] = None
        self.max_retries = 10
        self.retry_delay = 2
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds
        self._is_healthy = False
    
    def _verify_connection(self) -> bool:
        """Verify the connection is actually working"""
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS result")
                result.single()
            return True
        except Exception as e:
            logger.warning(f"Neo4j connection verification failed: {e}")
            return False
    
    def connect(self, retry_count: int = 0) -> bool:
        """
        Connect to Neo4j with exponential backoff retry logic.
        
        Args:
            retry_count: Current retry attempt number
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                connection_timeout=settings.neo4j_connection_timeout,
                max_connection_lifetime=3600,
                max_connection_pool_size=settings.neo4j_max_connection_pool_size,
                fetch_size=1000,
                connection_acquisition_timeout=60
            )
            
            if self._verify_connection():
                self._is_healthy = True
                logger.info("Connected to Neo4j successfully")
                return True
            else:
                self.driver.close()
                self.driver = None
                raise Exception("Connection verification failed")
                
        except Exception as e:
            if retry_count < self.max_retries:
                wait_time = min(self.retry_delay * (2 ** retry_count), 60)
                logger.warning(
                    f"Failed to connect to Neo4j (attempt {retry_count + 1}/{self.max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
                return self.connect(retry_count + 1)
            else:
                logger.error(f"Failed to connect to Neo4j after {self.max_retries} attempts: {e}")
                return False
    
    def is_connected(self) -> bool:
        """Check if connection is alive with caching"""
        current_time = time.time()
        
        # Use cached health status if recent
        if current_time - self._last_health_check < self._health_check_interval:
            return self._is_healthy
        
        # Perform actual health check
        self._last_health_check = current_time
        self._is_healthy = self._verify_connection()
        return self._is_healthy
    
    def reconnect(self) -> bool:
        """Force reconnection to Neo4j"""
        if self.driver:
            try:
                self.driver.close()
            except Exception as e:
                logger.warning(f"Error closing existing Neo4j connection: {e}")
        self.driver = None
        self._is_healthy = False
        return self.connect()
    
    @contextmanager
    def session(self):
        """
        Context manager for Neo4j sessions with automatic error handling.
        
        Usage:
            with neo4j_conn.session() as session:
                result = session.run("MATCH (n) RETURN n LIMIT 10")
        """
        if not self.is_connected():
            self.reconnect()
        
        if not self.driver:
            raise Exception("Neo4j connection not available")
        
        session = self.driver.session()
        try:
            yield session
        except (ServiceUnavailable, SessionExpired) as e:
            logger.warning(f"Neo4j session error, reconnecting: {e}")
            self.reconnect()
            raise
        finally:
            session.close()
    
    def query(self, cypher: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """
        Execute a Cypher query and return results as list of dicts.
        
        Args:
            cypher: Cypher query string
            parameters: Query parameters
        
        Returns:
            List of result records as dictionaries
        """
        if not self.is_connected():
            if not self.reconnect():
                return []
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher, parameters or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            return []
    
    def execute(self, cypher: str, parameters: Dict[str, Any] = None) -> bool:
        """
        Execute a Cypher statement (write operation).
        
        Args:
            cypher: Cypher statement
            parameters: Query parameters
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            if not self.reconnect():
                return False
        
        try:
            with self.driver.session() as session:
                session.run(cypher, parameters or {})
            return True
        except Exception as e:
            logger.error(f"Neo4j execute failed: {e}")
            return False
    
    def close(self):
        """Safely close the Neo4j connection"""
        if self.driver:
            try:
                self.driver.close()
                logger.info("Neo4j connection closed")
            except Exception as e:
                logger.warning(f"Error closing Neo4j connection: {e}")
            finally:
                self.driver = None
                self._is_healthy = False


class PostgresConnection:
    """
    PostgreSQL connection manager with connection pooling.
    """
    
    def __init__(self):
        self.pool: Optional[pool.ThreadedConnectionPool] = None
        self.max_retries = 10
        self.retry_delay = 2
        self._is_healthy = False
    
    def connect(self, retry_count: int = 0) -> bool:
        """
        Create PostgreSQL connection pool with retry logic.
        """
        try:
            self.pool = pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=settings.postgres_pool_size,
                dsn=settings.postgres_url,
                connect_timeout=10
            )
            
            # Test connection
            conn = self.pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            self.pool.putconn(conn)
            
            self._is_healthy = True
            logger.info("Connected to PostgreSQL successfully")
            return True
            
        except Exception as e:
            if retry_count < self.max_retries:
                wait_time = min(self.retry_delay * (2 ** retry_count), 60)
                logger.warning(
                    f"Failed to connect to PostgreSQL (attempt {retry_count + 1}/{self.max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
                return self.connect(retry_count + 1)
            else:
                logger.error(f"Failed to connect to PostgreSQL after {self.max_retries} attempts: {e}")
                return False
    
    def is_connected(self) -> bool:
        """Check if connection pool is healthy"""
        if not self.pool:
            return False
        
        try:
            conn = self.pool.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            self.pool.putconn(conn)
            self._is_healthy = True
            return True
        except Exception:
            self._is_healthy = False
            return False
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for PostgreSQL connections from the pool.
        
        Usage:
            with postgres_conn.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        if not self.pool:
            raise Exception("PostgreSQL connection pool not available")
        
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        finally:
            if conn:
                self.pool.putconn(conn)
    
    def execute(self, query: str, params: tuple = None) -> bool:
        """Execute a SQL statement"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                cursor.close()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL execute failed: {e}")
            return False
    
    def query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                cursor.close()
            return results
        except Exception as e:
            logger.error(f"PostgreSQL query failed: {e}")
            return []
    
    def close(self):
        """Close the connection pool"""
        if self.pool:
            try:
                self.pool.closeall()
                logger.info("PostgreSQL connection pool closed")
            except Exception as e:
                logger.warning(f"Error closing PostgreSQL pool: {e}")
            finally:
                self.pool = None
                self._is_healthy = False


class RedisConnection:
    """
    Redis connection manager with connection pooling and retry logic.
    """
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.pool: Optional[redis.ConnectionPool] = None
        self.max_retries = 10
        self.retry_delay = 2
        self._is_healthy = False
    
    def connect(self, retry_count: int = 0) -> bool:
        """
        Connect to Redis with connection pooling and retry logic.
        """
        try:
            self.pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                socket_connect_timeout=10,
                socket_timeout=settings.redis_socket_timeout,
                health_check_interval=30
            )
            
            self.client = redis.Redis(connection_pool=self.pool)
            self.client.ping()
            
            self._is_healthy = True
            logger.info("Connected to Redis successfully")
            return True
            
        except Exception as e:
            if retry_count < self.max_retries:
                wait_time = min(self.retry_delay * (2 ** retry_count), 60)
                logger.warning(
                    f"Failed to connect to Redis (attempt {retry_count + 1}/{self.max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
                return self.connect(retry_count + 1)
            else:
                logger.error(f"Failed to connect to Redis after {self.max_retries} attempts: {e}")
                return False
    
    def is_connected(self) -> bool:
        """Check if Redis connection is alive"""
        if not self.client:
            return False
        
        try:
            self.client.ping()
            self._is_healthy = True
            return True
        except Exception:
            self._is_healthy = False
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from Redis with JSON deserialization"""
        if not self.is_connected():
            return default
        
        try:
            value = self.client.get(key)
            if value is None:
                return default
            return json.loads(value)
        except json.JSONDecodeError:
            return value.decode() if isinstance(value, bytes) else value
        except Exception as e:
            logger.warning(f"Redis get failed for key {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, expire: int = None) -> bool:
        """Set value in Redis with JSON serialization"""
        if not self.is_connected():
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            if expire:
                self.client.setex(key, expire, serialized)
            else:
                self.client.set(key, serialized)
            return True
        except Exception as e:
            logger.warning(f"Redis set failed for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self.is_connected():
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete failed for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception:
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key"""
        if not self.is_connected():
            return False
        
        try:
            self.client.expire(key, seconds)
            return True
        except Exception:
            return False
    
    def incr(self, key: str) -> Optional[int]:
        """Increment a key's value"""
        if not self.is_connected():
            return None
        
        try:
            return self.client.incr(key)
        except Exception:
            return None
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            try:
                self.client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self.client = None
                self.pool = None
                self._is_healthy = False


# ===========================================
# Global Connection Instances
# ===========================================

neo4j_conn = Neo4jConnection()
postgres_conn = PostgresConnection()
redis_conn = RedisConnection()


async def init_databases() -> Dict[str, bool]:
    """
    Initialize all database connections with retry logic.
    
    Returns:
        Dictionary with connection status for each database
    """
    logger.info("Initializing database connections...")
    
    # Connect to all databases (these have internal retry logic)
    neo4j_connected = neo4j_conn.connect()
    postgres_connected = postgres_conn.connect()
    redis_connected = redis_conn.connect()
    
    # Log status
    status = {
        "neo4j": neo4j_connected,
        "postgres": postgres_connected,
        "redis": redis_connected
    }
    
    if all(status.values()):
        logger.info("All databases connected successfully!")
    else:
        logger.warning("Some database connections failed:")
        if not neo4j_connected:
            logger.warning("  - Neo4j: FAILED (knowledge graph features will not work)")
        if not postgres_connected:
            logger.warning("  - PostgreSQL: FAILED (structured data storage will not work)")
        if not redis_connected:
            logger.warning("  - Redis: FAILED (caching will not work)")
    
    return status


def get_health_status() -> Dict[str, Any]:
    """
    Get health status of all database connections.
    
    Returns:
        Dictionary with detailed health status
    """
    return {
        "neo4j": {
            "connected": neo4j_conn.is_connected(),
            "healthy": neo4j_conn._is_healthy
        },
        "postgres": {
            "connected": postgres_conn.is_connected(),
            "healthy": postgres_conn._is_healthy
        },
        "redis": {
            "connected": redis_conn.is_connected(),
            "healthy": redis_conn._is_healthy
        }
    }


# ===========================================
# Cache Utilities
# ===========================================

def cache_get(key: str, default: Any = None) -> Any:
    """Get value from cache"""
    if not settings.cache_enabled:
        return default
    return redis_conn.get(key, default)


def cache_set(key: str, value: Any, ttl: int = None) -> bool:
    """Set value in cache"""
    if not settings.cache_enabled:
        return True
    ttl = ttl or settings.cache_ttl_default
    return redis_conn.set(key, value, expire=ttl)


def cache_delete(key: str) -> bool:
    """Delete value from cache"""
    return redis_conn.delete(key)


def cache_key(*parts: str) -> str:
    """Generate cache key from parts"""
    return ":".join(str(p) for p in parts)
