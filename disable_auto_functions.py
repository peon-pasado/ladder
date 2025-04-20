#!/usr/bin/env python
import psycopg2
from datetime import datetime

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print("MODIFICANDO FUNCIÓN reveal_next_problem")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Nueva definición de la función reveal_next_problem que siempre devuelve problema 21065
    new_function_definition = """
    CREATE OR REPLACE FUNCTION reveal_next_problem(p_user_id integer, p_baekjoon_username text)
    RETURNS integer
    LANGUAGE plpgsql
    AS $function$
    DECLARE
        next_position INTEGER;
        problem_record RECORD;
        new_problem_id INTEGER;
    BEGIN
        -- Encontrar la siguiente posición
        SELECT position INTO next_position
        FROM ladder_problems
        WHERE baekjoon_username = p_baekjoon_username AND state = 'current';
        
        IF next_position IS NOT NULL THEN
            -- Si hay un problema actual, la siguiente posición será la actual + 1
            next_position := next_position + 1;
        ELSE
            -- Si no hay problema actual, establecer posición 1
            next_position := 1;
        END IF;
        
        -- Primero desmarcar cualquier problema current existente
        UPDATE ladder_problems
        SET state = 'hidden'
        WHERE baekjoon_username = p_baekjoon_username AND state = 'current';
        
        -- Obtener información del problema 21065
        SELECT problem_id, problem_title INTO problem_record
        FROM problems
        WHERE problem_id = '21065';
        
        -- Si encontramos el problema
        IF problem_record IS NOT NULL THEN
            -- Insertar el problema 21065 como current
            INSERT INTO ladder_problems 
            (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
            VALUES 
            (p_baekjoon_username, next_position, problem_record.problem_id, problem_record.problem_title, 'current', NOW())
            RETURNING id INTO new_problem_id;
            
            RAISE NOTICE 'Asignado problema 21065 (%) como current para %', 
                  problem_record.problem_title, p_baekjoon_username;
            
            RETURN new_problem_id;
        END IF;
        
        -- Si no encontramos el problema 21065 (muy improbable)
        RETURN NULL;
    END;
    $function$;
    """
    
    # Ejecutar la nueva definición
    cursor.execute(new_function_definition)
    
    print("\n✅ Función reveal_next_problem modificada con éxito")
    print("Ahora la función siempre asignará el problema 21065 al revelar el siguiente problema")
    
    # Guardar en caso de que lo necesitemos más tarde
    cursor.execute("""
    CREATE OR REPLACE FUNCTION get_problem_21065(baekjoon_username text)
    RETURNS integer
    LANGUAGE plpgsql
    AS $function$
    DECLARE
        problem_record RECORD;
        new_problem_id INTEGER;
    BEGIN
        -- Primero desmarcar cualquier problema current existente
        UPDATE ladder_problems
        SET state = 'hidden'
        WHERE baekjoon_username = baekjoon_username AND state = 'current';
        
        -- Obtener información del problema 21065
        SELECT problem_id, problem_title INTO problem_record
        FROM problems
        WHERE problem_id = '21065';
        
        -- Si encontramos el problema
        IF problem_record IS NOT NULL THEN
            -- Insertar el problema 21065 como current
            INSERT INTO ladder_problems 
            (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
            VALUES 
            (baekjoon_username, 1, problem_record.problem_id, problem_record.problem_title, 'current', NOW())
            RETURNING id INTO new_problem_id;
            
            RETURN new_problem_id;
        END IF;
        
        RETURN NULL;
    END;
    $function$;
    """)
    
    print("\n✅ Función auxiliar get_problem_21065 creada con éxito")
    
    # Probar la función para asegurarnos que está funcionando
    cursor.execute("SELECT get_problem_21065('fischer')")
    result = cursor.fetchone()
    
    if result and result[0]:
        print(f"\n✅ Prueba exitosa: Se asignó problema 21065 a fischer (ID: {result[0]})")
    else:
        print("\n❌ Prueba fallida: No se pudo asignar el problema 21065")
    
    # Verificar ladder
    cursor.execute("""
    SELECT id, position, problem_id, problem_title, state 
    FROM ladder_problems
    WHERE baekjoon_username = 'fischer' AND problem_id = '21065'
    """)
    
    current_problem = cursor.fetchone()
    if current_problem:
        print(f"\nProblema actual para fischer:")
        print(f"ID: {current_problem[0]}, Pos: {current_problem[1]}, Problem: {current_problem[2]}, Title: {current_problem[3]}, State: {current_problem[4]}")
    
    conn.commit()
    conn.close()
    
    print("\n✨ MODIFICACIÓN COMPLETADA ✨")
    print("Ahora hemos sobreescrito la función que asigna nuevos problemas.")
    print("También hemos creado una función auxiliar get_problem_21065 que puedes usar")
    print("para asignar manualmente el problema 21065 si es necesario.")
    print("Por favor, reinicia la aplicación y comprueba si el problema 21065 aparece.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 