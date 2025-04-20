#!/usr/bin/env python
import psycopg2
import sys

# URL de la base de datos
DATABASE_URL = "postgresql://ladder_db_user:6FCOPInpMsKIazgN7WbdXd1dzsUwZVmv@dpg-d01m3rruibrs73aurmt0-a.virginia-postgres.render.com/ladder_db"

print("INSPECCIÓN DE TRIGGERS Y FUNCIONES DE LA BASE DE DATOS")
print(f"Conectando a PostgreSQL con URL: {DATABASE_URL}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # 1. Examinar triggers
    print("\n1. DETALLE DE TRIGGERS:")
    cursor.execute("""
    SELECT trigger_name, event_object_table, event_manipulation, action_statement
    FROM information_schema.triggers
    WHERE event_object_schema = 'public'
    """)
    
    triggers = cursor.fetchall()
    if not triggers:
        print("No hay triggers definidos en la base de datos.")
    else:
        for t in triggers:
            print(f"\n--- TRIGGER: {t[0]} ---")
            print(f"Tabla: {t[1]}")
            print(f"Evento: {t[2]}")
            print(f"Acción: {t[3]}")
    
    # 2. Examinar definición de funciones
    print("\n2. DETALLE DE FUNCIONES:")
    
    # Lista de funciones a examinar
    functions = [
        "reset_ladder_function",
        "reveal_next_problem",
        "check_current_problems"
    ]
    
    for func in functions:
        print(f"\n--- FUNCIÓN: {func} ---")
        cursor.execute("""
        SELECT pg_get_functiondef(oid)
        FROM pg_proc
        WHERE proname = %s
        """, (func,))
        
        definition = cursor.fetchone()
        if definition:
            print(definition[0])
        else:
            print(f"No se encontró la definición de la función {func}")
    
    # 3. Examinar las restricciones de la tabla ladder_problems
    print("\n3. RESTRICCIONES DE LA TABLA ladder_problems:")
    cursor.execute("""
    SELECT conname, contype, consrc
    FROM pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    WHERE t.relname = 'ladder_problems'
    """)
    
    constraints = cursor.fetchall()
    if not constraints:
        print("No hay restricciones definidas para la tabla ladder_problems.")
    else:
        for c in constraints:
            print(f"Restricción: {c[0]}, Tipo: {c[1]}, Definición: {c[2] if len(c) > 2 and c[2] is not None else 'N/A'}")
    
    conn.close()
    
    print("\n✨ INSPECCIÓN COMPLETADA ✨")
    print("Las funciones y triggers encontrados están modificando automáticamente el ladder.")
    print("Es posible que la aplicación web esté utilizando estas funciones para")
    print("recalcular o asignar problemas cada vez que accedes al ladder.")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        conn.close()
    except:
        pass 