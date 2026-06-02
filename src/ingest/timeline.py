import sqlite3
import os

def init_db():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.abspath(os.path.join(script_dir, "../../db/sql/"))
    os.makedirs(db_dir, exist_ok=True)
    
    db_path = os.path.join(db_dir, "tesla_timeline.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the timeline table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            event_title TEXT NOT NULL,
            details TEXT NOT NULL
        )
    ''')
    
    
    cursor.execute('DELETE FROM timeline')
    
    # Tesla's major life events
    events = [
        (1856, "Birth", "Born on July 10 during a lightning storm in Smiljan, Austrian Empire (modern-day Croatia)."),
        (1884, "Arrival in America", "Arrived in New York City with four cents in his pocket and a letter of recommendation to Thomas Edison."),
        (1888, "AC Motor Patent", "Received patents for the polyphase alternating current (AC) motor, which were soon licensed by George Westinghouse."),
        (1891, "Tesla Coil", "Invented the Tesla Coil, a high-frequency transformer capable of creating high-voltage, low-current electricity."),
        (1893, "World's Columbian Exposition", "Successfully illuminated the World's Fair in Chicago using his AC system, proving its superiority over Edison's DC system."),
        (1899, "Colorado Springs", "Moved to Colorado Springs to conduct high-voltage, high-frequency experiments, claiming to have received extraterrestrial radio signals."),
        (1901, "Wardenclyffe Tower", "Began construction on the Wardenclyffe Tower in New York, intended to be a global wireless communication and power transmission system."),
        (1917, "Edison Medal", "Awarded the Edison Medal, the highest honor of the American Institute of Electrical Engineers, though he initially refused it."),
        (1928, "Final Patent", "Received his final patent for a VTOL (Vertical Take-Off and Landing) flying machine."),
        (1943, "Death", "Passed away alone in Room 3327 of the Hotel New Yorker on January 7 at the age of 86.")
    ]
    
    cursor.executemany('''
        INSERT INTO timeline (year, event_title, details)
        VALUES (?, ?, ?)
    ''', events)
    
    conn.commit()
    conn.close()
    print(f"Timeline database successfully created at {db_path} with {len(events)} historical records.")

if __name__ == "__main__":
    init_db()