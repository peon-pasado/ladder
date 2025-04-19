#!/usr/bin/env python
import os
import sys
import psycopg2
from datetime import datetime, timezone

# Obtener la URL de la base de datos
DATABASE_URL = os.environ.get('DATABASE_URL')

def fix_ladder_problems():
    """Corrige los problemas con el ladder"""
    print("Iniciando corrección del ladder...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # 1. Corregir los estados de los problemas para asegurar que solo el siguiente esté visible
        print("Corrigiendo estados de los problemas...")
        
        # Verificar si hay problemas en la base de datos
        cursor.execute("SELECT COUNT(*) FROM ladder_problems")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("No hay problemas en la base de datos. Primero configura los problemas.")
            return
            
        # Marcar todos los problemas como ocultos inicialmente
        cursor.execute("UPDATE ladder_problems SET state = 'hidden'")
        
        # Obtener el último problema resuelto para cada usuario
        cursor.execute("""
        SELECT baekjoon_username, MAX(position) as last_solved
        FROM solved_problems
        GROUP BY baekjoon_username
        """)
        
        users_progress = cursor.fetchall()
        
        # Si no hay progreso, hacer visible solo el primer problema para cada usuario
        if not users_progress:
            cursor.execute("""
            UPDATE ladder_problems 
            SET state = 'visible' 
            WHERE (baekjoon_username, position) IN (
                SELECT baekjoon_username, MIN(position)
                FROM ladder_problems
                GROUP BY baekjoon_username
            )
            """)
            print("No hay problemas resueltos. Se hizo visible el primer problema para cada usuario.")
        else:
            # Para cada usuario, hacer visible el siguiente problema después del último resuelto
            for username, last_position in users_progress:
                # Hacer visible el siguiente problema
                cursor.execute("""
                UPDATE ladder_problems
                SET state = 'visible'
                WHERE baekjoon_username = %s AND position = %s
                """, (username, last_position + 1))
                
                print(f"Para {username}: último problema resuelto es posición {last_position}. Revelado el siguiente.")
        
        # 2. Corregir los ratings de los usuarios
        print("\nActualizando ratings de usuarios...")
        
        cursor.execute("""
        SELECT u.id, COUNT(sp.id) as solved_count
        FROM users u
        JOIN baekjoon_accounts ba ON u.id = ba.user_id
        LEFT JOIN solved_problems sp ON ba.baekjoon_username = sp.baekjoon_username
        GROUP BY u.id
        """)
        
        for user_id, solved_count in cursor.fetchall():
            # Actualizar el rating basado en la cantidad de problemas resueltos
            new_rating = solved_count * 100  # Fórmula básica: 100 puntos por problema
            
            cursor.execute("""
            UPDATE users
            SET rating = %s
            WHERE id = %s
            """, (new_rating, user_id))
            
            print(f"Usuario ID {user_id}: Rating actualizado a {new_rating} (basado en {solved_count} problemas resueltos)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n¡Corrección completada con éxito!")
        print("Los problemas ahora deberían aparecer en el orden correcto y los ratings actualizados.")
        
    except Exception as e:
        print(f"Error durante la corrección: {str(e)}")
        
if __name__ == "__main__":
    if not DATABASE_URL:
        print("Error: DATABASE_URL no está definida en las variables de entorno.")
        sys.exit(1)
        
    fix_ladder_problems() 