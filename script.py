import sqlite3

def explore_problem_levels():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Obtener estadísticas sobre el campo level
    cursor.execute("SELECT MIN(level), MAX(level), AVG(level) FROM problems WHERE level IS NOT NULL")
    min_level, max_level, avg_level = cursor.fetchone()
    
    # Obtener conteo de problemas por nivel
    cursor.execute("""
        SELECT level, COUNT(*) as count 
        FROM problems 
        WHERE level IS NOT NULL 
        GROUP BY level 
        ORDER BY level
    """)
    
    level_distribution = cursor.fetchall()
    
    # Contar problemas sin nivel definido
    cursor.execute("SELECT COUNT(*) FROM problems WHERE level IS NULL")
    null_count = cursor.fetchone()[0]
    
    conn.close()
    
    # Mostrar resultados
    print(f"Rango de niveles: {min_level} a {max_level}")
    print(f"Nivel promedio: {avg_level:.2f}")
    print(f"Problemas sin nivel definido: {null_count}")
    print("\nDistribución de niveles:")
    
    for level, count in level_distribution:
        print(f"Nivel {level}: {count} problemas")

# Ejecutar la función
explore_problem_levels()