> **Escribir para quien revisa.** La descripción debe leerse en un minuto: qué cambia, por
> qué, y qué mirar con atención. Sin tablas, sin secciones decorativas, sin repetir lo que
> el diff ya muestra. Si no entra en pocas líneas, el PR es demasiado grande: dividirlo.
> El detalle técnico va en el issue o en el mensaje del commit.
>
> **Un diagrama cuando explique mejor que el texto.** Para flujos, orden de ejecución o
> relaciones entre componentes, un diagrama reemplaza párrafos: incluirlo en lugar de
> describirlos en prosa, no además de.

## 📝 Descripción
<!-- Resumen de los cambios realizados siguiendo el formato del commit template (templates/commit-template.en.git.txt) -->
<!-- Ejemplo: :sparkles: feat(inventory): add a physical count to the item detail -->

**Contexto detallado:**
<!-- Qué cambia y por qué, en pocas líneas. Mencionar incidencias vinculadas (Closes #123) -->

---

## 🧪 Verificación Técnica
- [ ] **API**: `uv run ruff check .`, `uv run ruff format --check .` y `uv run pytest` pasan (con `docker compose up -d db`).
- [ ] **Web**: `npm run lint`, `npm run typecheck`, `npm test -- --run` y `npm run build` pasan.
- [ ] **Migraciones**: si cambió el esquema, la migración sube y baja (`alembic upgrade head`, `alembic downgrade -1`, `alembic upgrade head`) y `tests/test_migrations.py` pasa.
- [ ] **Dependencias**: ¿Se modificó `api/pyproject.toml` o `web/package.json`? (Si es sí, el lockfile actualizado va en el mismo PR.)
- [ ] **Aislamiento por taller**: si toca datos, ¿toda consulta y mutación sigue filtrada por taller (`get_current_workshop_id` en la API, claves de caché por taller en la web)?
- [ ] **Sin conexión**: si toca inventario o sesión, ¿se probó en un navegador real tocar sin conexión, recargar y reconectar sin perder ni duplicar movimientos?

---

## 📸 Anexos (Opcional)
<!-- Adjuntar capturas en vista de teléfono (390 px) o salidas de las pruebas si aplica -->
