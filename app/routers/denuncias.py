from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Denuncia, EstadoDenuncia, Estudiante, Sala
from app.auth import get_estudiante_session

router = APIRouter(prefix="/denuncias")
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def denuncias_page(request: Request, db: Session = Depends(get_db)):
    estudiante_session = get_estudiante_session(request)
    if not estudiante_session:
        request.session["sala_destino"] = "estudio"
        return RedirectResponse("/auth/google/login", status_code=302)

    salas = db.query(Sala).all()
    estudiantes = db.query(Estudiante).filter(
        Estudiante.rut != estudiante_session["rut"]
    ).order_by(Estudiante.nombre).all()

    mis_denuncias = db.query(Denuncia).filter(
        Denuncia.rut_denunciante == estudiante_session["rut"]
    ).order_by(Denuncia.fecha_creacion.desc()).all()

    return templates.TemplateResponse("denuncias/index.html", {
        "request": request,
        "estudiante": estudiante_session,
        "salas": salas,
        "estudiantes": estudiantes,
        "mis_denuncias": mis_denuncias,
        "EstadoDenuncia": EstadoDenuncia,
    })


@router.post("/enviar")
async def enviar_denuncia(
    request: Request,
    rut_denunciado: str = Form(...),
    sala_id: int = Form(None),
    descripcion: str = Form(...),
    fecha_incidente: str = Form(...),
    hora_incidente: str = Form(...),
    db: Session = Depends(get_db),
):
    estudiante_session = get_estudiante_session(request)
    if not estudiante_session:
        return RedirectResponse("/auth/google/login", status_code=302)

    if rut_denunciado == estudiante_session["rut"]:
        return RedirectResponse("/denuncias?error=auto_denuncia", status_code=302)

    denunciado = db.query(Estudiante).filter(Estudiante.rut == rut_denunciado).first()
    if not denunciado:
        return RedirectResponse("/denuncias?error=no_encontrado", status_code=302)

    try:
        fecha_hora = datetime.strptime(f"{fecha_incidente} {hora_incidente}", "%Y-%m-%d %H:%M")
    except ValueError:
        fecha_hora = datetime.now()

    denuncia = Denuncia(
        rut_denunciante=estudiante_session["rut"],
        rut_denunciado=rut_denunciado,
        sala_id=sala_id if sala_id else None,
        descripcion=descripcion.strip(),
        fecha_incidente=fecha_hora,
        fecha_creacion=datetime.now(),
        estado=EstadoDenuncia.PENDIENTE,
    )
    db.add(denuncia)
    db.commit()
    return RedirectResponse("/denuncias?enviada=1", status_code=302)
