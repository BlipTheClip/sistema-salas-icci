import os
import qrcode
from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from app.database import engine, SessionLocal
from app.models import Base, Sala, Auditor, RolAuditor
from app.auth import oauth
from app.scheduler import iniciar_scheduler
from app.routers import checkin, admin, denuncias, reportes
from app.config import SECRET_KEY, BASE_URL, SUPERADMIN_USERNAME, SUPERADMIN_PASSWORD, SUPERADMIN_NOMBRE

app = FastAPI(title="Sistema Salas ICCI - UTA")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=86400)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["enumerate"] = enumerate

app.include_router(checkin.router)
app.include_router(admin.router)
app.include_router(denuncias.router)
app.include_router(reportes.router)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _crear_salas(db):
    salas = [("Sala de Estudio", "estudio"), ("Sala de Descanso", "descanso")]
    for nombre, slug in salas:
        if not db.query(Sala).filter(Sala.slug == slug).first():
            db.add(Sala(nombre=nombre, slug=slug))
    db.commit()


def _crear_superadmin(db):
    if not db.query(Auditor).filter(Auditor.username == SUPERADMIN_USERNAME).first():
        db.add(Auditor(
            username=SUPERADMIN_USERNAME,
            nombre_completo=SUPERADMIN_NOMBRE,
            password_hash=pwd_context.hash(SUPERADMIN_PASSWORD),
            rol=RolAuditor.SUPER_ADMIN,
            activo=True,
        ))
        db.commit()


def _generar_qrs():
    qr_dir = Path("app/static/qr")
    qr_dir.mkdir(parents=True, exist_ok=True)
    for slug in ("estudio", "descanso"):
        ruta = qr_dir / f"qr_{slug}.png"
        if not ruta.exists():
            url = f"{BASE_URL}/checkin/{slug}"
            img = qrcode.make(url)
            img.save(str(ruta))


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _crear_salas(db)
        _crear_superadmin(db)
    finally:
        db.close()
    _generar_qrs()
    iniciar_scheduler()


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/qr/{slug}")
async def descargar_qr(slug: str):
    if slug not in ("estudio", "descanso"):
        return RedirectResponse("/", status_code=302)
    ruta = Path(f"app/static/qr/qr_{slug}.png")
    if not ruta.exists():
        return RedirectResponse("/", status_code=302)
    return FileResponse(str(ruta), media_type="image/png", filename=f"QR_Sala_{slug.title()}.png")
