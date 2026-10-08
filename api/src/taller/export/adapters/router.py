"""FastAPI router for the workshop-scoped data export (`design.md`'s AD-13).

`GET /export` is read-only: it never commits, and ignores any query
parameter -- in particular, it never accepts a client-supplied workshop id
for scoping. The response is built fully in memory (no `StreamingResponse`,
so the request's DB session stays open for the whole build; see AD-13's
rejected alternatives).
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from taller.export.adapters import sources
from taller.export.application.csv_zip import build_csv, build_zip
from taller.identity.adapters.dependencies import get_current_workshop_id
from taller.shared.db import get_db

export_router = APIRouter(tags=["export"])


@export_router.get("/export")
def export_data_route(
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> Response:
    archive = build_zip(
        {
            "customers.csv": build_csv(
                sources.CUSTOMERS_HEADERS, sources.customers_rows(db, workshop_id)
            ),
            "vehicles.csv": build_csv(
                sources.VEHICLES_HEADERS, sources.vehicles_rows(db, workshop_id)
            ),
            "items.csv": build_csv(sources.ITEMS_HEADERS, sources.items_rows(db, workshop_id)),
            "inventory_movements.csv": build_csv(
                sources.INVENTORY_MOVEMENTS_HEADERS,
                sources.inventory_movements_rows(db, workshop_id),
            ),
            "work_orders.csv": build_csv(
                sources.WORK_ORDERS_HEADERS, sources.work_orders_rows(db, workshop_id)
            ),
            "work_order_lines.csv": build_csv(
                sources.WORK_ORDER_LINES_HEADERS, sources.work_order_lines_rows(db, workshop_id)
            ),
            "payments.csv": build_csv(
                sources.PAYMENTS_HEADERS, sources.payments_rows(db, workshop_id)
            ),
            "fiscal_invoices.csv": build_csv(
                sources.FISCAL_INVOICES_HEADERS, sources.fiscal_invoices_rows(db, workshop_id)
            ),
            "fiscal_invoice_lines.csv": build_csv(
                sources.FISCAL_INVOICE_LINES_HEADERS,
                sources.fiscal_invoice_lines_rows(db, workshop_id),
            ),
            "fiscal_credit_notes.csv": build_csv(
                sources.FISCAL_CREDIT_NOTES_HEADERS,
                sources.fiscal_credit_notes_rows(db, workshop_id),
            ),
        }
    )
    filename = f"taller-export-{date.today().isoformat()}.zip"
    return Response(
        content=archive,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
