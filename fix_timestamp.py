import sqlite3
from datetime import datetime, timedelta

def fix_timestamps():
    """
    Fix the revealed_at timestamps for any current problems with dates in the future
    """
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all current problems
    cursor.execute(
        "SELECT id, revealed_at FROM ladder_problems WHERE state = 'current'"
    )
    
    problems = cursor.fetchall()
    fixed_count = 0
    
    # Get current system time
    system_time = datetime.now()
    print(f"System time: {system_time}")
    
    # Create a future date from now (not from hard-coded date)
    # Use a timestamp 1 hour in the future from now
    future_time = system_time + timedelta(hours=1)
    timestamp = future_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    for problem in problems:
        problem_id = problem['id']
        revealed_at = problem['revealed_at']
        
        print(f"Problem ID: {problem_id}")
        print(f"  Current timestamp: {revealed_at}")
        print(f"  Setting to: {timestamp} (1 hour in the future from system time)")
        
        # Force update with future timestamp
        cursor.execute(
            "UPDATE ladder_problems SET revealed_at = ? WHERE id = ?",
            (timestamp, problem_id)
        )
        fixed_count += 1
    
    conn.commit()
    conn.close()
    print(f"Fixed {fixed_count} problems")

if __name__ == "__main__":
    # Print current date to verify it's correct
    print(f"Current date: {datetime.now()}")
    print(f"Current UTC date: {datetime.utcnow()}")
    fix_timestamps() 