# Portal GECOVA Unificado

## Instalación

```bash
pip install -r requirements.txt
python app.py
```

Acceder en: http://localhost:5000

## Despliegue en la nube (Railway / Render / etc.)

1. Subir todos los archivos a un repositorio Git
2. Conectar el repo en Railway o Render
3. Start command: `gunicorn app:app`
4. La base de datos SQLite se crea automáticamente al iniciar

## Módulos

- **Reportes de Generación** – Carga Excel + PDF CFE → genera informe PDF
- **Órdenes de Mantenimiento** – Checklist preventivo → genera PDF numerado
- **Cotizaciones** *(próximamente)*
- **Órdenes de Trabajo** *(próximamente)*

## Usuarios por defecto

El primer acceso crea el admin. Agregar usuarios desde Admin → Usuarios.
