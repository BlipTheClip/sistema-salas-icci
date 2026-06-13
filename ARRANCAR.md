# Cómo Arrancar el Sistema

## Desarrollo local (sin Docker)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables (editar .env con tus datos)
cp .env.example .env

# 3. Cargar la nómina de estudiantes
python scripts/cargar_nomina.py "ruta/al/nomina.xlsx"

# 4. Arrancar el servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Producción con Docker

```bash
# 1. Editar .env con valores reales
# 2. Construir y levantar
docker compose up -d --build

# 3. Cargar nómina (solo primera vez)
docker compose exec web python scripts/cargar_nomina.py /app/nomina.xlsx
```

## URLs del sistema

| URL | Descripción |
|-----|-------------|
| `/` | Página de inicio |
| `/checkin/estudio` | QR Sala de Estudio |
| `/checkin/descanso` | QR Sala de Descanso |
| `/denuncias/` | Formulario de denuncias (requiere login Google) |
| `/admin/` | Panel CEC |
| `/admin/en-vivo` | Vista en tiempo real |
| `/admin/historial` | Historial de registros |
| `/admin/sanciones` | Gestión de sanciones |
| `/admin/denuncias` | Bandeja de denuncias |
| `/admin/reportes/` | Reportes y estadísticas |
| `/admin/auditores` | Gestión de auditores (solo Super Admin) |
| `/qr/estudio` | Descargar QR Sala de Estudio |
| `/qr/descanso` | Descargar QR Sala de Descanso |

## Configurar Google OAuth

1. Ir a https://console.cloud.google.com/
2. Crear proyecto → APIs y Servicios → Credenciales
3. Crear "ID de cliente OAuth 2.0" → Aplicación web
4. Agregar URI de redireccionamiento: `http://TU_SERVIDOR/auth/google/callback`
5. Copiar Client ID y Client Secret al archivo `.env`
