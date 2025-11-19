# Desactivar AirPlay Receiver (puerto 5000)

El puerto 5000 en macOS es usado por **AirPlay Receiver** del sistema.

## Solución Permanente:

1. Abre **Ajustes del Sistema** (System Settings)
2. Ve a **General**
3. Busca **AirDrop y Handoff**
4. **DESACTIVA** "AirPlay Receiver"

## Alternativa - Cambiar el puerto de la aplicación:

Si prefieres no desactivar AirPlay, puedes usar otro puerto como 8080:

```bash
python app.py  # Modificar app.py para usar otro puerto
```

## Verificar qué está usando el puerto 5000:

```bash
lsof -i :5000
```

## Matar el proceso manualmente:

```bash
# Ver el PID
lsof -i :5000

# Matar el proceso (reemplaza PID con el número que veas)
kill -9 PID
```

