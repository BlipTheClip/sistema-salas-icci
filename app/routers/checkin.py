from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Estudiante, Sala, RegistroAcceso, Sancion, PersonaForanea
from app.auth import oauth, email_dominio_valido, get_estudiante_session
from app.config import BASE_URL, HORA_APERTURA, HORA_CIERRE, DIAS_SEMANA_VALIDOS, MODO_PRUEBA

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

MAX_FORANEOS_POR_SALA = 10
MAX_FORANEOS_POR_ESTUDIANTE = 2


def sala_esta_abierta() -> bool:
    if MODO_PRUEBA:
        return True
    ahora = datetime.now()
    return (
        ahora.weekday() in DIAS_SEMANA_VALIDOS
        and HORA_APERTURA <= ahora.hour < HORA_CIERRE
    )


def get_sancion_activa(db: Session, rut: str) -> Optional[Sancion]:
    ahora = datetime.now()
    return db.query(Sancion).filter(
        Sancion.rut_estudiante == rut,
        Sancion.activa == True,
        (Sancion.fecha_fin.is_(None)) | (Sancion.fecha_fin >= ahora),
    ).first()


def contar_foraneos_en_sala(db: Session, sala_id: int) -> int:
    hoy = datetime.now().date()
    registros_abiertos = db.query(RegistroAcceso).filter(
        RegistroAcceso.sala_id == sala_id,
        RegistroAcceso.hora_salida.is_(None),
        RegistroAcceso.hora_entrada >= datetime.combine(hoy, datetime.min.time()),
    ).all()
    return sum(r.num_foraneos for r in registros_abiertos)


@router.get("/checkin/{slug}")
async def checkin_page(slug: str, request: Request, db: Session = Depends(get_db)):
    sala = db.query(Sala).filter(Sala.slug == slug).first()
    if not sala:
        return templates.TemplateResponse("checkin/error.html", {
            "request": request, "mensaje": "Sala no encontrada."
        })

    if not sala_esta_abierta():
        ahora = datetime.now()
        return templates.TemplateResponse("checkin/cerrada.html", {
            "request": request, "sala": sala, "ahora": ahora,
            "hora_apertura": HORA_APERTURA, "hora_cierre": HORA_CIERRE,
        })

    estudiante_session = get_estudiante_session(request)
    if not estudiante_session:
        request.session["sala_destino"] = slug
        return templates.TemplateResponse("checkin/login.html", {
            "request": request, "sala": sala
        })

    hoy = datetime.now().date()
    registro_existente = db.query(RegistroAcceso).filter(
        RegistroAcceso.rut_estudiante == estudiante_session["rut"],
        RegistroAcceso.sala_id == sala.id,
        RegistroAcceso.hora_salida.is_(None),
        RegistroAcceso.hora_entrada >= datetime.combine(hoy, datetime.min.time()),
    ).first()

    sancion = get_sancion_activa(db, estudiante_session["rut"])
    foraneos_en_sala = contar_foraneos_en_sala(db, sala.id)
    cupos_foraneos = max(0, MAX_FORANEOS_POR_SALA - foraneos_en_sala)

    return templates.TemplateResponse("checkin/index.html", {
        "request": request,
        "sala": sala,
        "estudiante": estudiante_session,
        "sancion": sancion,
        "ya_dentro": registro_existente is not None,
        "foraneos_en_sala": foraneos_en_sala,
        "cupos_foraneos": min(cupos_foraneos, MAX_FORANEOS_POR_ESTUDIANTE),
        "max_sala": MAX_FORANEOS_POR_SALA,
    })


