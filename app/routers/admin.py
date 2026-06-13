from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database import get_db
from app.models import (
    Auditor, RolAuditor, Estudiante, Sala, RegistroAcceso,
    Sancion, TipoSancion, Denuncia, EstadoDenuncia
)
from app.auth import get_auditor_session, require_auditor, require_superadmin

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MOTIVOS_PREDEFINIDOS = [
    "Ruidos molestos",
    "Comida con olores fuertes",
    "Acaparamiento de espacio o mobiliario",
    "Ingreso no autorizado de personas externas",
    "Obstrucción de pasillos o salidas",
    "Mal uso del mobiliario",
    "Otro",
]


def _redirigir_login():
    return RedirectResponse("/admin/login", status_code=302)


# ── Login / Logout ────────────────────────────────────────────────────────────

@router.get("/login")
async def login_page(request: Request):
    if get_auditor_session(request):
        return RedirectResponse("/admin/", status_code=302)
    return templates.TemplateResponse("admin/login.html", {"request": request, "error": None})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    auditor = db.query(Auditor).filter(
        Auditor.username == username, Auditor.activo == True
    ).first()

    if not auditor or not pwd_context.verify(password, auditor.password_hash):
        return templates.TemplateResponse("admin/login.html", {
            "request": request, "error": "Usuario o contraseña incorrectos."
        })

    request.session["auditor"] = {
        "id": auditor.id,
        "username": auditor.username,
        "nombre": auditor.nombre_completo,
        "rol": auditor.rol.value,
    }
    return RedirectResponse("/admin/", status_code=302)


@router.get("/logout")
async def admin_logout(request: Request):
    request.session.pop("auditor", None)
    return RedirectResponse("/admin/login", status_code=302)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    auditor = require_auditor(request)
    if not auditor:
        return _redirigir_login()

    hoy = datetime.now().date()
    inicio_hoy = datetime.combine(hoy, datetime.min.time())

    total_hoy = db.query(RegistroAcceso).filter(
        RegistroAcceso.hora_entrada >= inicio_hoy
    ).count()

    dentro_ahora = db.query(RegistroAcceso).filter(
        RegistroAcceso.hora_entrada >= inicio_hoy,
        RegistroAcceso.hora_salida.is_(None),
    ).count()

    sanciones_activas = db.query(Sancion).filter(
        Sancion.activa == True,
        (Sancion.fecha_fin.is_(None)) | (Sancion.fecha_fin >= datetime.now()),
    ).count()

    denuncias_pendientes = db.query(Denuncia).filter(
        Denuncia.estado == EstadoDenuncia.PENDIENTE
    ).count()

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "auditor": auditor,
        "total_hoy": total_hoy,
        "dentro_ahora": dentro_ahora,
        "sanciones_activas": sanciones_activas,
        "denuncias_pendientes": denuncias_pendientes,
    })


# ── En Vivo ───────────────────────────────────────────────────────────────────

@router.get("/en-vivo")
async def en_vivo(request: Request, db: Session = Depends(get_db)):
    auditor = require_auditor(request)
    if not auditor:
        return _redirigir_login()

    hoy = datetime.now().date()
    inicio_hoy = datetime.combine(hoy, datetime.min.time())

    salas = db.query(Sala).all()
    datos_salas = []
    for sala in salas:
        registros = db.query(RegistroAcceso).filter(
            RegistroAcceso.sala_id == sala.id,
            RegistroAcceso.hora_entrada >= inicio_hoy,
            RegistroAcceso.hora_salida.is_(None),
        ).all()
        datos_salas.append({
            "sala": sala,
            "registros": registros,
            "total_estudiantes": len(registros),
            "total_foraneos": sum(r.num_foraneos for r in registros),
        })

    return templates.TemplateResponse("admin/en_vivo.html", {
        "request": request,
        "auditor": auditor,
        "datos_salas": datos_salas,
        "ahora": datetime.now(),
    })


# ── Historial ─────────────────────────────────────────────────────────────────

