
import os
import re
import asyncio
import logging
from typing import Any, List, Optional, Tuple, Dict, Union

# Try importing asyncpg. If not available, we can only run in sqlite mode.
try:
    import asyncpg
except ImportError:
    asyncpg = None

# Try importing aiosqlite.
try:
    import aiosqlite
except ImportError:
    aiosqlite = None

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

class Database:
    def __init__(self):
        self.mode = "sqlite"
        self._pool = None
        self._sqlite_path = os.path.join(os.path.dirname(__file__), "app.db")
        
        # Determine mode
        if DATABASE_URL and DATABASE_URL.startswith("postgres"):
            if not asyncpg:
                logger.error("DATABASE_URL is set but 'asyncpg' is not installed. Falling back to SQLite.")
                self.mode = "sqlite"
            else:
                self.mode = "postgres"
                # Fix protocol for asyncpg if needed (usually postgres:// works, but let's be safe)
                self.pg_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgres://").replace("postgresql://", "postgres://")
        else:
            if not DATABASE_URL:
                 logger.warning("DATABASE_URL is missing or empty. Falling back to SQLite.")
            elif not DATABASE_URL.startswith("postgres"):
                 logger.warning(f"DATABASE_URL does not start with 'postgres' (Value: {DATABASE_URL[:10]}...). Falling back to SQLite.")
            self.mode = "sqlite"
            
        logger.info(f"Database initialized in {self.mode} mode")

    @property
    def is_postgres(self):
        return self.mode == "postgres"

    async def connect(self):
        """Initialize connection pool (for Postgres) or ensure path (for SQLite)."""
        if self.mode == "postgres":
            if not self._pool:
                try:
                    self._pool = await asyncpg.create_pool(self.pg_url)
                    logger.info("Connected to PostgreSQL")
                except Exception as e:
                    logger.error(f"Failed to connect to Postgres: {e}")
                    raise
        else:
            # SQLite: Just ensure dir exists
            os.makedirs(os.path.dirname(self._sqlite_path), exist_ok=True)
            logger.info(f"Using SQLite at {self._sqlite_path}")

    async def close(self):
        if self.mode == "postgres" and self._pool:
            await self._pool.close()
            logger.info("Closed PostgreSQL pool")

    def _convert_sql_params(self, sql: str, params: tuple) -> Tuple[str, tuple]:
        """
        Convert SQL with '?' placeholders to '$n' provided params for Postgres.
        For SQLite, return as is.
        """
        if self.mode == "sqlite":
            return sql, params
        
        if not params:
            return sql, []

        # Simple regex replacement of ? with $1, $2, etc.
        # Note: This is a naive implementation. It might break if '?' is inside a string literal.
        # But for this project's queries it should be sufficient.
        
        parts = sql.split('?')
        if len(parts) == 1:
            return sql, params
            
        new_sql = ""
        for i, part in enumerate(parts[:-1]):
            new_sql += f"{part}${i+1}"
        new_sql += parts[-1]
        
        return new_sql, params

    async def execute(self, sql: str, params: tuple = None) -> None:
        """Execute a modification query (INSERT, UPDATE, DELETE)."""
        params = params or ()
        if self.mode == "postgres":
            if not self._pool:
                await self.connect()
            
            sql_pg, params_pg = self._convert_sql_params(sql, params)
            async with self._pool.acquire() as conn:
                await conn.execute(sql_pg, *params_pg)
        else:
            async with aiosqlite.connect(self._sqlite_path) as db:
                await db.execute("PRAGMA journal_mode = WAL")
                await db.execute("PRAGMA busy_timeout = 30000")
                await db.execute(sql, params)
                await db.commit()

    async def executemany(self, sql: str, params_list: List[tuple]) -> None:
        """Execute a query for many sets of parameters."""
        if not params_list:
            return

        if self.mode == "postgres":
            if not self._pool:
                await self.connect()
            
            # Convert first set to get SQL structure, assume all match
            sql_pg, _ = self._convert_sql_params(sql, params_list[0])
            
            async with self._pool.acquire() as conn:
                # asyncpg executemany takes (command, args)
                await conn.executemany(sql_pg, params_list)
        else:
            async with aiosqlite.connect(self._sqlite_path) as db:
                await db.execute("PRAGMA journal_mode = WAL")
                await db.execute("PRAGMA busy_timeout = 30000")
                await db.executemany(sql, params_list)
                await db.commit()

    async def execute_returning(self, sql: str, params: tuple = None, id_column: str = "id") -> Any:
        """Execute INSERT and return the new row's id.
        For Postgres: appends RETURNING <id_column> to the SQL.
        For SQLite: uses cursor.lastrowid.
        """
        params = params or ()
        if self.mode == "postgres":
            if not self._pool:
                await self.connect()
            
            sql_pg, params_pg = self._convert_sql_params(sql, params)
            # Append RETURNING if not already present
            if "RETURNING" not in sql_pg.upper():
                sql_pg = sql_pg.rstrip().rstrip(";") + f" RETURNING {id_column}"
            async with self._pool.acquire() as conn:
                return await conn.fetchval(sql_pg, *params_pg)
        else:
            async with aiosqlite.connect(self._sqlite_path) as db_conn:
                await db_conn.execute("PRAGMA journal_mode = WAL")
                await db_conn.execute("PRAGMA busy_timeout = 30000")
                cursor = await db_conn.execute(sql, params)
                await db_conn.commit()
                return cursor.lastrowid

    async def fetchone(self, sql: str, params: tuple = None) -> Optional[dict]:
        """Execute query and return one row as dict."""
        params = params or ()
        if self.mode == "postgres":
            if not self._pool:
                await self.connect()
            
            sql_pg, params_pg = self._convert_sql_params(sql, params)
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(sql_pg, *params_pg)
                return dict(row) if row else None
        else:
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(sql, params) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None

    async def fetchall(self, sql: str, params: tuple = None) -> List[dict]:
        """Execute query and return all rows as list of dicts."""
        params = params or ()
        if self.mode == "postgres":
            if not self._pool:
                await self.connect()
            
            sql_pg, params_pg = self._convert_sql_params(sql, params)
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(sql_pg, *params_pg)
                return [dict(row) for row in rows]
        else:
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
    
    async def fetchval(self, sql: str, params: tuple = None) -> Any:
        """Execute query and return a single value (scalar)."""
        params = params or ()
        if self.mode == "postgres":
            if not self._pool:
                await self.connect()
            
            sql_pg, params_pg = self._convert_sql_params(sql, params)
            async with self._pool.acquire() as conn:
                return await conn.fetchval(sql_pg, *params_pg)
        else:
            async with aiosqlite.connect(self._sqlite_path) as db:
                async with db.execute(sql, params) as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else None

# Global instance
db = Database()
