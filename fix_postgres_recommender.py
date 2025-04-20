#!/usr/bin/env python
import os
import sys
import psycopg2
from datetime import datetime, timezone
import random

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print("Este script implementará la funcionalidad del recomendador de problemas en PostgreSQL")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

def crear_funciones_recomendador():
    """
    Crea funciones en PostgreSQL para reemplazar el ProblemRecommender de Python
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # 1. Crear función para calcular buchholz
        cursor.execute("""
        CREATE OR REPLACE FUNCTION calculate_buchholz(p_user_id INTEGER) 
        RETURNS INTEGER AS $$
        DECLARE
            avg_level FLOAT;
            user_rating INTEGER;
            max_buchholz INTEGER := 500;
            buchholz INTEGER;
        BEGIN
            -- Obtener el promedio del nivel de los últimos 5 problemas resueltos
            WITH recent_problems AS (
                SELECT p.level
                FROM solved_problems sp
                JOIN problems p ON sp.problem_id = p.problem_id
                WHERE sp.user_id = p_user_id
                AND p.level IS NOT NULL 
                AND p.level > 0
                ORDER BY sp.solved_at DESC
                LIMIT 5
            )
            SELECT AVG(level)
            INTO avg_level
            FROM recent_problems;
            
            -- Si no hay datos, retornar 0
            IF avg_level IS NULL THEN
                RETURN 0;
            END IF;
            
            -- Obtener el rating actual del usuario
            SELECT rating INTO user_rating
            FROM users
            WHERE id = p_user_id;
            
            -- Si no hay rating, usar valor por defecto
            IF user_rating IS NULL THEN
                user_rating := 1500;
            END IF;
            
            -- Calcular buchholz (diferencia respecto al rating)
            buchholz := ROUND(avg_level - user_rating);
            
            -- Limitar el valor para evitar extremos
            RETURN GREATEST(-max_buchholz, LEAST(max_buchholz, buchholz));
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        print("✅ Función calculate_buchholz creada correctamente")
        
        # 2. Crear función para revelar el siguiente problema
        cursor.execute("""
        CREATE OR REPLACE FUNCTION reveal_next_problem(p_user_id INTEGER, p_baekjoon_username TEXT) 
        RETURNS INTEGER AS $$
        DECLARE
            next_position INTEGER;
            user_rating INTEGER;
            buchholz INTEGER;
            target_rating INTEGER;
            min_level INTEGER;
            max_level INTEGER;
            problem_record RECORD;
            new_problem_id INTEGER;
            level_range_offset INTEGER := 250;
            buchholz_weight FLOAT := 0.3;
            random_offset INTEGER;
        BEGIN
            -- Generar offset aleatorio para variedad
            random_offset := floor(random() * 100) - 50;
            
            -- Encontrar la siguiente posición
            SELECT position INTO next_position
            FROM ladder_problems
            WHERE baekjoon_username = p_baekjoon_username AND state = 'current';
            
            IF next_position IS NOT NULL THEN
                -- Si hay un problema actual, la siguiente posición será la actual + 1
                next_position := next_position + 1;
            ELSE
                -- Si no hay problema actual, verificar la posición máxima
                SELECT COALESCE(MAX(position), 0) + 1 INTO next_position
                FROM ladder_problems
                WHERE baekjoon_username = p_baekjoon_username;
            END IF;
            
            -- Obtener el rating actual del usuario
            SELECT rating INTO user_rating
            FROM users
            WHERE id = p_user_id;
            
            IF user_rating IS NULL THEN
                user_rating := 1500;
            END IF;
            
            -- Calcular el buchholz
            buchholz := calculate_buchholz(p_user_id);
            
            -- Ajustar el rating objetivo según el buchholz
            target_rating := user_rating + ROUND(buchholz * buchholz_weight);
            
            -- Rango de niveles a buscar
            min_level := target_rating - level_range_offset + random_offset;
            max_level := target_rating + level_range_offset + random_offset;
            
            -- Primero desmarcar cualquier problema current existente
            UPDATE ladder_problems
            SET state = 'hidden'
            WHERE baekjoon_username = p_baekjoon_username AND state = 'current';
            
            -- Buscar un nuevo problema en el rango ideal
            WITH existing_problems AS (
                SELECT problem_id
                FROM ladder_problems
                WHERE baekjoon_username = p_baekjoon_username
            ),
            candidates AS (
                SELECT problem_id, problem_title, level
                FROM problems
                WHERE level BETWEEN min_level AND max_level
                AND problem_id NOT IN (SELECT problem_id FROM existing_problems)
                ORDER BY RANDOM()
                LIMIT 10
            )
            SELECT problem_id, problem_title INTO problem_record
            FROM candidates
            LIMIT 1;
            
            -- Si encontramos un problema en el rango ideal
            IF problem_record IS NOT NULL THEN
                -- Insertar el nuevo problema como current
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
                VALUES 
                (p_baekjoon_username, next_position, problem_record.problem_id, problem_record.problem_title, 'current', NOW() + INTERVAL '6 hours')
                RETURNING id INTO new_problem_id;
                
                RETURN new_problem_id;
            END IF;
            
            -- Si no hay candidatos en el rango ideal, ampliar la búsqueda
            min_level := target_rating - (level_range_offset * 2);
            max_level := target_rating + (level_range_offset * 2);
            
            WITH existing_problems AS (
                SELECT problem_id
                FROM ladder_problems
                WHERE baekjoon_username = p_baekjoon_username
            ),
            wider_candidates AS (
                SELECT problem_id, problem_title, level
                FROM problems
                WHERE level BETWEEN min_level AND max_level
                AND problem_id NOT IN (SELECT problem_id FROM existing_problems)
                ORDER BY RANDOM()
                LIMIT 5
            )
            SELECT problem_id, problem_title INTO problem_record
            FROM wider_candidates
            LIMIT 1;
            
            -- Si encontramos un problema en el rango ampliado
            IF problem_record IS NOT NULL THEN
                -- Insertar el nuevo problema como current
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
                VALUES 
                (p_baekjoon_username, next_position, problem_record.problem_id, problem_record.problem_title, 'current', NOW() + INTERVAL '6 hours')
                RETURNING id INTO new_problem_id;
                
                RETURN new_problem_id;
            END IF;
            
            -- Como último recurso, cualquier problema no usado
            WITH existing_problems AS (
                SELECT problem_id
                FROM ladder_problems
                WHERE baekjoon_username = p_baekjoon_username
            ),
            fallback AS (
                SELECT problem_id, problem_title
                FROM problems
                WHERE problem_id NOT IN (SELECT problem_id FROM existing_problems)
                ORDER BY RANDOM()
                LIMIT 1
            )
            SELECT problem_id, problem_title INTO problem_record
            FROM fallback
            LIMIT 1;
            
            -- Si encontramos algún problema
            IF problem_record IS NOT NULL THEN
                -- Insertar el nuevo problema como current
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
                VALUES 
                (p_baekjoon_username, next_position, problem_record.problem_id, problem_record.problem_title, 'current', NOW() + INTERVAL '6 hours')
                RETURNING id INTO new_problem_id;
                
                RETURN new_problem_id;
            END IF;
            
            -- Si no se pudo encontrar ningún problema
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        print("✅ Función reveal_next_problem creada correctamente")
        
        # 3. Crear o actualizar la función save_solved_problem para usar el nuevo recomendador
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
            v_next_problem_id INTEGER;
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
                -- Llamar a la nueva función para revelar el siguiente problema
                v_next_problem_id := reveal_next_problem(p_user_id, v_baekjoon_username);
                
                IF v_next_problem_id IS NOT NULL THEN
                    RAISE NOTICE 'Nuevo problema revelado: %', v_next_problem_id;
                ELSE
                    RAISE NOTICE 'No se pudo revelar un nuevo problema';
                END IF;
            END IF;
            
            RETURN TRUE;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        print("✅ Función save_solved_problem actualizada correctamente")
        
        # 4. Prueba del recomendador para el usuario 1 (admin)
        if "--test" in sys.argv:
            cursor.execute("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
            admin_result = cursor.fetchone()
            
            if admin_result:
                admin_id = admin_result[0]
                
                cursor.execute("""
                SELECT baekjoon_username 
                FROM baekjoon_accounts 
                WHERE user_id = %s 
                LIMIT 1
                """, (admin_id,))
                
                baekjoon_result = cursor.fetchone()
                
                if baekjoon_result:
                    baekjoon_username = baekjoon_result[0]
                    
                    print(f"\n🧪 Probando el recomendador para usuario {admin_id} (baekjoon: {baekjoon_username})")
                    
                    # Calcular buchholz
                    cursor.execute("SELECT calculate_buchholz(%s)", (admin_id,))
                    buchholz = cursor.fetchone()[0]
                    print(f"Buchholz calculado: {buchholz}")
                    
                    # Revelar siguiente problema
                    cursor.execute("SELECT reveal_next_problem(%s, %s)", (admin_id, baekjoon_username))
                    new_problem_id = cursor.fetchone()[0]
                    
                    if new_problem_id:
                        print(f"Nuevo problema revelado con ID: {new_problem_id}")
                        
                        # Mostrar detalles del problema
                        cursor.execute("""
                        SELECT id, position, problem_id, problem_title, state, revealed_at
                        FROM ladder_problems
                        WHERE id = %s
                        """, (new_problem_id,))
                        
                        problem = cursor.fetchone()
                        if problem:
                            print(f"Problema recomendado:")
                            print(f"  ID: {problem[0]}")
                            print(f"  Posición: {problem[1]}")
                            print(f"  Problem ID: {problem[2]}")
                            print(f"  Título: {problem[3]}")
                            print(f"  Estado: {problem[4]}")
                            print(f"  Revealed At: {problem[5]}")
                    else:
                        print("No se pudo revelar un nuevo problema (quizás no hay problemas disponibles)")
                else:
                    print("No se encontró cuenta de Baekjoon para el usuario admin")
            else:
                print("No se encontró usuario admin")
        
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
    if crear_funciones_recomendador():
        print("\n✨ ¡Funciones del recomendador creadas con éxito! ✨")
        print("Ahora el sistema de recomendación de problemas está implementado en PostgreSQL")
        print("Cuando un usuario resuelva un problema, el sistema automáticamente:")
        print("1. Actualizará su rating")
        print("2. Calculará su buchholz")
        print("3. Seleccionará un nuevo problema apropiado")
        print("\nPara probar el recomendador, ejecute:")
        print("python fix_postgres_recommender.py --test")
        sys.exit(0)
    else:
        print("\n❌ Error al crear las funciones del recomendador.")
        sys.exit(1) 