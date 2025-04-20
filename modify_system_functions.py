#!/usr/bin/env python
import psycopg2
import time

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

problem_id = "21065"  # El problema que queremos asignar
baekjoon_username = "fischer"  # Solo para esta cuenta

print("MODIFICACIÓN TEMPORAL DE FUNCIONES DEL SISTEMA")
print(f"Forzando problema {problem_id} para {baekjoon_username}")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. CREAR RESPALDOS DE LAS FUNCIONES ORIGINALES
    print("\n1. CREANDO RESPALDOS DE FUNCIONES ORIGINALES:")
    
    # Respaldar reveal_next_problem
    cursor.execute("""
    SELECT pg_get_functiondef(oid)
    FROM pg_proc
    WHERE proname = 'reveal_next_problem'
    """)
    reveal_next_problem_original = cursor.fetchone()[0]
    
    # Guardar como una nueva función de respaldo
    cursor.execute("""
    CREATE OR REPLACE FUNCTION reveal_next_problem_backup()
    RETURNS integer
    LANGUAGE plpgsql
    AS $function$
    DECLARE
        dummy INTEGER;
    BEGIN
        RETURN NULL;
    END;
    $function$;
    """)
    
    cursor.execute(f"""
    CREATE OR REPLACE FUNCTION reveal_next_problem_backup()
    RETURNS integer
    LANGUAGE plpgsql
    AS $function${reveal_next_problem_original.split('AS ')[1]}
    """)
    
    print("✅ Función reveal_next_problem respaldada")
    
    # Respaldar reset_ladder_function
    cursor.execute("""
    SELECT pg_get_functiondef(oid)
    FROM pg_proc
    WHERE proname = 'reset_ladder_function'
    """)
    reset_ladder_function_original = cursor.fetchone()[0]
    
    # Guardar como una nueva función de respaldo
    cursor.execute("""
    CREATE OR REPLACE FUNCTION reset_ladder_function_backup(username text)
    RETURNS boolean
    LANGUAGE plpgsql
    AS $function$
    DECLARE
        dummy BOOLEAN;
    BEGIN
        RETURN FALSE;
    END;
    $function$;
    """)
    
    cursor.execute(f"""
    CREATE OR REPLACE FUNCTION reset_ladder_function_backup(username text)
    RETURNS boolean
    LANGUAGE plpgsql
    AS $function${reset_ladder_function_original.split('AS ')[1]}
    """)
    
    print("✅ Función reset_ladder_function respaldada")
    
    # 2. MODIFICAR LAS FUNCIONES PARA FORZAR PROBLEMA 21065
    print("\n2. MODIFICANDO FUNCIONES DEL SISTEMA:")
    
    # Modificar reveal_next_problem para siempre devolver 21065
    cursor.execute("""
    CREATE OR REPLACE FUNCTION reveal_next_problem(p_user_id integer, p_baekjoon_username text)
    RETURNS integer
    LANGUAGE plpgsql
    AS $function$
    DECLARE
        problem_record RECORD;
        new_problem_id INTEGER;
    BEGIN
        -- Solo para fischer, forzar problema 21065
        IF p_baekjoon_username = 'fischer' THEN
            -- Desmarcar cualquier problema current existente
            UPDATE ladder_problems
            SET state = 'hidden'
            WHERE baekjoon_username = p_baekjoon_username AND state = 'current';
            
            -- Obtener información del problema 21065
            SELECT problem_id, problem_title INTO problem_record
            FROM problems
            WHERE problem_id = '21065';
            
            -- Si encontramos el problema
            IF problem_record IS NOT NULL THEN
                -- Insertar o actualizar el problema 21065 como current
                DELETE FROM ladder_problems
                WHERE baekjoon_username = p_baekjoon_username AND problem_id = '21065';
                
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
                VALUES 
                (p_baekjoon_username, 1, problem_record.problem_id, problem_record.problem_title, 'current', NOW())
                RETURNING id INTO new_problem_id;
                
                RAISE NOTICE 'Forzado problema 21065 para fischer';
                
                RETURN new_problem_id;
            END IF;
            
            RETURN NULL;
        ELSE
            -- Para otros usuarios, usar la función de respaldo (comportamiento normal)
            RETURN reveal_next_problem_backup(p_user_id, p_baekjoon_username);
        END IF;
    END;
    $function$;
    """)
    
    print("✅ Función reveal_next_problem modificada")
    
    # Modificar reset_ladder_function para siempre usar 21065
    cursor.execute("""
    CREATE OR REPLACE FUNCTION reset_ladder_function(username text)
    RETURNS boolean
    LANGUAGE plpgsql
    AS $function$
    DECLARE
        problem_record RECORD;
        deleted_count INTEGER;
    BEGIN
        -- Solo para fischer, forzar problema 21065
        IF username = 'fischer' THEN
            -- Limpiar todos los problemas actuales
            DELETE FROM ladder_problems WHERE baekjoon_username = username;
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            
            -- Obtener información del problema 21065
            SELECT problem_id, problem_title INTO problem_record
            FROM problems
            WHERE problem_id = '21065';
            
            -- Si se encontró el problema, agregarlo como 'current'
            IF problem_record IS NOT NULL THEN
                INSERT INTO ladder_problems 
                (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
                VALUES (username, 1, problem_record.problem_id, problem_record.problem_title, 'current', NOW());
                
                RAISE NOTICE 'Forzado problema 21065 para fischer';
                
                RETURN TRUE;
            ELSE
                RETURN FALSE;
            END IF;
        ELSE
            -- Para otros usuarios, usar la función de respaldo (comportamiento normal)
            RETURN reset_ladder_function_backup(username);
        END IF;
    END;
    $function$;
    """)
    
    print("✅ Función reset_ladder_function modificada")
    
    # 3. LIMPIAR Y REINICIAR EL LADDER
    print("\n3. REINICIANDO EL LADDER:")
    
    # Eliminar todos los problemas actuales
    cursor.execute("DELETE FROM ladder_problems WHERE baekjoon_username = %s", (baekjoon_username,))
    deleted = cursor.rowcount
    print(f"✅ Se eliminaron {deleted} problemas del ladder")
    
    # Obtener información del problema 21065
    cursor.execute("SELECT problem_id, problem_title FROM problems WHERE problem_id = %s", (problem_id,))
    problem = cursor.fetchone()
    
    if not problem:
        print(f"❌ Error: El problema {problem_id} no existe en la base de datos")
    else:
        problem_title = problem[1]
        print(f"✅ Problema encontrado: {problem_id} - {problem_title}")
        
        # Insertar el problema como current
        cursor.execute("""
        INSERT INTO ladder_problems 
        (baekjoon_username, position, problem_id, problem_title, state, revealed_at)
        VALUES (%s, %s, %s, %s, 'current', %s)
        """, (baekjoon_username, 1, problem_id, problem_title, time.strftime('%Y-%m-%d %H:%M:%S')))
        
        print(f"✅ Problema {problem_id} agregado manualmente como 'current'")
    
    # 4. CREAR SCRIPT PARA RESTAURAR LAS FUNCIONES ORIGINALES
    print("\n4. CREANDO SCRIPT DE RESTAURACIÓN:")
    
    # Crear archivo de restauración
    with open("restore_functions.py", "w") as f:
        f.write("""#!/usr/bin/env python
import psycopg2

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print("RESTAURANDO FUNCIONES ORIGINALES DEL SISTEMA")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. Restaurar reveal_next_problem
    cursor.execute('''
    SELECT pg_get_functiondef(oid)
    FROM pg_proc
    WHERE proname = 'reveal_next_problem_backup'
    ''')
    reveal_next_problem_backup = cursor.fetchone()[0]
    
    cursor.execute(f'''
    CREATE OR REPLACE FUNCTION reveal_next_problem(p_user_id integer, p_baekjoon_username text)
    RETURNS integer
    LANGUAGE plpgsql
    AS $function${reveal_next_problem_backup.split('AS ')[1].replace('reveal_next_problem_backup', 'reveal_next_problem')}
    ''')
    
    print("✅ Función reveal_next_problem restaurada")
    
    # 2. Restaurar reset_ladder_function
    cursor.execute('''
    SELECT pg_get_functiondef(oid)
    FROM pg_proc
    WHERE proname = 'reset_ladder_function_backup'
    ''')
    reset_ladder_function_backup = cursor.fetchone()[0]
    
    cursor.execute(f'''
    CREATE OR REPLACE FUNCTION reset_ladder_function(username text)
    RETURNS boolean
    LANGUAGE plpgsql
    AS $function${reset_ladder_function_backup.split('AS ')[1].replace('reset_ladder_function_backup', 'reset_ladder_function')}
    ''')
    
    print("✅ Función reset_ladder_function restaurada")
    
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
    
    print("✅ Archivo restore_functions.py creado para restaurar las funciones originales")
    
    conn.commit()
    conn.close()
    
    print("\n✨ MODIFICACIÓN COMPLETA ✨")
    print(f"Las funciones del sistema han sido modificadas para forzar el problema {problem_id}.")
    print("Por favor, sigue estos pasos:")
    print("1. Cierra completamente la aplicación web")
    print("2. Borra el caché del navegador")
    print("3. Reinicia el navegador")
    print("4. Accede nuevamente a la aplicación")
    print("5. Verifica que aparezca el problema 21065")
    print("\nIMPORTANTE: Cuando hayas terminado, ejecuta restore_functions.py para")
    print("restaurar las funciones originales del sistema.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.rollback()
        conn.close()
    except:
        pass 