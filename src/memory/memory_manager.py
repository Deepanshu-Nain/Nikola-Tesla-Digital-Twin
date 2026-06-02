"""
 Handles saving and retrieving user-specific facts from the local SQLite database.
"""

import sqlite3
import os
from datetime import datetime

class MemoryManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Resolve absolute path to tesla.db
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.abspath(os.path.join(script_dir, "../../db/tesla.db"))
        else:
            self.db_path = db_path
            
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}. Did you run databases.py?")

    def save_memory(self, user_id: str, memory_type: str, memory_content: str) -> bool:
        """
        Saves a new fact about the user into the database.
        Returns True if successful.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO long_term_memory (user_id, memory_type, memory_content, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (user_id, memory_type, memory_content, datetime.now()))
            
            conn.commit()
            conn.close()
            print(f"[Memory] Saved {memory_type} for user '{user_id}': {memory_content}")
            return True
        except Exception as e:
            print(f"[Memory] Failed to save memory: {e}")
            return False

    def get_memories(self, user_id: str) -> str:
        """
        Retrieves all known facts about a specific user and formats them 
        into a string that can be injected into Tesla's prompt.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT memory_type, memory_content 
                FROM long_term_memory 
                WHERE user_id = ?
                ORDER BY timestamp ASC
            ''', (user_id,))
            
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                return "No previous memories found for this user."
                
            memory_string = "Known facts about the user:\n"
            for mem_type, content in records:
                memory_string += f"- {mem_type.capitalize()}: {content}\n"
                
            return memory_string
            
        except Exception as e:
            print(f"[Memory] Failed to retrieve memories: {e}")
            return "Error retrieving memories."

