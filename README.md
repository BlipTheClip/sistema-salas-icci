# Sistema de Control de Acceso a Salas — ICCI UTA

Sistema web para el control de acceso y uso de las salas de estudio del
Departamento de Computación e Informática de la Universidad de Tarapacá.

Actualmente desplegado en los servidores del departamento.

## Funcionalidades

- Control de acceso a las salas de estudio del departamento.
- Registro de datos para personas externas al departamento.
- Límite de ocupación por sala.

## Stack

Aplicación en Python, desplegada con Docker Compose y Nginx como proxy inverso.

## Puesta en marcha

Requisitos: Docker y Docker Compose.

```bash
git clone https://github.com/BlipTheClip/sistema-salas-icci.git
cd sistema-salas-icci
cp .env.example .env    # completar con los valores del entorno
docker compose up -d
```

Las instrucciones detalladas de arranque están en [`ARRANCAR.md`](ARRANCAR.md).

Las variables sensibles se definen en `.env`, que no se versiona.
Usar `.env.example` como plantilla.

## Desarrollo

Desarrollado con [Claude Code](https://claude.com/claude-code) como herramienta
de implementación. Las decisiones de diseño y los requisitos son propios.

## Autor

Pablo Ignacio Varas Burgos — Ingeniería Civil en Computación e Informática,
Universidad de Tarapacá.
