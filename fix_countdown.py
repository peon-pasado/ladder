import sqlite3
from datetime import datetime, timedelta

def fix_countdown():
    """
    Set the revealed_at timestamps for all current problems to 6 hours in the future
    """
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Get current system time
    system_time = datetime.now()
    print(f"System time: {system_time}")
    
    # Create a timestamp 6 hours in the future (using longer window)
    future_time = system_time + timedelta(hours=6)
    
    # Important: Use a timestamp format without the Z suffix 
    # to avoid timezone conversion issues in JavaScript
    timestamp = future_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
    print(f"New timestamp: {timestamp}")
    
    # Update all current problems
    cursor.execute(
        "UPDATE ladder_problems SET revealed_at = ? WHERE state = 'current'",
        (timestamp,)
    )
    
    rows_updated = cursor.rowcount
    print(f"Updated {rows_updated} problems")
    
    # Verify the update
    cursor.execute(
        "SELECT id, revealed_at FROM ladder_problems WHERE state = 'current'"
    )
    
    for row in cursor.fetchall():
        print(f"Problem ID: {row[0]}, revealed_at: {row[1]}")
    
    conn.commit()
    conn.close()
    print("Update completed successfully")

if __name__ == "__main__":
    fix_countdown() 