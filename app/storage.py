import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import threading


class Database:
    def __init__(self, database_url: str):
        # Extract path from sqlite:////data/app.db
        self.db_path = database_url.replace("sqlite:///", "")
        self.local = threading.local()
    
    def get_conn(self):
        """Get thread-local connection"""
        if not hasattr(self.local, "conn"):
            self.local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn
    
    def init_db(self):
        """Initialize database schema"""
        conn = self.get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                from_msisdn TEXT NOT NULL,
                to_msisdn TEXT NOT NULL,
                ts TEXT NOT NULL,
                text TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_from_msisdn ON messages(from_msisdn)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ts ON messages(ts)
        """)
        
        conn.commit()
    
    def check_health(self):
        """Check if database is accessible"""
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
    
    def insert_message(
        self,
        message_id: str,
        from_msisdn: str,
        to_msisdn: str,
        ts: str,
        text: Optional[str]
    ) -> bool:
        """
        Insert message into database.
        Returns True if duplicate (already exists), False if newly created.
        """
        conn = self.get_conn()
        cursor = conn.cursor()
        
        # Check if already exists
        cursor.execute(
            "SELECT 1 FROM messages WHERE message_id = ?",
            (message_id,)
        )
        if cursor.fetchone():
            return True  # Duplicate
        
        # Insert new message
        created_at = datetime.utcnow().isoformat() + "Z"
        try:
            cursor.execute("""
                INSERT INTO messages (message_id, from_msisdn, to_msisdn, ts, text, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (message_id, from_msisdn, to_msisdn, ts, text, created_at))
            conn.commit()
            return False  # New message
        except sqlite3.IntegrityError:
            # Race condition: another thread inserted it
            return True
    
    def get_messages(
        self,
        limit: int = 50,
        offset: int = 0,
        from_msisdn: Optional[str] = None,
        since: Optional[str] = None,
        search_text: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get messages with pagination and filters.
        Returns (messages, total_count)
        """
        conn = self.get_conn()
        cursor = conn.cursor()
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if from_msisdn:
            where_clauses.append("from_msisdn = ?")
            params.append(from_msisdn)
        
        if since:
            where_clauses.append("ts >= ?")
            params.append(since)
        
        if search_text:
            where_clauses.append("text LIKE ?")
            params.append(f"%{search_text}%")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM messages WHERE {where_sql}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Get paginated data
        data_query = f"""
            SELECT message_id, from_msisdn, to_msisdn, ts, text
            FROM messages
            WHERE {where_sql}
            ORDER BY ts ASC, message_id ASC
            LIMIT ? OFFSET ?
        """
        cursor.execute(data_query, params + [limit, offset])
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "message_id": row["message_id"],
                "from": row["from_msisdn"],
                "to": row["to_msisdn"],
                "ts": row["ts"],
                "text": row["text"]
            })
        
        return messages, total
    
    def get_stats(self) -> Dict:
        """Get message statistics"""
        conn = self.get_conn()
        cursor = conn.cursor()
        
        # Total messages
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        
        # Senders count
        cursor.execute("SELECT COUNT(DISTINCT from_msisdn) FROM messages")
        senders_count = cursor.fetchone()[0]
        
        # Messages per sender (top 10)
        cursor.execute("""
            SELECT from_msisdn, COUNT(*) as count
            FROM messages
            GROUP BY from_msisdn
            ORDER BY count DESC
            LIMIT 10
        """)
        messages_per_sender = [
            {"from": row["from_msisdn"], "count": row["count"]}
            for row in cursor.fetchall()
        ]
        
        # First and last message timestamps
        cursor.execute("SELECT MIN(ts) as first_ts, MAX(ts) as last_ts FROM messages")
        row = cursor.fetchone()
        first_message_ts = row["first_ts"]
        last_message_ts = row["last_ts"]
        
        return {
            "total_messages": total_messages,
            "senders_count": senders_count,
            "messages_per_sender": messages_per_sender,
            "first_message_ts": first_message_ts,
            "last_message_ts": last_message_ts
        }