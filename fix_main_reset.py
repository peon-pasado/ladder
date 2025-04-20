#!/usr/bin/env python
import os
import sys
import psycopg2
from datetime import datetime, timezone

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print("Este script aplicará un parche temporal para corregir el funcionamiento del reset del ladder")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

def aplicar_parche():
    """
    Este script crea una función en PostgreSQL que será llamada cuando se reinicie el ladder.
    La función asegurará que solo un problema aleatorio se seleccione como 'current'.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Definir la función de PostgreSQL para reset del ladder que implementa
        # la misma lógica que hemos corregido
        cursor.execute("""
        CREATE OR REPLACE FUNCTION reset_ladder_function(username TEXT) 
        RETURNS BOOLEAN AS $$
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
        $$ LANGUAGE plpgsql;
        """)
        
        print("\n✅ Función reset_ladder_function creada correctamente en PostgreSQL")
        
        # Crear un trigger que evite que se inserten múltiples problemas con estado 'current'
        cursor.execute("""
        CREATE OR REPLACE FUNCTION check_current_problems() 
        RETURNS TRIGGER AS $$
        DECLARE
            current_count INTEGER;
        BEGIN
            -- Si estamos intentando insertar un problema 'current'
            IF NEW.state = 'current' THEN
                -- Contar cuántos problemas 'current' ya existen para este usuario
                SELECT COUNT(*) INTO current_count
                FROM ladder_problems
                WHERE baekjoon_username = NEW.baekjoon_username
                AND state = 'current'
                AND id != COALESCE(NEW.id, -1);
                
                -- Si ya hay problemas 'current', convertir los existentes a 'hidden'
                IF current_count > 0 THEN
                    UPDATE ladder_problems
                    SET state = 'hidden'
                    WHERE baekjoon_username = NEW.baekjoon_username
                    AND state = 'current'
                    AND id != COALESCE(NEW.id, -1);
                    
                    RAISE NOTICE 'Se actualizaron % problemas current a hidden para %', 
                          current_count, NEW.baekjoon_username;
                END IF;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        # Intentar eliminar el trigger si ya existe
        try:
            cursor.execute("""
            DROP TRIGGER IF EXISTS ensure_one_current_problem ON ladder_problems;
            """)
        except Exception as e:
            print(f"Advertencia al eliminar trigger: {str(e)}")
        
        # Crear el trigger
        cursor.execute("""
        CREATE TRIGGER ensure_one_current_problem
        BEFORE INSERT OR UPDATE ON ladder_problems
        FOR EACH ROW
        EXECUTE FUNCTION check_current_problems();
        """)
        
        print("✅ Trigger ensure_one_current_problem creado correctamente")
        print("\nEl parche ha sido aplicado con éxito. Ahora al reiniciar el ladder:")
        print(" 1. Se seleccionará un solo problema aleatorio")
        print(" 2. Solo habrá un problema 'current' en el ladder")
        
        # Verificar que todo funciona probando con un usuario específico
        # Solo es para demostración, no es necesario ejecutarlo
        if "--test" in sys.argv:
            cursor.execute("SELECT baekjoon_username FROM baekjoon_accounts WHERE user_id = 1")
            username = cursor.fetchone()[0]
            if username:
                print(f"\n🧪 Probando el reset con el usuario {username}...")
                cursor.execute("SELECT reset_ladder_function(%s)", (username,))
                result = cursor.fetchone()[0]
                print(f"Resultado del test: {'ÉXITO' if result else 'FALLÓ'}")
                
                # Mostrar el estado actual del ladder
                cursor.execute("""
                SELECT id, position, problem_id, problem_title, state
                FROM ladder_problems 
                WHERE baekjoon_username = %s
                ORDER BY position
                """, (username,))
                ladder = cursor.fetchall()
                
                if ladder:
                    print("\nEstado actual del ladder:")
                    print(f"{'ID':<5} | {'Pos':<4} | {'Problem ID':<10} | {'State':<8} | {'Title'}")
                    print("-" * 80)
                    for problem in ladder:
                        print(f"{problem[0]:<5} | {problem[1]:<4} | {problem[2]:<10} | {problem[4]:<8} | {problem[3]}")
                else:
                    print("No se encontraron problemas en el ladder")
        
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
    if aplicar_parche():
        print("\n✨ ¡Parche aplicado con éxito! ✨")
        print("Ahora puedes reiniciar la aplicación con normalidad.")
        print("Al reiniciar el ladder desde la interfaz, solo se añadirá un problema.")
        sys.exit(0)
    else:
        print("\n❌ Error al aplicar el parche.")
        sys.exit(1) 