@router.post("/checkin/{slug}")
async def hacer_checkin(
    request: Request,
    slug: str,
    db: Session = Depends(get_db),
):
    sala = db.query(Sala).filter(Sala.slug == slug).first()
    if not sala or not sala_esta_abierta():
        return RedirectResponse(f"/checkin/{slug}", status_code=302)

    estudiante_session = get_estudiante_session(request)
    if not estudiante_session:
        return RedirectResponse(f"/checkin/{slug}", status_code=302)

    if get_sancion_activa(db, estudiante_session["rut"]):
        return RedirectResponse(f"/checkin/{slug}", status_code=302)

    form = await request.form()

    # Recopilar datos de foráneos del formulario
    foraneos_data: List[dict] = []
    i = 1
    while f"foraneo_nombre_{i}" in form:
        nombre = form.get(f"foraneo_nombre_{i}", "").strip()
        rut_o_id = form.get(f"foraneo_id_{i}", "").strip()
        if nombre and rut_o_id:
            foraneos_data.append({"nombre": nombre, "rut_o_id": rut_o_id})
        i += 1

    num_foraneos = len(foraneos_data)

    # Validar límite por estudiante
    if num_foraneos > MAX_FORANEOS_POR_ESTUDIANTE:
        num_foraneos = MAX_FORANEOS_POR_ESTUDIANTE
        foraneos_data = foraneos_data[:MAX_FORANEOS_POR_ESTUDIANTE]

    # Validar límite total de la sala
    foraneos_actuales = contar_foraneos_en_sala(db, sala.id)
    cupos_disponibles = MAX_FORANEOS_POR_SALA - foraneos_actuales
    if num_foraneos > cupos_disponibles:
        foraneos_data = foraneos_data[:cupos_disponibles]
        num_foraneos = len(foraneos_data)

    registro = RegistroAcceso(
        rut_estudiante=estudiante_session["rut"],
        sala_id=sala.id,
        hora_entrada=datetime.now(),
        num_foraneos=num_foraneos,
    )
    db.add(registro)
    db.flush()

    for f_data in foraneos_data:
        db.add(PersonaForanea(
            registro_id=registro.id,
            nombre=f_data["nombre"],
            rut_o_id=f_data["rut_o_id"],
        ))

    db.commit()
    db.refresh(registro)

    return templates.TemplateResponse("checkin/exito.html", {
        "request": request,
        "sala": sala,
        "estudiante": estudiante_session,
        "registro": registro,
        "foraneos": registro.foraneos,
    })


@router.post("/checkout/{registro_id}")
async def hacer_checkout(registro_id: int, request: Request, db: Session = Depends(get_db)):
    estudiante_session = get_estudiante_session(request)
    if not estudiante_session:
        return RedirectResponse("/", status_code=302)

    registro = db.query(RegistroAcceso).filter(
        RegistroAcceso.id == registro_id,
        RegistroAcceso.rut_estudiante == estudiante_session["rut"],
        RegistroAcceso.hora_salida.is_(None),
    ).first()

    if registro:
        registro.hora_salida = datetime.now()
        db.commit()

    slug = registro.sala.slug if registro else "estudio"
    return RedirectResponse(f"/checkin/{slug}", status_code=302)


# ── Google OAuth ──────────────────────────────────────────────────────────────

@router.get("/auth/google/login")
async def google_login(request: Request):
    redirect_uri = f"{BASE_URL}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        return templates.TemplateResponse("checkin/error.html", {
            "request": request,
            "mensaje": "Error al autenticar con Google. Intenta de nuevo."
        })

    user_info = token.get("userinfo")
    if not user_info:
        return templates.TemplateResponse("checkin/error.html", {
            "request": request,
            "mensaje": "No se pudo obtener información de tu cuenta Google."
        })

    email = user_info.get("email", "").lower()

    if not email_dominio_valido(email):
        return templates.TemplateResponse("checkin/error.html", {
            "request": request,
            "mensaje": f"Solo pueden acceder estudiantes con correo @alumnos.uta.cl o @estudiantes.uta.cl. Tu correo ({email}) no está autorizado."
        })

    estudiante = db.query(Estudiante).filter(Estudiante.email == email).first()
    if not estudiante:
        return templates.TemplateResponse("checkin/error.html", {
            "request": request,
            "mensaje": f"Tu correo ({email}) no figura en la nómina oficial de la carrera. Si crees que es un error, contacta al CEC."
        })

    request.session["estudiante"] = {
        "rut": estudiante.rut,
        "nombre": estudiante.nombre,
        "email": estudiante.email,
    }

    destino_directo = request.session.pop("destino_post_login", None)
    if destino_directo:
        return RedirectResponse(destino_directo, status_code=302)

    destino = request.session.pop("sala_destino", "estudio")
    return RedirectResponse(f"/checkin/{destino}", status_code=302)


@router.get("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)
