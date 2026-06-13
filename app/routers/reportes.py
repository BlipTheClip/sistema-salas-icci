from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import RegistroAcceso, Sancion, Denuncia, Sala, Estudiante, EstadoDenuncia
from app.auth import require_auditor

router = APIRouter(prefix="/admin/reportes")
templates = Jinja2Templates(directory="app/templates")

PERIODOS = {"hoy": 1, "semana": 7, "mes": 30, "semestre": 180}


def _inicio_periodo(periodo: str) -> datetime:
    dias = PERIODOS.get(periodo, 7)
    return datetime.now() - timedelta(days=dias)


@router.get("/")
async def reportes(request: Request, periodo: str = "semana", db: Session = Depends(get_db)):
    auditor = require_auditor(request)
    if not auditor:
        return RedirectResponse("/admin/login", status_code=302)

    inicio = _inicio_periodo(periodo)
    salas = db.query(Sala).all()

    # ── Registros en el período ───────────────────────────────────────────────
    registros = db.query(RegistroAcceso).filter(
        RegistroAcceso.hora_entrada >= inicio
    ).all()

    # Ocupación por hora del día (0-23)
    por_hora = defaultdict(int)
    for r in registros:
        por_hora[r.hora_entrada.hour] += 1
    ocupacion_por_hora = [por_hora.get(h, 0) for h in range(8, 21)]
    etiquetas_hora = [f"{h:02d}:00" for h in range(8, 21)]

    # Uso por día de la semana
    dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    por_dia = defaultdict(int)
    for r in registros:
        dia = r.hora_entrada.weekday()
        if dia < 5:
            por_dia[dia] += 1
    uso_por_dia = [por_dia.get(d, 0) for d in range(5)]

    # Comparativa por sala
    uso_por_sala = {}
    for sala in salas:
        uso_por_sala[sala.nombre] = sum(1 for r in registros if r.sala_id == sala.id)

    # Total foráneos
    total_foraneos = sum(r.num_foraneos for r in registros)

    # Duración promedio de visita (solo registros con checkout)
    duraciones = [
        (r.hora_salida - r.hora_entrada).total_seconds() / 60
        for r in registros if r.hora_salida
    ]
    duracion_promedio = round(sum(duraciones) / len(duraciones)) if duraciones else 0

    # Top 10 usuarios más frecuentes
    conteo_usuarios = defaultdict(int)
    for r in registros:
        conteo_usuarios[r.rut_estudiante] += 1
    top_ruts = sorted(conteo_usuarios.items(), key=lambda x: x[1], reverse=True)[:10]
    top_usuarios = []
    for rut, visitas in top_ruts:
        est = db.query(Estudiante).filter(Estudiante.rut == rut).first()
        if est:
            top_usuarios.append({"nombre": est.nombre, "rut": rut, "visitas": visitas})

    # ── Sanciones ─────────────────────────────────────────────────────────────
    sanciones = db.query(Sancion).filter(Sancion.fecha_inicio >= inicio).all()
    total_sanciones = len(sanciones)
    sanciones_activas = sum(
        1 for s in sanciones
        if s.activa and (s.fecha_fin is None or s.fecha_fin >= datetime.now())
    )

    motivos_conteo = defaultdict(int)
    for s in sanciones:
        motivos_conteo[s.motivo] += 1
    motivos_labels = list(motivos_conteo.keys())
    motivos_data = [motivos_conteo[m] for m in motivos_labels]

    # ── Denuncias ─────────────────────────────────────────────────────────────
    denuncias = db.query(Denuncia).filter(Denuncia.fecha_creacion >= inicio).all()
    total_denuncias = len(denuncias)
    denuncias_pendientes = sum(1 for d in denuncias if d.estado == EstadoDenuncia.PENDIENTE)
    denuncias_resueltas = sum(1 for d in denuncias if d.estado == EstadoDenuncia.RESUELTA)

    return templates.TemplateResponse("reportes/index.html", {
        "request": request,
        "auditor": auditor,
        "periodo": periodo,
        "periodos": list(PERIODOS.keys()),
        # Registros
        "total_registros": len(registros),
        "total_foraneos": total_foraneos,
        "duracion_promedio": duracion_promedio,
        "etiquetas_hora": etiquetas_hora,
        "ocupacion_por_hora": ocupacion_por_hora,
        "dias_nombres": dias_nombres,
        "uso_por_dia": uso_por_dia,
        "uso_por_sala_labels": list(uso_por_sala.keys()),
        "uso_por_sala_data": list(uso_por_sala.values()),
        "top_usuarios": top_usuarios,
        # Sanciones
        "total_sanciones": total_sanciones,
        "sanciones_activas": sanciones_activas,
        "motivos_labels": motivos_labels,
        "motivos_data": motivos_data,
        # Denuncias
        "total_denuncias": total_denuncias,
        "denuncias_pendientes": denuncias_pendientes,
        "denuncias_resueltas": denuncias_resueltas,
    })