@router.get("/historial")
async def historial(
    request: Request,
    fecha: str = None,
    sala_id: int = None,
    db: Session = Depends(get_db),
):
    auditor = require_auditor(request)
    if not auditor:
        return _redirigir_login()

    if fecha:
        try:
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            fecha_dt = datetime.now().date()
    else:
        fecha_dt = datetime.now().date()

    inicio = datetime.combine(fecha_dt, datetime.min.time())
    fin = datetime.combine(fecha_dt, datetime.max.time())

    query = db.query(RegistroAcceso).filter(
        RegistroAcceso.hora_entrada >= inicio,
        RegistroAcceso.hora_entrada <= fin,
    )
    if sala_id:
        query = query.filter(RegistroAcceso.sala_id == sala_id)

    registros = query.order_by(RegistroAcceso.hora_entrada.desc()).all()
    salas = db.query(Sala).all()

    return templates.TemplateResponse("admin/historial.html", {
        "request": request,
        "auditor": auditor,
        "registros": registros,
        "fecha": fecha_dt.strftime("%Y-%m-%d"),
        "salas": salas,
        "sala_id_sel": sala_id,
    })


# ── Sanciones ─────────────────────────────────────────────────────────────────

@router.get("/sanciones")
async def sanciones_page(request: Request, db: Session = Depends(get_db)):
    auditor = require_auditor(request)
    if not auditor:
        return _redirigir_login()

    ahora = datetime.now()
    sanciones = db.query(Sancion).order_by(Sancion.fecha_inicio.desc()).all()

    return templates.TemplateResponse("admin/sanciones.html", {
        "request": request,
        "auditor": auditor,
        "sanciones": sanciones,
        "ahora": ahora,
        "motivos": MOTIVOS_PREDEFINIDOS,
        "estudiantes": db.query(Estudiante).order_by(Estudiante.nombre).all(),
    })


@router.post("/sanciones/aplicar")
async def aplicar_sancion(
    request: Request,
    rut_estudiante: str = Form(...),
    tipo: str = Form(...),
    dias: int = Form(None),
    motivo: str = Form(...),
    motivo_otro: str = Form(""),
    db: Session = Depends(get_db),
):
    auditor = require_auditor(request)
    if not auditor:
        return _redirigir_login()

    motivo_final = motivo_otro.strip() if motivo == "Otro" else motivo
    if not motivo_final:
        motivo_final = motivo

    tipo_enum = TipoSancion.PERMANENTE if tipo == "PERMANENTE" else TipoSancion.TEMPORAL
    fecha_fin = None
    if tipo_enum == TipoSancion.TEMPORAL and dias and dias > 0:
        fecha_fin = datetime.now() + timedelta(days=dias)

    sancion = Sancion(
        rut_estudiante=rut_estudiante,
        tipo=tipo_enum,
        fecha_inicio=datetime.now(),
        fecha_fin=fecha_fin,
        dias_sancion=dias if tipo_enum == TipoSancion.TEMPORAL else None,
        motivo=motivo_final,
        auditor_username=auditor["username"],
        activa=True,
    )
    db.add(sancion)
    db.commit()
    return RedirectResponse("/admin/sanciones", status_code=302)


@router.post("/sanciones/{sancion_id}/revocar")
async def revocar_sancion(sancion_id: int, request: Request, db: Session = Depends(get_db)):
    auditor = require_auditor(request)
    if not auditor:
        return _redirigir_login()

    sancion = db.query(Sancion).filter(Sancion.id == sancion_id).first()
    if sancion:
        sancion.activa = False
        db.commit()
    return RedirectResponse("/admin/sanciones", status_code=302)


# ── Denuncias ─────────────────────────────────────────────────────────────────

@router.get("/denuncias")
async def denuncias_page(request: Request, db: Session = Depends(get_db)):
    auditor = require_auditor(request)
    if not auditor:
        return _redirigir_login()

    denuncias = db.query(Denuncia).order_by(Denuncia.fecha_creacion.desc()).all()
    return templates.TemplateResponse("admin/denuncias.html", {
        "request": request,
        "auditor": auditor,
        "denuncias": denuncias,
        "motivos": MOTIVOS_PREDEFINIDOS,
        "EstadoDenuncia": EstadoDenuncia,
    })


