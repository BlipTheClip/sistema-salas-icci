import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
SUPERADMIN_USERNAME = os.getenv("SUPERADMIN_USERNAME", "admin")
SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD", "admin123")
SUPERADMIN_NOMBRE = os.getenv("SUPERADMIN_NOMBRE", "Administrador CEC")

DOMINIOS_VALIDOS = {"alumnos.uta.cl", "estudiantes.uta.cl"}

HORA_APERTURA = 8   # 08:00
HORA_CIERRE = 20    # 20:00
DIAS_SEMANA_VALIDOS = {0, 1, 2, 3, 4}  # lunes=0 ... viernes=4
