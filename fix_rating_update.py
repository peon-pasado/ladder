#!/usr/bin/env python
import os
import sys
import psycopg2
from datetime import datetime, timezone

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print("Este script aplicará un parche para corregir la actualización de ratings al resolver problemas")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

def aplicar_parche_rating():
    """
    Crea funciones en PostgreSQL para manejar la actualización de ratings
    cuando un problema es verificado como resuelto.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # 1. Crear función para calcular cambio de rating
        cursor.execute("""
        CREATE OR REPLACE FUNCTION calculate_rating_change(current_rating INTEGER, problem_level INTEGER) 
        RETURNS INTEGER AS $$
        DECLARE
            delta INTEGER;
            factor FLOAT;
        BEGIN
            -- Factor base para el cambio de rating
            factor := 0.05;
            
            -- Diferencia de niveles
            delta := problem_level - current_rating;
            
            -- Si el problema es más difícil, el aumento es mayor
            IF delta > 0 THEN
                -- Para problemas más difíciles, factor aumenta
                factor := factor * (1.0 + (delta::FLOAT / 1000.0));
                
                -- Calcular aumento base (redondeado)
                RETURN ROUND(problem_level * factor);
            ELSE
                -- Para problemas más fáciles, factor disminuye pero siempre hay algo de aumento
                factor := factor * (0.5 + (500.0 / (ABS(delta) + 500.0)));
                
                -- Calcular aumento base (redondeado)
                RETURN GREATEST(25, ROUND(problem_level * factor));
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        print("✅ Función calculate_rating_change creada correctamente")
        
        # 2. Crear función para guardar problema resuelto
        cursor.execute("""
        CREATE OR REPLACE FUNCTION save_solved_problem(
            p_user_id INTEGER, 
            p_problem_id TEXT, 
            p_problem_title TEXT, 
            p_position INTEGER
        ) RETURNS BOOLEAN AS $$
        DECLARE
            v_baekjoon_username TEXT;
            v_problem_level INTEGER;
            v_current_rating INTEGER;
            v_delta_rating INTEGER;
            v_solved_at TIMESTAMP;
        BEGIN
            -- Obtener la hora actual
            v_solved_at := NOW();
            
            -- Insertar en solved_problems
            INSERT INTO solved_problems 
            (user_id, problem_id, problem_title, position, solved_at)
            VALUES 
            (p_user_id, p_problem_id, p_problem_title, p_position, v_solved_at);
            
            -- Marcar el problema como resuelto en ladder_problems
            UPDATE ladder_problems 
            SET state = 'solved' 
            WHERE problem_id = p_problem_id AND baekjoon_username IN (
                SELECT baekjoon_username FROM baekjoon_accounts WHERE user_id = p_user_id
            );
            
            -- Obtener el nivel del problema
            SELECT level INTO v_problem_level 
            FROM problems 
            WHERE problem_id = p_problem_id;
            
            -- Si no se encuentra el nivel, usar un valor predeterminado
            IF v_problem_level IS NULL THEN
                v_problem_level := 1500;
            END IF;
            
            -- Obtener el rating actual del usuario
            SELECT rating INTO v_current_rating 
            FROM users 
            WHERE id = p_user_id;
            
            -- Si no se encuentra el rating, usar un valor predeterminado
            IF v_current_rating IS NULL THEN
                v_current_rating := 1500;
            END IF;
            
            -- Calcular el cambio de rating
            v_delta_rating := calculate_rating_change(v_current_rating, v_problem_level);
            
            -- Actualizar el rating del usuario
            UPDATE users 
            SET rating = rating + v_delta_rating
            WHERE id = p_user_id;
            
            -- Obtener el nombre de usuario de Baekjoon
            SELECT baekjoon_username INTO v_baekjoon_username 
            FROM baekjoon_accounts 
            WHERE user_id = p_user_id 
            LIMIT 1;
            
            -- Si tenemos el nombre de usuario, revelar el siguiente problema recomendado
            IF v_baekjoon_username IS NOT NULL THEN
                -- Llamar a una función para revelar el siguiente problema
                -- (Esta función tendría que ser implementada por separado)
                -- Por ahora, revelamos un problema aleatorio como muestra
                
                -- Primero marcamos todos los problemas como no current
                UPDATE ladder_problems
                SET state = 'hidden'
                WHERE baekjoon_username = v_baekjoon_username AND state = 'current';
                
                -- Seleccionar un nuevo problema aleatorio y marcarlo como current
                WITH new_problem AS (
                    SELECT problem_id, problem_title
                    FROM problems
                    WHERE problem_id NOT IN (
                        SELECT problem_id FROM ladder_problems
                        WHERE baekjoon_username = v_baekjoon_username
                    )
                    ORDER BY RANDOM()
                    LIMIT 1
                )
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
                SELECT 
                    v_baekjoon_username, 
                    COALESCE((SELECT MAX(position) FROM ladder_problems WHERE baekjoon_username = v_baekjoon_username), 0) + 1,
                    problem_id, 
                    problem_title, 
                    'current',
                    NOW() + INTERVAL '6 hours'
                FROM new_problem;
            END IF;
            
            RETURN TRUE;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        print("✅ Función save_solved_problem creada correctamente")
        
        # 3. Crear función para verificar un problema como resuelto
        cursor.execute("""
        CREATE OR REPLACE FUNCTION verify_solved_problem(
            p_problem_id INTEGER,
            p_user_id INTEGER
        ) RETURNS BOOLEAN AS $$
        DECLARE
            v_problem_data RECORD;
            v_baekjoon_username TEXT;
            v_success BOOLEAN;
        BEGIN
            -- Obtener información del problema
            SELECT lp.position, lp.problem_id, lp.problem_title, lp.baekjoon_username
            INTO v_problem_data
            FROM ladder_problems lp
            WHERE lp.id = p_problem_id;
            
            IF v_problem_data IS NULL THEN
                RETURN FALSE;
            END IF;
            
            -- Verificar que la cuenta pertenezca al usuario
            SELECT ba.baekjoon_username INTO v_baekjoon_username
            FROM baekjoon_accounts ba
            WHERE ba.user_id = p_user_id
            AND ba.baekjoon_username = v_problem_data.baekjoon_username;
            
            IF v_baekjoon_username IS NULL THEN
                RETURN FALSE;
            END IF;
            
            -- Actualizar el estado del problema a 'solved'
            UPDATE ladder_problems
            SET state = 'solved'
            WHERE id = p_problem_id;
            
            -- Llamar a la función para guardar el problema resuelto
            v_success := save_solved_problem(
                p_user_id,
                v_problem_data.problem_id,
                v_problem_data.problem_title,
                v_problem_data.position
            );
            
            RETURN v_success;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        print("✅ Función verify_solved_problem creada correctamente")
        
        # 4. Instrucciones para corregir la aplicación Python
        print("\n⚠️ IMPORTANTE: Para usar estas funciones desde la aplicación Python, necesitarás:")
        print("1. Actualizar la ruta '/account/<int:account_id>/ladder/problem/<int:problem_id>/verify' para usar PostgreSQL")
        print("2. Llamar directamente a la función de PostgreSQL verify_solved_problem en lugar de usar SQLite")
        
        # Ejemplo de código que podríamos usar para corregirlo en Python
        print("\nA continuación, algunos ejemplos de código modificado para verificar problemas:")
        print("```python")
        print("# En la ruta verify_problem_solved:")
        print("conn = psycopg2.connect(DATABASE_URL)")
        print("cursor = conn.cursor()")
        print("cursor.execute('SELECT verify_solved_problem(%s, %s)', (problem_id, current_user.id))")
        print("result = cursor.fetchone()[0]")
        print("conn.commit()")
        print("conn.close()")
        print("```")
        
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
    if aplicar_parche_rating():
        print("\n✨ ¡Parche para ratings aplicado con éxito! ✨")
        print("Ahora cuando verifiques un problema como resuelto:")
        print("1. Se actualizará el rating del usuario correctamente")
        print("2. Se seleccionará un nuevo problema aleatorio como 'current'")
        print("3. Todo se mantendrá en sincronía usando PostgreSQL")
        
        print("\nPara probar el cambio, verifica un problema y observa si el rating aumenta.")
        sys.exit(0)
    else:
        print("\n❌ Error al aplicar el parche.")
        sys.exit(1) 