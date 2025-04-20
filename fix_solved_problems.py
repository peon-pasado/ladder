#!/usr/bin/env python
import os
import sys
import psycopg2
from datetime import datetime, timezone

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print("Este script verificará y corregirá la página de problemas resueltos")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

def diagnosticar_problemas_resueltos():
    """Diagnostica y corrige problemas en la visualización de problemas resueltos"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # 1. Verificar si hay problemas resueltos en la base de datos
        cursor.execute("SELECT COUNT(*) FROM solved_problems")
        total_solved = cursor.fetchone()[0]
        
        print(f"Total de problemas resueltos en la base de datos: {total_solved}")
        
        # 2. Verificar si hay problemas en estado 'solved' en ladder_problems
        cursor.execute("SELECT COUNT(*) FROM ladder_problems WHERE state = 'solved'")
        total_ladder_solved = cursor.fetchone()[0]
        
        print(f"Total de problemas marcados como 'solved' en el ladder: {total_ladder_solved}")
        
        # 3. Verificar datos de solved_problems para el usuario 1 (admin)
        cursor.execute("""
        SELECT sp.id, sp.problem_id, sp.problem_title, sp.position, sp.solved_at,
               u.username, u.rating
        FROM solved_problems sp
        JOIN users u ON sp.user_id = u.id
        WHERE sp.user_id = 1
        ORDER BY sp.solved_at DESC
        """)
        
        user_solved = cursor.fetchall()
        
        if user_solved:
            print("\n=== Problemas resueltos por el usuario 1 (admin) ===")
            print(f"{'ID':<5} | {'Problem ID':<10} | {'Title':<40} | {'Position':<10} | {'Solved At':<25} | {'Rating':<7}")
            print("-" * 100)
            for problem in user_solved:
                print(f"{problem[0]:<5} | {problem[1]:<10} | {problem[2][:38]:<40} | {problem[3]:<10} | {problem[4]:<25} | {problem[6]:<7}")
        else:
            print("\nNo se encontraron problemas resueltos para el usuario 1 (admin)")
        
        # 4. Crear una función mejorada para obtener problemas resueltos en PostgreSQL
        print("\nCreando función mejorada para obtener problemas resueltos...")
        
        cursor.execute("""
        CREATE OR REPLACE FUNCTION get_solved_problems(p_user_id INTEGER) 
        RETURNS TABLE (
            id INTEGER,
            problem_id TEXT,
            problem_title TEXT,
            problem_position INTEGER,
            solved_at TIMESTAMP,
            level INTEGER,
            rating_change INTEGER
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                sp.id,
                sp.problem_id,
                sp.problem_title,
                sp.position as problem_position,
                sp.solved_at,
                p.level,
                25 as rating_change  -- Valor por defecto, se podría calcular basado en nivel y rating
            FROM 
                solved_problems sp
            LEFT JOIN 
                problems p ON sp.problem_id = p.problem_id
            WHERE 
                sp.user_id = p_user_id
            ORDER BY 
                sp.solved_at DESC;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        print("✅ Función get_solved_problems creada correctamente")
        
        # 5. Verificar si hay problemas que están marcados como solved en ladder_problems
        # pero no están en solved_problems (inconsistencia)
        cursor.execute("""
        SELECT lp.id, lp.problem_id, lp.problem_title, lp.position, lp.baekjoon_username
        FROM ladder_problems lp
        LEFT JOIN solved_problems sp ON 
            lp.problem_id = sp.problem_id AND
            sp.user_id IN (SELECT user_id FROM baekjoon_accounts WHERE baekjoon_username = lp.baekjoon_username)
        WHERE 
            lp.state = 'solved' AND
            sp.id IS NULL
        """)
        
        inconsistencias = cursor.fetchall()
        
        if inconsistencias:
            print("\n⚠️ Se encontraron problemas resueltos en ladder_problems que no están en solved_problems:")
            print(f"{'ID':<5} | {'Problem ID':<10} | {'Title':<40} | {'Position':<10} | {'Username':<15}")
            print("-" * 90)
            for problema in inconsistencias:
                print(f"{problema[0]:<5} | {problema[1]:<10} | {problema[2][:38]:<40} | {problema[3]:<10} | {problema[4]:<15}")
            
            # 6. Preguntar si se desea corregir las inconsistencias
            if "--fix" in sys.argv:
                print("\nCorrigiendo inconsistencias...")
                
                for problema in inconsistencias:
                    # Obtener el user_id a partir del baekjoon_username
                    cursor.execute(
                        "SELECT user_id FROM baekjoon_accounts WHERE baekjoon_username = %s",
                        (problema[4],)
                    )
                    
                    user_result = cursor.fetchone()
                    if user_result:
                        user_id = user_result[0]
                        
                        # Insertar en solved_problems
                        cursor.execute("""
                        INSERT INTO solved_problems 
                        (user_id, problem_id, problem_title, position, solved_at)
                        VALUES (%s, %s, %s, %s, NOW())
                        """, (user_id, problema[1], problema[2], problema[3]))
                        
                        print(f"✅ Problema {problema[1]} añadido a solved_problems para el usuario {user_id}")
                
                conn.commit()
                print("✅ Inconsistencias corregidas")
        
        # 7. Identificar problemas que puedan haber quedado en estado 'current' después de resolverse
        cursor.execute("""
        SELECT lp.id, lp.problem_id, lp.problem_title, lp.state, lp.baekjoon_username
        FROM ladder_problems lp
        JOIN solved_problems sp ON lp.problem_id = sp.problem_id
        JOIN baekjoon_accounts ba ON lp.baekjoon_username = ba.baekjoon_username
        WHERE 
            sp.user_id = ba.user_id AND
            lp.state = 'current'
        """)
        
        problemas_current_resueltos = cursor.fetchall()
        
        if problemas_current_resueltos:
            print("\n⚠️ Se encontraron problemas que están marcados como 'current' pero ya fueron resueltos:")
            print(f"{'ID':<5} | {'Problem ID':<10} | {'Title':<40} | {'State':<10} | {'Username':<15}")
            print("-" * 90)
            for problema in problemas_current_resueltos:
                print(f"{problema[0]:<5} | {problema[1]:<10} | {problema[2][:38]:<40} | {problema[3]:<10} | {problema[4]:<15}")
            
            # 8. Corregir problemas current que deberían ser solved
            if "--fix" in sys.argv:
                print("\nCorrigiendo estados de problemas...")
                
                for problema in problemas_current_resueltos:
                    cursor.execute("""
                    UPDATE ladder_problems
                    SET state = 'solved'
                    WHERE id = %s
                    """, (problema[0],))
                    
                    print(f"✅ Problema {problema[1]} actualizado a estado 'solved'")
                
                conn.commit()
                print("✅ Estados de problemas corregidos")
        
        # 9. Actualizar la función set_revealed_at para usar PostgreSQL
        print("\nCreando función de PostgreSQL para set_revealed_at...")
        
        cursor.execute("""
        CREATE OR REPLACE FUNCTION set_problem_revealed_at(p_problem_id INTEGER) 
        RETURNS TIMESTAMP AS $$
        DECLARE
            v_timestamp TIMESTAMP;
        BEGIN
            -- Usar current_timestamp + 6 horas
            v_timestamp := NOW() + INTERVAL '6 hours';
            
            -- Actualizar revealed_at en el problema
            UPDATE ladder_problems
            SET revealed_at = v_timestamp
            WHERE id = p_problem_id;
            
            RETURN v_timestamp;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        print("✅ Función set_problem_revealed_at creada correctamente")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"ERROR: {str(e)}")
        try:
            conn.rollback()
        except:
            pass
        return False

if __name__ == "__main__":
    if diagnosticar_problemas_resueltos():
        print("\n✨ Diagnóstico completado con éxito ✨")
        print("Para corregir automáticamente las inconsistencias, ejecute:")
        print("python fix_solved_problems.py --fix")
    else:
        print("\n❌ Error durante el diagnóstico.")
        sys.exit(1) 