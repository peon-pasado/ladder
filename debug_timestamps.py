import sqlite3
from datetime import datetime

def debug_timestamps():
    """
    Debug all 'current' problems and their revealed_at timestamps
    """
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find all 'current' problems
    cursor.execute(
        "SELECT id, revealed_at, baekjoon_username FROM ladder_problems WHERE state = 'current'"
    )
    
    problems = cursor.fetchall()
    
    if not problems:
        print("No 'current' problems found.")
        conn.close()
        return
    
    print(f"Found {len(problems)} 'current' problems:")
    
    for problem in problems:
        problem_id = problem['id']
        revealed_at = problem['revealed_at']
        username = problem['baekjoon_username']
        
        print(f"Problem ID: {problem_id}, Username: {username}")
        print(f"  revealed_at: {revealed_at}")
        
        # Try to parse the date
        if revealed_at:
            try:
                if 'T' in revealed_at:
                    # ISO format
                    date_obj = datetime.fromisoformat(revealed_at.replace('Z', '+00:00'))
                    print(f"  Parsed as: {date_obj} (ISO format)")
                else:
                    # Try other formats
                    try:
                        date_obj = datetime.strptime(revealed_at, '%Y-%m-%d %H:%M:%S')
                        print(f"  Parsed as: {date_obj} (Standard format)")
                    except ValueError:
                        print(f"  Unable to parse date: {revealed_at}")
            except Exception as e:
                print(f"  Error parsing date: {e}")
        else:
            print("  No revealed_at timestamp set")
    
    conn.close()

if __name__ == "__main__":
    debug_timestamps()
    
    # Update all current problems without timestamps
    print("\nUpdating all current problems without timestamps...")
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Get all current problems without a revealed_at timestamp
    cursor.execute(
        "SELECT id FROM ladder_problems WHERE state = 'current' AND (revealed_at IS NULL OR revealed_at = '')"
    )
    
    problem_ids = [row[0] for row in cursor.fetchall()]
    
    if problem_ids:
        # Set the current time in ISO format
        current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        for problem_id in problem_ids:
            cursor.execute(
                "UPDATE ladder_problems SET revealed_at = ? WHERE id = ?",
                (current_time, problem_id)
            )
            print(f"Updated problem ID: {problem_id} with timestamp: {current_time}")
        
        conn.commit()
        print(f"Updated {len(problem_ids)} problems")
    else:
        print("No problems need updating")
    
    conn.close() 