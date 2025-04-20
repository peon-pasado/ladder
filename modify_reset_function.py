#!/usr/bin/env python
import psycopg2

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print("MODIFICANDO FUNCIÓN reset_ladder_function")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Nueva definición de la función que siempre usará el problema 21065
    new_function_definition = """
    CREATE OR REPLACE FUNCTION reset_ladder_function(username text)
    RETURNS boolean
    LANGUAGE plpgsql
    AS $function$
    DECLARE
        problem_record RECORD;
        deleted_count INTEGER;
    BEGIN
        -- Limpiar todos los problemas actuales
        DELETE FROM ladder_problems WHERE baekjoon_username = username;
        GET DIAGNOSTICS deleted_count = ROW_COUNT;
        
        -- Registrar cuántos problemas se eliminaron
        RAISE NOTICE 'Se eliminaron % problemas del ladder para %', deleted_count, username;
        
        -- ¡CAMBIO! Siempre usar el problema 21065
        SELECT problem_id, problem_title INTO problem_record
        FROM problems
        WHERE problem_id = '21065';
        
        -- Si se encontró el problema, agregarlo como 'current'
        IF problem_record IS NOT NULL THEN
            INSERT INTO ladder_problems 
            (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
            VALUES (username, 1, problem_record.problem_id, problem_record.problem_title, 'current', NOW());
            
            RAISE NOTICE 'Se agregó el problema 21065 (%) como current para %', 
                  problem_record.problem_title, username;
            
            RETURN TRUE;
        ELSE
            -- Si no existe el problema 21065 (muy improbable), usar cualquier problema
            SELECT problem_id, problem_title INTO problem_record
            FROM problems
            ORDER BY RANDOM()
            LIMIT 1;
            
            IF problem_record IS NOT NULL THEN
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
                VALUES (username, 1, problem_record.problem_id, problem_record.problem_title, 'current', NOW());
                
                RAISE NOTICE 'No se encontró el problema 21065. Se agregó % (%) para %',
                      problem_record.problem_id, problem_record.problem_title, username;
                
                RETURN TRUE;
            END IF;
        END IF;
        
        RETURN FALSE;
    END;
    $function$;
    """
    
    # Ejecutar la nueva definición
    cursor.execute(new_function_definition)
    
    print("\n✅ Función reset_ladder_function modificada con éxito")
    print("Ahora la función siempre asignará el problema 21065 al reiniciar el ladder")
    
    # Verificar la modificación
    cursor.execute("""
    SELECT pg_get_functiondef(oid)
    FROM pg_proc
    WHERE proname = 'reset_ladder_function'
    """)
    
    definition = cursor.fetchone()
    if definition:
        print("\nNueva definición de la función:")
        print(definition[0])
    
    # Probar la función con el usuario fischer
    print("\nProbando la función con el usuario fischer:")
    cursor.execute("SELECT reset_ladder_function('fischer')")
    result = cursor.fetchone()
    print(f"Resultado: {result[0]}")
    
    # Verificar el ladder después de la modificación
    cursor.execute("""
    SELECT id, position, problem_id, problem_title, state, revealed_at 
    FROM ladder_problems
    WHERE baekjoon_username = 'fischer'
    ORDER BY position
    """)
    
    ladder = cursor.fetchall()
    print("\nEstado del ladder después de la modificación:")
    for p in ladder:
        print(f"ID: {p[0]}, Pos: {p[1]}, Problem: {p[2]}, Título: {p[3]}, Estado: {p[4]}, Revelado: {p[5]}")
    
    conn.commit()
    conn.close()
    
    print("\n✨ MODIFICACIÓN COMPLETADA ✨")
    print("Ahora, cada vez que se reinicie el ladder, se asignará específicamente")
    print("el problema 21065 (Friendship Circles) para el usuario fischer.")
    print("Por favor, reinicia la aplicación web y comprueba si el cambio persiste.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 