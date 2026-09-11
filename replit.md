# AulaData en Replit

## Ejecutar la aplicación

El workflow `Start application` inicia Flask en el puerto 5000:

```bash
python app.py
```

La aplicación usa la `DATABASE_URL` administrada por Replit cuando está disponible. También conserva compatibilidad con la configuración tradicional mediante `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD`.

## Variables y secretos

Secretos requeridos:

- `SECRET_KEY`
- `ADMIN_INITIAL_PASSWORD`
- `CONSULTA_INITIAL_PASSWORD`

## Base de datos

Después de conectar una base PostgreSQL o cambiar el esquema, aplicar:

```bash
flask --app app db upgrade
flask --app app crear-usuarios
```

## Preview

- Aplicación: workflow `Start application`
- Puerto: `5000`
- Healthcheck: `/health`