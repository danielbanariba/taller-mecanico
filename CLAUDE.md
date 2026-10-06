# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Mechanic-shop management system ("Taller Mecánico"), originally a university project. Identifiers, routes, and UI text are in Spanish. It is two independent Python apps:

- `backend/`: FastAPI. Only exposes auth (login / create user).
- `frontend/`: Reflex 0.4.8 (`app_name="frontend"`, so the app package is `frontend/frontend/`).

There are no tests, linters, formatters, or CI.

## Setup and running

Dependencies are only listed in `pip_install.ps1` (`frontend/requirements.txt` pins just `reflex==0.4.8`). The `.ps1` scripts assume Windows and a venv named `env` at the repo root (`env\Scripts\activate.ps1`). On Linux:

```sh
python -m venv env && source env/bin/activate
pip install fastapi "uvicorn[standard]" reflex==0.4.8 pydantic "pydantic[email]" pandas sqlalchemy passlib bcrypt pyjwt requests cx_Oracle plotly reflex-dynoselect reflex-calendar
```

- Backend: `cd backend && uvicorn main:app --reload`. It must run from `backend/`: imports are cwd-relative, and the SQLite file `./users.db` is created there when `auth_controller` is imported.
- Frontend: `cd frontend && reflex run`. Login posts to a hardcoded `http://localhost:8000/login/`, so FastAPI must own port 8000; Reflex's own backend also defaults to 8000, so move it (`reflex run --backend-port 8001`).
- `front.ps1` does `Set-Location Frontend` (capital F), which breaks on case-sensitive filesystems.
- Seed scripts in `backend/db/` (`crear_tablas_SQLite.py`, `insertar_datos_SQLite.py`) use a bare `from client import ...`, so run them with cwd `backend/db/`. `insertar_datos_SQLite.py` calls `.db_url` on the tuple returned by `conectar_SQLite()` and fails as written.

## Architecture

The two halves do not share a database, and the frontend mostly bypasses the backend.

**Data paths, per feature:**

- Login: `frontend/frontend/login.py` (`Login` state) → HTTP → `backend/auth_controller.py` (SQLite `users.db`, bcrypt via passlib, JWT via PyJWT). `backend/auth/LoginState.py` is an unused duplicate of the Reflex login state.
- Inventario, proveedores, usuarios CRUD: Reflex talks **directly to Oracle** through SQLAlchemy, with no API in between. Layers: `pages/*.py` → root-level `*_page.py` (Reflex `State` classes such as `InventarioState`, `UserState`, `ProvedorState`) → `service/*_service.py` → `repository/*_repository.py` → `repository/connect_db.py` (hardcoded `oracle+cx_oracle://...@localhost:1521/xe`). Models are `rx.Model`/SQLModel classes in `model/`. The Oracle schema lives in `frontend/oracle/*.sql` (DDL, DML, sequences, triggers, user). Without a local Oracle XE these pages fail.
- Clientes, empleados, cotización: no service/repository layer; they are UI-only or use static data (CSV reads, hardcoded lists).

**Routing:** every route is registered in `frontend/frontend/frontend.py` via `app.add_page`. `pages/` composes routes; `view/` holds the UI components those pages use. The live `/proveedores` route renders the hardcoded list in `view/proveedores.py`; the Oracle-backed `proveedor_page.py` is only wired in a commented-out route. `frontend.py` also redefines `inventarios()` locally, shadowing the imported `pages.inventarios`.

**Shared UI:** `styles/` (color, font, and size constants), `components/` (buttons, notifications, forms), `figures/` (calendar, charts, decorative widgets).

**Dead code** (nothing imports it): `frontend/frontend/view/Ey-Apurence-xd/`, `frontend/frontend/view/inventario.py`, `frontend/frontend/utils/*.ts`, `backend/routers/`, `backend/schemas/`, `backend/config/db.py`. `backend/main.py` mounts only the `auth_controller` router.

**Other gotchas:**

- `backend/sql/BD_TALLER_MECANICO.sql` is a binary SQLite database, not a SQL script.
- `SECRET_KEY` is hardcoded in `backend/auth_controller.py`; `secret_key.env` is never loaded (there is no dotenv or `os.environ` usage anywhere).
- `frontend/frontend/URL.py` holds in-page anchor routes, not the backend base URL.
