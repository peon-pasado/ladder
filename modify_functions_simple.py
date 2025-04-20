#!/usr/bin/env python
import psycopg2
import time

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

problem_id = "21065"  # El problema que queremos asignar
baekjoon_username = "fischer"  # Solo para esta cuenta

print("MODIFICACIÓN SIMPLIFICADA DE FUNCIONES DEL SISTEMA")
print(f"Forzando problema {problem_id} para {baekjoon_username}")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. MODIFICAR reset_ladder_function PARA SIEMPRE USAR 21065
    print("\n1. MODIFICANDO FUNCIÓN reset_ladder_function:")
    
    reset_ladder_new = """
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
        
        -- Fischer siempre usa 21065
        IF username = 'fischer' THEN
            -- Buscar el problema 21065
            SELECT problem_id, problem_title INTO problem_record
            FROM problems
            WHERE problem_id = '21065';
            
            -- Si existe, asignarlo
            IF problem_record IS NOT NULL THEN
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
                VALUES (username, 1, problem_record.problem_id, problem_record.problem_title, 'current', NOW());
                
                RAISE NOTICE 'Reset ladder para fischer con problema 21065';
                RETURN TRUE;
            END IF;
            
            RETURN FALSE;
        ELSE
            -- Otros usuarios usan problema aleatorio (comportamiento original)
            SELECT problem_id, problem_title INTO problem_record
            FROM problems
            ORDER BY RANDOM()
            LIMIT 1;
            
            -- Si se encontró un problema, agregarlo como 'current'
            IF problem_record IS NOT NULL THEN
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
                VALUES (username, 1, problem_record.problem_id, problem_record.problem_title, 'current', NOW());
                
                RETURN TRUE;
            END IF;
            
            RETURN FALSE;
        END IF;
    END;
    $function$;
    """
    
    cursor.execute(reset_ladder_new)
    print("✅ Función reset_ladder_function modificada")
    
    # 2. LIMPIAR Y REINICIAR EL LADDER
    print("\n2. REINICIANDO EL LADDER:")
    
    # Eliminar todos los problemas actuales
    cursor.execute("DELETE FROM ladder_problems WHERE baekjoon_username = %s", (baekjoon_username,))
    deleted = cursor.rowcount
    print(f"✅ Se eliminaron {deleted} problemas del ladder")
    
    # Llamar directamente a la función reset_ladder_function
    cursor.execute("SELECT reset_ladder_function(%s)", (baekjoon_username,))
    result = cursor.fetchone()[0]
    
    if result:
        print(f"✅ Ladder reiniciado correctamente con reset_ladder_function")
    else:
        print(f"❌ Error al reiniciar el ladder")
    
    # 3. VERIFICAR EL LADDER
    cursor.execute("""
    SELECT id, position, problem_id, problem_title, state, revealed_at 
    FROM ladder_problems
    WHERE baekjoon_username = %s
    ORDER BY position
    """, (baekjoon_username,))
    
    ladder = cursor.fetchall()
    print(f"\nLadder actual para {baekjoon_username}:")
    for p in ladder:
        print(f"ID: {p[0]}, Pos: {p[1]}, Problema: {p[2]}, Título: {p[3]}, Estado: {p[4]}, Revelado: {p[5]}")
    
    # 4. CREAR SCRIPT DE RESTAURACIÓN
    print("\n3. CREANDO SCRIPT DE RESTAURACIÓN:")
    
    with open("restore_original_function.py", "w") as f:
        f.write("""#!/usr/bin/env python
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
    
    print("\\n✨ RESTAURACIÓN COMPLETADA ✨")
    print("Las funciones del sistema han sido restauradas a su estado original.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass
""")
    
    print("✅ Archivo restore_original_function.py creado")
    
    conn.commit()
    conn.close()
    
    print("\n✨ MODIFICACIÓN COMPLETA ✨")
    print(f"La función reset_ladder_function ha sido modificada para que fischer")
    print(f"siempre reciba el problema {problem_id}.")
    print("\nPor favor, sigue estos pasos:")
    print("1. Cierra completamente la aplicación web")
    print("2. Borra el caché del navegador")
    print("3. Reinicia el navegador")
    print("4. Accede nuevamente a la aplicación")
    print("5. Verifica que aparezca el problema 21065")
    print("\nIMPORTANTE: Cuando hayas terminado, ejecuta restore_original_function.py")
    print("para restaurar la función original del sistema.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 