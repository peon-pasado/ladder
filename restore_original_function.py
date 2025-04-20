#!/usr/bin/env python
import psycopg2

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print("RESTAURANDO FUNCIÓN ORIGINAL")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Restaurar la función original
    reset_ladder_original = '''
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
            
            -- Seleccionar un problema aleatorio
            SELECT problem_id, problem_title INTO problem_record
            FROM problems
            ORDER BY RANDOM()
            LIMIT 1;
            
            -- Si se encontró un problema, agregarlo como 'current'
            IF problem_record IS NOT NULL THEN
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state)
                VALUES (username, 1, problem_record.problem_id, problem_record.problem_title, 'current');
                
                RAISE NOTICE 'Se agregó el problema % (%) como current para %', 
                      problem_record.problem_id, problem_record.problem_title, username;
                
                RETURN TRUE;
            ELSE
                -- Si no hay problemas en la BD, usar el problema predeterminado
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state)
                VALUES (username, 1, '21065', 'Friendship Circles', 'current');
                
                RAISE NOTICE 'No se encontraron problemas aleatorios. Se agregó el problema predeterminado 21065 para %', username;
                
                RETURN TRUE;
            END IF;
            
            RETURN FALSE;
        END;
        $function$;
    '''
    
    cursor.execute(reset_ladder_original)
    print("✅ Función reset_ladder_function restaurada a su versión original")
    
    conn.commit()
    conn.close()
    
    print("\n✨ RESTAURACIÓN COMPLETADA ✨")
    print("Las funciones del sistema han sido restauradas a su estado original.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass
