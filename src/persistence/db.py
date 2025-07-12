import sqlite3
import os
import asyncio

DATABASE_PATH = "data/bot.db"
SCHEMA_PATH = "src/persistence/schema.sql"

class Database:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self._lock = asyncio.Lock()

    async def connect(self):
        """Connects to the database."""
        return sqlite3.connect(self.db_path)

    async def initialize(self):
        """Initializes the database schema."""
        async with self._lock:
            conn = await self.connect()
            try:
                with open(SCHEMA_PATH, 'r') as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
                conn.commit()
                print("Database schema initialized.")
            except sqlite3.Error as e:
                print(f"Database initialization error: {e}")
            finally:
                conn.close()

    async def execute(self, query, params=()):
        """Executes a single query with optional parameters."""
        async with self._lock:
            conn = await self.connect()
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                conn.commit()
                return cursor
            except sqlite3.Error as e:
                print(f"Database execution error: {e}\nQuery: {query}\nParams: {params}")
                conn.rollback()
                raise
            finally:
                conn.close()

    async def fetchone(self, query, params=()):
        """Fetches one row from a query."""
        async with self._lock:
            conn = await self.connect()
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                return cursor.fetchone()
            except sqlite3.Error as e:
                print(f"Database fetchone error: {e}\nQuery: {query}\nParams: {params}")
                raise
            finally:
                conn.close()

    async def fetchall(self, query, params=()):
        """Fetches all rows from a query."""
        async with self._lock:
            conn = await self.connect()
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                return cursor.fetchall()
            except sqlite3.Error as e:
                print(f"Database fetchall error: {e}\nQuery: {query}\nParams: {params}")
                raise
            finally:
                conn.close()

    async def executemany(self, query, params_list):
        """Executes a query against all parameter sequences or mappings in the sequence params_list."""
        async with self._lock:
            conn = await self.connect()
            cursor = conn.cursor()
            try:
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor
            except sqlite3.Error as e:
                print(f"Database executemany error: {e}\nQuery: {query}\nParams: {params_list}")
                conn.rollback()
                raise
            finally:
                conn.close()

# Example Usage (for testing)
async def main():
    db = Database()
    await db.initialize()

    # Example: Insert an admin
    try:
        await db.execute("INSERT INTO admins (user_id) VALUES (?)", (12345,))
        print("Admin inserted.")
    except Exception as e:
        print(f"Could not insert admin: {e}")

    # Example: Fetch admins
    admins = await db.fetchall("SELECT user_id FROM admins")
    print(f"Admins: {admins}")

if __name__ == "__main__":
    # Ensure data directory exists for the database file
    os.makedirs("data", exist_ok=True)
    asyncio.run(main())
