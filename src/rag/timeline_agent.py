# whhy it s here i.. timline dosent exist in gradio 

import sqlite3
import os
import re

def search_timeline(query: str) -> str:
    """Extracts a year from the user query and looks it up in the SQL database."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.abspath(os.path.join(script_dir, "../../db/sql/tesla_timeline.db"))
    
    # Simple regex to find a 4-digit year in the user's question
    match = re.search(r'\b(18\d{2}|19\d{2})\b', query)
    
    if not match:
        return "" # No year found, let the Librarian handle it
        
    year = match.group(1)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT event_title, details FROM timeline WHERE year = ?", (year,))
        results = cursor.fetchall()
        conn.close()
        
        if results:
            print(f"[Timeline Agent] Found exact SQL match for year {year}!")
            formatted_results = "\n".join([f"- {row[0]}: {row[1]}" for row in results])
            return f"Historical Database Fact for {year}:\n{formatted_results}"
        else:
            return f"Historical Database Fact: No major anchor events found strictly in the year {year}."
            
    except Exception as e:
        print(f"[Timeline Agent] SQL Error: {e}")
        return ""