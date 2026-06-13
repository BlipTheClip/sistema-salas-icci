import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean,
    ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.database import Base


class Sala(Base):
    __tablename__ = "salas"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    registros = relationship("RegistroAcceso", back_populates="sala")
    denuncias = relationship("Denuncia", back_populates="sala")


class Estudiante(Base):
    __tablename__ = "estudiantes"
    rut = Column(String(12), primary_key=True)
    nombre = Column(String(200), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    registros = relationship("RegistroAcceso", back_populates="estudiante")
    sanciones = relationship("Sancion", back_populates="estudiante")
    denuncias_realizadas = relationship(
        "Denuncia", foreign_keys="Denuncia.rut_denunciante", back_populates="denunciante"
    )
    denuncias_recibidas = relationship(
        "Denuncia", foreign_keys="Denuncia.rut_denunciado", back_populates="denunciado"
    )


class RegistroAcceso(Base):
    __tablename__ = "registros_acceso"
    id = Column(Integer, primary_key=True)
    rut_estudiante = Column(String(12), ForeignKey("estudiantes.rut"), nullable=False)
    sala_id = Column(Integer, ForeignKey("salas.id"), nullable=False)
    hora_entrada = Column(DateTime, default=datetime.now, nullable=False)
    hora_salida = Column(DateTime, nullable=True)
    num_foraneos = Column(Integer, default=0)
    auto_checkout = Column(Boolean, default=False)
    estudiante = relationship("Estudiante", back_populates="registros")
    sala = relationship("Sala", back_populates="registros")


class TipoSancion(str, enum.Enum):
    TEMPORAL = "TEMPORAL"
    PERMANENTE = "PERMANENTE"


class Sancion(Base):
    __tablename__ = "sanciones"
    id = Column(Integer, primary_key=True)
    rut_estudiante = Column(String(12), ForeignKey("estudiantes.rut"), nullable=False)
    tipo = Column(SAEnum(TipoSancion), nullable=False)
    fecha_inicio = Column(DateTime, default=datetime.now, nullable=False)
    fecha_fin = Column(DateTime, nullable=True)
    dias_sancion = Column(Integer, nullable=True)
    motivo = Column(Text, nullable=False)
    auditor_username = Column(String(100), nullable=False)
    activa = Column(Boolean, default=True)
    denuncia_id = Column(Integer, ForeignKey("denuncias.id"), nullable=True)
    estudiante = relationship("Estudiante", back_populates="sanciones")


class EstadoDenuncia(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    EN_REVISION = "EN_REVISION"
    RESUELTA = "RESUELTA"
    ARCHIVADA = "ARCHIVADA"


class Denuncia(Base):
    __tablename__ = "denuncias"
    id = Column(Integer, primary_key=True)
    rut_denunciante = Column(String(12), ForeignKey("estudiantes.rut"), nullable=False)
    rut_denunciado = Column(String(12), ForeignKey("estudiantes.rut"), nullable=False)
    sala_id = Column(Integer, ForeignKey("salas.id"), nullable=True)
    descripcion = Column(Text, nullable=False)
    fecha_incidente = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.now)
    estado = Column(SAEnum(EstadoDenuncia), default=EstadoDenuncia.PENDIENTE)
    nota_auditor = Column(Text, nullable=True)
    auditor_username = Column(String(100), nullable=True)
    denunciante = relationship(
        "Estudiante", foreign_keys=[rut_denunciante], back_populates="denuncias_realizadas"
    )
    denunciado = relationship(
        "Estudiante", foreign_keys=[rut_denunciado], back_populates="denuncias_recibidas"
    )
    sala = relationship("Sala", back_populates="denuncias")
    sancion = relationship("Sancion", foreign_keys="Sancion.denuncia_id", primaryjoin="Denuncia.id == Sancion.denuncia_id", uselist=False)


class RolAuditor(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    AUDITOR = "AUDITOR"


class Auditor(Base):
    __tablename__ = "auditores"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    nombre_completo = Column(String(200), nullable=False)
    password_hash = Column(String(200), nullable=False)
    rol = Column(SAEnum(RolAuditor), default=RolAuditor.AUDITOR)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.now)
