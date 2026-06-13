from typing import Optional
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.responses import RedirectResponse
from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, BASE_URL, DOMINIOS_VALIDOS

oauth = OAuth()
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def get_estudiante_session(request: Request) -> Optional[dict]:
    return request.session.get("estudiante")


def get_auditor_session(request: Request) -> Optional[dict]:
    return request.session.get("auditor")


def require_estudiante(request: Request) -> Optional[dict]:
    user = get_estudiante_session(request)
    if not user:
        return None
    return user


def require_auditor(request: Request) -> Optional[dict]:
    auditor = get_auditor_session(request)
    if not auditor:
        return None
    return auditor


def require_superadmin(request: Request) -> Optional[dict]:
    auditor = get_auditor_session(request)
    if not auditor or auditor.get("rol") != "SUPER_ADMIN":
        return None
    return auditor


def email_dominio_valido(email: str) -> bool:
    try:
        dominio = email.split("@")[1].lower()
        return dominio in DOMINIOS_VALIDOS
    except IndexError:
        return False
