# Taller Mecánico — Inventario

Control de inventario de repuestos para talleres mecánicos de autos y motos en Honduras. Pensado para un taller pequeño, de bajo presupuesto, que hoy lleva el conteo en la cabeza o en papel y necesita saber, en el momento, cuántas unidades le quedan de cada repuesto (amortiguadores, aceite, filtros, etc.) sin depender de Excel ni de internet estable.

## ¿Qué resuelve?

- **Inicio de sesión con número de teléfono** (8 dígitos) y contraseña: sin correo, sin pasos de más.
- **Un toque para sumar o restar** una unidad de un repuesto desde la lista.
- **Conteo físico**: registrar la cantidad real contada y el sistema calcula el ajuste.
- **Alertas de stock bajo**: aviso cuando un repuesto llega a su mínimo configurado.
- **Historial por repuesto**: qué movimientos se hicieron, cuándo y el efecto en el stock.
- **Funciona sin señal**: la lista de repuestos queda disponible sin conexión y los cambios se guardan en el teléfono para enviarse solos cuando vuelva la señal.
- Instalable como app (PWA) en el teléfono del mecánico, con botones grandes pensados para usarse con las manos sucias en el taller.

## Stack

| Capa | Tecnología |
|---|---|
| API | Python, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL |
| Web | React + TypeScript, Vite, Tailwind CSS, TanStack Query, PWA (service worker + caché offline) |
| Pruebas | pytest (API), Vitest + Testing Library + MSW (web) |

Arquitectura: screaming, por feature, en ambos lados. El detalle para quien va a tocar código vive en [`CLAUDE.md`](./CLAUDE.md).

## Cómo correrlo en local

1. **Base de datos** (Postgres en Docker, puerto `5440`):
   ```sh
   docker compose up -d db
   ```
2. **API** (puerto `8010`): copiar `api/env.example` a `api/.env` y ajustar las variables `TALLER_*` (URL de base de datos, secreto del JWT, si la cookie requiere HTTPS). Luego:
   ```sh
   cd api
   uv run alembic upgrade head
   uv run uvicorn taller.main:app --reload --port 8010
   ```
3. **Web** (puerto `5173`, con proxy a la API en `/api`):
   ```sh
   cd web
   npm install
   npm run dev
   ```

Con los tres arriba, abrir `http://localhost:5173` registra un taller nuevo y entra directo al inventario.

## Checks

```sh
# API
cd api && uv run ruff check . && uv run ruff format --check . && uv run pytest

# Web
cd web && npm run lint && npm run typecheck && npm test -- --run && npm run build
```

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `api/` | API en FastAPI (identidad, inventario, migraciones de Alembic, pruebas) |
| `web/` | App web/PWA en React + Vite |
| `docker-compose.yml`, `docker/` | Postgres local y script de creación de la base de pruebas |
| `docs/research/` | Investigación de mercado que sustenta las decisiones de producto |
| `odd/` | Historial de planificación e implementación de cada feature |

## Hacia dónde va

El inventario es la base. Después de esto, en este orden:

1. **Clientes, vehículos (autos y motos), cotizaciones y órdenes de trabajo** que consuman repuestos del inventario.
2. **Facturación SAR/CAI** como módulo opcional (rango de CAI, RTN, desglose de ISV 15%, solo en lempiras) — el taller que no factura no paga ni ve ese módulo.
3. **Más usuarios por taller con roles**, recuperación de contraseña, envío de cotizaciones por WhatsApp, fotos por repuesto, y el cobro del producto en sí.

La prioridad y el porqué de este orden están en la investigación de mercado: [`docs/research/Necesidades de talleres en Honduras.md`](./docs/research/Necesidades%20de%20talleres%20en%20Honduras.md).
