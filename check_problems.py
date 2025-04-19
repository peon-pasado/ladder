import sqlite3

def check_problems():
    """Verifica los problemas que están en la base de datos."""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Verificar si la tabla existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='problems'")
    if not cursor.fetchone():
        print("La tabla 'problems' no existe en la base de datos.")
        conn.close()
        return
    
    # Contar el total de problemas
    cursor.execute("SELECT COUNT(*) FROM problems")
    total = cursor.fetchone()[0]
    print(f"Total de problemas en la base de datos: {total}")
    
    # Mostrar algunos problemas de ejemplo
    cursor.execute("SELECT problem_id, problem_title FROM problems LIMIT 10")
    print("\nPrimeros 10 problemas:")
    for row in cursor.fetchall():
        print(f"ID: {row[0]}, Título: {row[1]}")
    
    # Verificar problemas por rango
    ranges = [
        (20996, 21008),
        (21060, 21071),
        # Rangos corregidos para el anterior rango 20329-21058
        (20329, 20329),  # Solo el problema 20329
        (21048, 21048),  # Solo el problema 21048
        (20339, 20339),  # Solo el problema 20339
        (21050, 21058),  # Rango del 21050 al 21058
        (21072, 21132)
    ]
    
    print("\nVerificación por rangos:")
    for i, (start, end) in enumerate(ranges, 1):
        cursor.execute(
            "SELECT COUNT(*) FROM problems WHERE CAST(problem_id AS INTEGER) BETWEEN ? AND ?",
            (start, end)
        )
        count = cursor.fetchone()[0]
        print(f"Rango {i} ({start}-{end}): {count} problemas (esperados: {end-start+1})")
    
    conn.close()

if __name__ == "__main__":
    check_problems() 