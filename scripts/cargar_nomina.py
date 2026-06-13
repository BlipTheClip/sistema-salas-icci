"""
Carga la nómina de estudiantes desde el Excel oficial al la base de datos.
Uso: python scripts/cargar_nomina.py <ruta_al_excel>
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import openpyxl
from app.database import engine, SessionLocal
from app.models import Base, Estudiante


def normalizar_rut(rut_raw: str) -> str:
    return str(rut_raw).strip().upper()


def normalizar_email(email_raw: str) -> str:
    return str(email_raw).strip().lower()


def cargar(ruta_excel: str):
    Base.metadata.create_all(bind=engine)
    wb = openpyxl.load_workbook(ruta_excel)
    ws = wb.active

    db = SessionLocal()
    nuevos = 0
    actualizados = 0
    errores = 0

    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            continue  # saltar encabezado

        try:
            _, rut_raw, nombre_raw, email_raw = row[:4]
            if not rut_raw or not nombre_raw or not email_raw:
                continue

            rut = normalizar_rut(rut_raw)
            nombre = str(nombre_raw).strip().upper()
            email = normalizar_email(email_raw)

            existente = db.query(Estudiante).filter(Estudiante.rut == rut).first()
            if existente:
                existente.nombre = nombre
                existente.email = email
                actualizados += 1
            else:
                db.add(Estudiante(rut=rut, nombre=nombre, email=email))
                nuevos += 1
        except Exception as e:
            print(f"  Error en fila {i+1}: {e}")
            errores += 1

    db.commit()
    db.close()

    print(f"\nNomina cargada exitosamente:")
    print(f"  Nuevos:      {nuevos}")
    print(f"  Actualizados: {actualizados}")
    print(f"  Errores:     {errores}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        ruta = os.path.join(os.path.dirname(__file__), "..", "nomina.xlsx")
        print(f"Usando ruta por defecto: {ruta}")
    else:
        ruta = sys.argv[1]

    if not os.path.exists(ruta):
        print(f"Error: no se encontro el archivo '{ruta}'")
        sys.exit(1)

    cargar(ruta)
