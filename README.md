# Sistema de Control de Acceso a Salas — ICCI UTA

Sistema web para el control de acceso y uso de las salas de estudio del Departamento de Computación e Informática de la Universidad de Tarapacá.

Actualmente desplegado en los servidores del departamento.

> **[Agrega una captura de pantalla aquí]** — es lo primero que mira cualquiera que entre al repositorio.
> Súbela a la carpeta `docs/` y enlázala así: `![Vista principal](docs/captura.png)`

## Qué resuelve

Las salas de estudio del departamento se ocupaban [describe en una frase cómo se gestionaban antes: en papel, por WhatsApp, sin registro]. Esto hacía difícil [saber quién ocupó una sala / respetar el aforo / etc.].

El sistema centraliza ese control en un solo lugar.

## Funcionalidades

- Registro de acceso de estudiantes a las salas de estudio.
- Registro de datos para personas externas al departamento ("foráneos").
- Límite de ocupación configurable por sala.
- [Completa: panel de administración, historial de uso, reportes, autenticación...]

## Stack

- **Backend:** Python — [indica el framework: Flask / FastAPI / Django]
- **Base de datos:** [PostgreSQL / MySQL / SQLite]
- **Despliegue:** Docker + Docker Compose, con Nginx como proxy inverso

## Puesta en marcha

Requisitos: Docker y Docker Compose.

```bash
git clone https://github.com/BlipTheClip/sistema-salas-icci.git
cd sistema-salas-icci

# Copia el archivo de ejemplo y completa tus valores
cp .env.example .env

docker compose up -d
```

La aplicación queda disponible en `http://localhost:[puerto]`.

Para más detalle sobre el arranque, revisa [`ARRANCAR.md`](ARRANCAR.md).

## Configuración

Todas las variables sensibles se definen en un archivo `.env`, que **no se versiona**. Usa `.env.example` como plantilla:

| Variable | Descripción |
|---|---|
| `[VARIABLE]` | [Para qué sirve] |
| `[VARIABLE]` | [Para qué sirve] |

## Estructura

```
app/              Código de la aplicación
scripts/          Scripts de utilidad y mantenimiento
Dockerfile        Imagen de la aplicación
docker-compose.yml
nginx.conf        Configuración del proxy inverso
.env.example      Plantilla de variables de entorno
ARRANCAR.md       Instrucciones de arranque
```

## Desarrollo

Este proyecto se desarrolló con [Claude Code](https://claude.com/claude-code) como herramienta de implementación. Las decisiones de diseño, los requisitos y la coordinación con el departamento son propias.

## Autor

Pablo Ignacio Varas Burgos — Ingeniería Civil en Computación e Informática, Universidad de Tarapacá.

## Licencia

[Elige una: MIT si quieres que sea reutilizable, o indica que es de uso interno del departamento.]
