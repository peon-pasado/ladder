import sqlite3
from datetime import datetime

def update_revealed_timestamps():
    """
    Update all 'current' problems that have NULL revealed_at timestamps
    """
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Find all 'current' problems with NULL revealed_at
    cursor.execute(
        "SELECT id FROM ladder_problems WHERE state = 'current' AND revealed_at IS NULL"
    )
    
    problem_ids = [row[0] for row in cursor.fetchall()]
    
    if not problem_ids:
        print("No problems found with missing timestamps.")
        conn.close()
        return
    
    print(f"Found {len(problem_ids)} problems with missing timestamps. Updating...")
    
    # Format for JavaScript compatibility
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    # Update each problem
    for problem_id in problem_ids:
        cursor.execute(
            "UPDATE ladder_problems SET revealed_at = ? WHERE id = ?",
            (current_time, problem_id)
        )
        print(f"Updated problem ID: {problem_id}")
    
    conn.commit()
    conn.close()
    print("Update complete.")

if __name__ == "__main__":
    update_revealed_timestamps() 