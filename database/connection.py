"""
Database Connection Manager
Handles PostgreSQL connections and operations
"""

import os
from contextlib import contextmanager
from typing import Optional, Generator, Any, List, Dict
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from database.models import Base

logger = structlog.get_logger()


class DatabaseManager:
    """
    PostgreSQL database connection manager.
    Provides connection pooling and session management.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize database manager.

        Args:
            config: Optional configuration dict, otherwise uses environment variables
        """
        if config:
            self.config = config
        else:
            self.config = {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': os.getenv('POSTGRES_PORT', '5432'),
                'database': os.getenv('POSTGRES_DB', 'ytc_trading'),
                'user': os.getenv('POSTGRES_USER', 'ytc_trader'),
                'password': os.getenv('POSTGRES_PASSWORD', '')
            }

        self.logger = logger.bind(component="database")

        # Build connection string
        self.connection_string = self._build_connection_string()

        # Create engine with connection pooling
        self.engine = create_engine(
            self.connection_string,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL debugging
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        self.logger.info("database_manager_initialized",
                        host=self.config['host'],
                        database=self.config['database'])

    def _build_connection_string(self) -> str:
        """
        Build PostgreSQL connection string.

        Returns:
            Connection string
        """
        return (
            f"postgresql://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.

        Yields:
            SQLAlchemy session

        Example:
            with db.get_session() as session:
                session.query(Trade).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error("session_error", error=str(e))
            raise
        finally:
            session.close()

    def create_tables(self) -> None:
        """
        Create all tables defined in models.
        """
        try:
            # Create schemas first
            with self.engine.connect() as conn:
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS trading"))
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit"))
                conn.commit()

            # Create tables
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("tables_created")

        except Exception as e:
            self.logger.error("table_creation_failed", error=str(e))
            raise

    def drop_tables(self) -> None:
        """
        Drop all tables. USE WITH CAUTION!
        """
        Base.metadata.drop_all(bind=self.engine)
        self.logger.warning("tables_dropped")

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Any]:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Optional parameters for query

        Returns:
            List of results
        """
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            return result.fetchall()

    def execute_insert(self, query: str, params: Optional[Dict] = None) -> Optional[int]:
        """
        Execute an INSERT query and return inserted ID.

        Args:
            query: SQL query string
            params: Optional parameters for query

        Returns:
            Inserted ID if applicable
        """
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            session.commit()
            return result.lastrowid if result.rowcount > 0 else None

    def test_connection(self) -> bool:
        """
        Test database connectivity.

        Returns:
            True if connection successful
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.logger.info("connection_test_passed")
            return True
        except Exception as e:
            self.logger.error("connection_test_failed", error=str(e))
            return False

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.

        Returns:
            Pool statistics
        """
        pool = self.engine.pool
        return {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total_connections': pool.size() + pool.overflow()
        }

    def close(self) -> None:
        """
        Close all database connections.
        """
        self.engine.dispose()
        self.logger.info("database_connections_closed")


# Singleton instance
_db_instance: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """
    Get singleton database instance.

    Returns:
        DatabaseManager instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