@router.post("/denuncias/{denuncia_id}/estado")
async def cambiar_estado_denuncia(
    denuncia_id: int,
    request: Request,
    estado: str = Form(...),
    nota_auditor: str = Form(""),
    db: Session = Depends(get_db),
):
    auditor = require_auditor(request)
    if not auditor:
        return _redirigir_login()

    denuncia = db.query(Denuncia).filter(Denuncia.id == denuncia_id).first()
    if denuncia:
        denuncia.estado = EstadoDenuncia(estado)
        denuncia.nota_auditor = nota_auditor.strip() or None
        denuncia.auditor_username = auditor["username"]
        db.commit()
    return RedirectResponse("/admin/denuncias", status_code=302)


@router.post("/denuncias/{denuncia_id}/sancionar")
async def sancionar_desde_denuncia(
    denuncia_id: int,
    request: Request,
    tipo: str = Form(...),
    dias: int = Form(None),
    motivo: str = Form(...),
    db: Session = Depends(get_db),
):
    auditor = require_auditor(request)
    if not auditor:
        return _redirigir_login()

    denuncia = db.query(Denuncia).filter(Denuncia.id == denuncia_id).first()
    if not denuncia:
        return RedirectResponse("/admin/denuncias", status_code=302)

    tipo_enum = TipoSancion.PERMANENTE if tipo == "PERMANENTE" else TipoSancion.TEMPORAL
    fecha_fin = None
    if tipo_enum == TipoSancion.TEMPORAL and dias and dias > 0:
        fecha_fin = datetime.now() + timedelta(days=dias)

    sancion = Sancion(
        rut_estudiante=denuncia.rut_denunciado,
        tipo=tipo_enum,
        fecha_inicio=datetime.now(),
        fecha_fin=fecha_fin,
        dias_sancion=dias if tipo_enum == TipoSancion.TEMPORAL else None,
        motivo=motivo,
        auditor_username=auditor["username"],
        activa=True,
        denuncia_id=denuncia_id,
    )
    db.add(sancion)
    denuncia.estado = EstadoDenuncia.RESUELTA
    denuncia.auditor_username = auditor["username"]
    db.commit()
    return RedirectResponse("/admin/denuncias", status_code=302)


# ── Auditores (solo SUPER_ADMIN) ──────────────────────────────────────────────

@router.get("/auditores")
async def auditores_page(request: Request, db: Session = Depends(get_db)):
    auditor = require_superadmin(request)
    if not auditor:
        return RedirectResponse("/admin/", status_code=302)

    auditores = db.query(Auditor).order_by(Auditor.fecha_creacion.desc()).all()
    return templates.TemplateResponse("admin/auditores.html", {
        "request": request,
        "auditor": auditor,
        "auditores": auditores,
    })


@router.post("/auditores/crear")
async def crear_auditor(
    request: Request,
    username: str = Form(...),
    nombre_completo: str = Form(...),
    password: str = Form(...),
    rol: str = Form("AUDITOR"),
    db: Session = Depends(get_db),
):
    auditor_ses = require_superadmin(request)
    if not auditor_ses:
        return RedirectResponse("/admin/", status_code=302)

    existente = db.query(Auditor).filter(Auditor.username == username).first()
    if existente:
        return RedirectResponse("/admin/auditores?error=usuario_existe", status_code=302)

    nuevo = Auditor(
        username=username,
        nombre_completo=nombre_completo,
        password_hash=pwd_context.hash(password),
        rol=RolAuditor(rol),
        activo=True,
    )
    db.add(nuevo)
    db.commit()
    return RedirectResponse("/admin/auditores", status_code=302)


@router.post("/auditores/{auditor_id}/toggle")
async def toggle_auditor(auditor_id: int, request: Request, db: Session = Depends(get_db)):
    auditor_ses = require_superadmin(request)
    if not auditor_ses:
        return RedirectResponse("/admin/", status_code=302)

    auditor_obj = db.query(Auditor).filter(Auditor.id == auditor_id).first()
    es_su_propia_cuenta = auditor_obj and auditor_obj.username == auditor_ses["username"]
    es_superadmin = auditor_obj and auditor_obj.rol == RolAuditor.SUPER_ADMIN
    if auditor_obj and not es_su_propia_cuenta and not es_superadmin:
        auditor_obj.activo = not auditor_obj.activo
        db.commit()
    return RedirectResponse("/admin/auditores", status_code=302)
