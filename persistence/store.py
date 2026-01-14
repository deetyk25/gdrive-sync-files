import sqlite3
from contextlib import contextmanager
from typing import Iterable, Dict, Optional

# Class providing an interface for interacting with SQLite
# Manages files, jobs, and sync status
class SQLiteStore:
    def __init__(self, db_path: str = "sync.db"):
        # Defines path to SQLite database file + initializes tables
        self.db_path = db_path
        self._init_db()

    @contextmanager
    # Context manager for SQLite connections
    # Commits on success, rolls back on exceptions, closes connection after
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        # Returns rows as dictionary objects
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # Initializes database tables for files, sync state, and jobs
    def _init_db(self):
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    modified_time TEXT NOT NULL
                )
                """
            )

            # Stores checkpoints for sync state
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )

            # Stores jobs and tasks
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL,
                    last_error TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    # Insert or update file metadata in files table.
    def upsert_files(self, files: Iterable[Dict]):
        with self._conn() as conn:
            conn.executemany(
                """
                INSERT INTO files (id, name, mime_type, modified_time)
                VALUES (:id, :name, :mimeType, :modifiedTime)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    mime_type=excluded.mime_type,
                    modified_time=excluded.modified_time
                """,
                files,
            )

    # Returns file counts in database
    def get_file_count(self) -> int:
        with self._conn() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM files")
            return cur.fetchone()[0]
        
    # Returns value of checkpoint when given the key
    # Returns none if key DNE in table
    def get_checkpoint(self, key: str) -> Optional[str]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT value FROM sync_state WHERE key = ?", (key,)
            )
            row = cur.fetchone()
            return row["value"] if row else None

    # Sets / updates value when given a key
    def set_checkpoint(self, key: str, value: Optional[str]):
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO sync_state (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (key, value),
            )

    # Deletes checkpoint pairing when given a key
    def clear_checkpoint(self, key: str):
        with self._conn() as conn:
            conn.execute("DELETE FROM sync_state WHERE key = ?", (key,))
    
    # Creates new job entry on jobs table
    # Automatically sets status as pending
    # Returns job's ID
    def create_job(self, job_type: str, max_attempts: int = 3) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO jobs (type, status, max_attempts)
                VALUES (?, 'PENDING', ?)
                """,
                (job_type, max_attempts),
            )
            return cur.lastrowid
        
    # Retrieves pending jobs up to the defined limit
    # Jobs ordered from oldest to latest
    def fetch_pending_jobs(self, limit: int = 10):
        with self._conn() as conn:
            return conn.execute(
                """
                SELECT *
                FROM jobs
                WHERE status = 'PENDING'
                ORDER BY created_at
                LIMIT ?
                """,
                (limit,),
            ).fetchall()


    # Updates properties of a job
    def update_job(
        self,
        job_id: int,
        status: str,
        attempts: int,
        last_error: Optional[str] = None,
    ):
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?,
                    attempts = ?,
                    last_error = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, attempts, last_error, job_id),
            )
