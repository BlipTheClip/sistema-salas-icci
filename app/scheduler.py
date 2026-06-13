from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import RegistroAcceso


def auto_checkout():
    db: Session = SessionLocal()
    try:
        abiertos = db.query(RegistroAcceso).filter(
            RegistroAcceso.hora_salida.is_(None)
        ).all()
        ahora = datetime.now()
        for registro in abiertos:
            registro.hora_salida = ahora
            registro.auto_checkout = True
        db.commit()
        print(f"[Scheduler] Auto-checkout: {len(abiertos)} registros cerrados a las {ahora.strftime('%H:%M')}")
    finally:
        db.close()


def iniciar_scheduler():
    scheduler = BackgroundScheduler(timezone="America/Santiago")
    # Auto-checkout de lunes a viernes a las 20:00
    scheduler.add_job(
        auto_checkout,
        CronTrigger(day_of_week="mon-fri", hour=20, minute=0),
        id="auto_checkout",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
