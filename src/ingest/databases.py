import sqlite3
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv


load_dotenv()

def setup_sqlite(db_path: str):
    print(f"Initializing SQLite database at {db_path}...")
    
    # Ensure it EXIsts lol
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tesla_timeline(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER,
        title TEXT,
        description TEXT
    )
    ''')

    # 2. Sources Table 
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tesla_sources(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name TEXT,
        source_type TEXT,
        path TEXT
    )
    ''')

    # 3. Long-Term Memory Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS long_term_memory(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'default_user',
        memory_type TEXT, -- e.g., 'interest', 'learning_goal', 'preference'
        memory_content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()
    print("SQLite tables created successfully.")

def setup_qdrant(qdrant_path: str):
    """Initializes a local Qdrant vector database collection."""
    print(f"Initializing local Qdrant database at {qdrant_path}...")
    
    # Initialize a local file-based Qdrant client
    client = QdrantClient(path=qdrant_path)
    
    collection_name = "tesla_knowledge"
    
    # Check if collection exists to avoid overwriting
    if not client.collection_exists(collection_name=collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
        )
        print(f"Qdrant collection '{collection_name}' created successfully.")
    else:
        print(f"Qdrant collection '{collection_name}' already exists.")

if __name__ == "__main__":
    #ABSOlute path.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    sqlite_db_path = os.path.abspath(os.path.join(script_dir, "../../db/tesla.db"))
    qdrant_db_path = os.path.abspath(os.path.join(script_dir, "../../db/qdrant/"))
    
    print("--- Starting Database Setup ---")
    setup_sqlite(sqlite_db_path)
    setup_qdrant(qdrant_db_path)
    print("--- Setup Complete ---")