"""FastAPI routes for the work-orders feature.

Composition root for this feature: it builds every repository (work
orders, its own counter, plus customers' and inventory's, for the
cross-feature reads AD-12 calls for) and wires them into the use cases.
"""

import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from taller.customers.adapters.repositories import (
    SqlAlchemyCustomerRepository,
    SqlAlchemyVehicleRepository,
)
from taller.customers.application.ports import CustomerRepository, VehicleRepository
from taller.customers.application.use_cases import describe_vehicles
from taller.customers.domain.entities import Customer, Vehicle
from taller.customers.domain.errors import VehicleNotFound
from taller.identity.adapters.dependencies import (
    get_clock,
    get_current_user,
    get_current_workshop_id,
)
from taller.identity.application.ports import Clock
from taller.identity.domain.entities import User
from taller.inventory.adapters.repositories import (
    SqlAlchemyItemRepository,
    SqlAlchemyMovementRepository,
)
from taller.inventory.domain.errors import MovementIdConflict, StockOutOfRange
from taller.shared.db import get_db
from taller.workorders.adapters.repositories import (
    SqlAlchemyPaymentRepository,
    SqlAlchemyWorkOrderRepository,
    SqlAlchemyWorkshopCounterRepository,
)
from taller.workorders.adapters.schemas import (
    CashSummaryOut,
    PaymentCreateRequest,
    VoidPaymentRequest,
    WorkOrderCreateRequest,
    WorkOrderLineCreateRequest,
    WorkOrderLineUpdateRequest,
    WorkOrderOut,
    WorkOrderStatusUpdateRequest,
    WorkOrderSummaryOut,
    WorkOrderUpdateRequest,
)
from taller.workorders.application.ports import PaymentRepository
from taller.workorders.application.use_cases import (
    add_line,
    change_status,
    create_work_order,
    daily_cash_summary,
    get_work_order,
    list_work_orders,
    record_payment,
    remove_line,
    update_line,
    update_work_order,
    void_payment,
)
from taller.workorders.domain.entities import LineKind, PaymentMethod, WorkOrder
from taller.workorders.domain.errors import (
    InvalidStatusTransition,
    ItemNotFoundForLine,
    PaymentExceedsBalance,
    PaymentIdConflict,
    PaymentNotFound,
    WorkOrderHasPayments,
    WorkOrderIdConflict,
    WorkOrderLineIdConflict,
    WorkOrderLineNotFound,
    WorkOrderLocked,
    WorkOrderNotFound,
    WorkOrderNotPayable,
)

work_orders_router = APIRouter(tags=["work-orders"])

#: Default PostgreSQL primary key constraint name (no explicit name was
#: given in the migration). Order ids are global primary keys, not scoped
#: to a workshop, so a client-supplied id colliding with another
#: workshop's row surfaces here as a violation of this constraint, never
#: as the workshop-scoped pre-check (which cannot see the other
#: workshop's row at all). Mirrors `taller.customers.adapters.router`'s
#: `_CUSTOMER_PK_CONSTRAINT`.
_ORDER_PK_CONSTRAINT = "work_orders_pkey"


def _violated_constraint(exc: IntegrityError) -> str | None:
    """Mirrors `taller.customers.adapters.router._violated_constraint`."""
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)


def _embed(
    order: WorkOrder,
    *,
    workshop_id: uuid.UUID,
    vehicle_repo: VehicleRepository,
    customer_repo: CustomerRepository,
) -> tuple[Vehicle, Customer]:
    """Resolve an order's vehicle and owner through `describe_vehicles`
    (`design.md`'s AD-12), for both a single-order response and a list.
    """
    embeds = describe_vehicles(
        workshop_id=workshop_id,
        vehicle_ids=[order.vehicle_id],
        vehicle_repo=vehicle_repo,
        customer_repo=customer_repo,
    )
    return embeds[order.vehicle_id]


def _to_out(
    order: WorkOrder,
    *,
    workshop_id: uuid.UUID,
    vehicle_repo: VehicleRepository,
    customer_repo: CustomerRepository,
    payment_repo: PaymentRepository,
) -> WorkOrderOut:
    vehicle, customer = _embed(
        order, workshop_id=workshop_id, vehicle_repo=vehicle_repo, customer_repo=customer_repo
    )
    payments = payment_repo.list_for_order(workshop_id=workshop_id, order_id=order.id)
    return WorkOrderOut.from_domain(order, vehicle=vehicle, customer=customer, payments=payments)


@work_orders_router.get("/work-orders", response_model=list[WorkOrderSummaryOut])
def list_work_orders_route(
    status_group: Literal["open", "closed", "all"] = Query(default="open"),
    vehicle_id: uuid.UUID | None = Query(default=None),
    customer_id: uuid.UUID | None = Query(default=None),
    before_number: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> list[WorkOrderSummaryOut]:
    order_repo = SqlAlchemyWorkOrderRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    customer_repo = SqlAlchemyCustomerRepository(db)

    orders = list_work_orders(
        workshop_id=workshop_id,
        status_group=status_group,
        vehicle_id=vehicle_id,
        customer_id=customer_id,
        before_number=before_number,
        limit=limit,
        order_repo=order_repo,
    )
    totals = order_repo.totals(workshop_id=workshop_id, order_ids=[order.id for order in orders])
    embeds = describe_vehicles(
        workshop_id=workshop_id,
        vehicle_ids=[order.vehicle_id for order in orders],
        vehicle_repo=vehicle_repo,
        customer_repo=customer_repo,
    )
    return [
        WorkOrderSummaryOut.from_domain(
            order,
            vehicle=embeds[order.vehicle_id][0],
            customer=embeds[order.vehicle_id][1],
            total_cents=totals.get(order.id, 0),
        )
        for order in orders
    ]


@work_orders_router.post(
    "/work-orders", response_model=WorkOrderOut, status_code=status.HTTP_201_CREATED
)
def create_work_order_route(
    payload: WorkOrderCreateRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> WorkOrderOut:
    order_repo = SqlAlchemyWorkOrderRepository(db)
    counter_repo = SqlAlchemyWorkshopCounterRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    customer_repo = SqlAlchemyCustomerRepository(db)
    payment_repo = SqlAlchemyPaymentRepository(db)

    def _attempt() -> tuple[WorkOrder, bool]:
        result = create_work_order(
            workshop_id=workshop_id,
            order_id=payload.id,
            vehicle_id=payload.vehicle_id,
            complaint=payload.complaint,
            odometer_km=payload.odometer_km,
            notes=payload.notes,
            created_by=current_user.id,
            order_repo=order_repo,
            counter_repo=counter_repo,
            vehicle_repo=vehicle_repo,
        )
        db.commit()
        return result

    try:
        order, is_new = _attempt()
    except WorkOrderIdConflict as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="work_order_id_conflict") from exc
    except VehicleNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="vehicle_not_found") from exc
    except IntegrityError as first_exc:
        db.rollback()
        # Another request committed the same order id between our
        # pre-check and our insert; retry once so the pre-check resolves
        # it as a replay or a precise conflict. The rollback above also
        # undoes this attempt's counter bump, so the retry never skips a
        # number (design.md's AD-6).
        try:
            order, is_new = _attempt()
        except WorkOrderIdConflict as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, detail="work_order_id_conflict") from exc
        except VehicleNotFound as exc:
            db.rollback()
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="vehicle_not_found") from exc
        except IntegrityError as exc:
            db.rollback()
            if _violated_constraint(exc) == _ORDER_PK_CONSTRAINT:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, detail="work_order_id_conflict"
                ) from exc
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail="work_order_create_failed"
            ) from (exc or first_exc)

    if not is_new:
        response.status_code = status.HTTP_200_OK
    return _to_out(
        order,
        workshop_id=workshop_id,
        vehicle_repo=vehicle_repo,
        customer_repo=customer_repo,
        payment_repo=payment_repo,
    )


@work_orders_router.get("/work-orders/{order_id}", response_model=WorkOrderOut)
def get_work_order_route(
    order_id: uuid.UUID,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> WorkOrderOut:
    order_repo = SqlAlchemyWorkOrderRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    customer_repo = SqlAlchemyCustomerRepository(db)
    payment_repo = SqlAlchemyPaymentRepository(db)
    try:
        order = get_work_order(workshop_id=workshop_id, order_id=order_id, order_repo=order_repo)
    except WorkOrderNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="work_order_not_found") from exc
    return _to_out(
        order,
        workshop_id=workshop_id,
        vehicle_repo=vehicle_repo,
        customer_repo=customer_repo,
        payment_repo=payment_repo,
    )


@work_orders_router.patch("/work-orders/{order_id}", response_model=WorkOrderOut)
def update_work_order_route(
    order_id: uuid.UUID,
    payload: WorkOrderUpdateRequest,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> WorkOrderOut:
    order_repo = SqlAlchemyWorkOrderRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    customer_repo = SqlAlchemyCustomerRepository(db)
    payment_repo = SqlAlchemyPaymentRepository(db)
    fields = payload.model_dump(exclude_unset=True)
    try:
        order = update_work_order(
            workshop_id=workshop_id, order_id=order_id, fields=fields, order_repo=order_repo
        )
        db.commit()
    except WorkOrderNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="work_order_not_found") from exc
    except WorkOrderLocked as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="work_order_locked") from exc
    return _to_out(
        order,
        workshop_id=workshop_id,
        vehicle_repo=vehicle_repo,
        customer_repo=customer_repo,
        payment_repo=payment_repo,
    )


@work_orders_router.put("/work-orders/{order_id}/status", response_model=WorkOrderOut)
def change_status_route(
    order_id: uuid.UUID,
    payload: WorkOrderStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> WorkOrderOut:
    order_repo = SqlAlchemyWorkOrderRepository(db)
    item_repo = SqlAlchemyItemRepository(db)
    movement_repo = SqlAlchemyMovementRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    customer_repo = SqlAlchemyCustomerRepository(db)
    payment_repo = SqlAlchemyPaymentRepository(db)
    try:
        order = change_status(
            workshop_id=workshop_id,
            order_id=order_id,
            target=payload.status,
            created_by=current_user.id,
            order_repo=order_repo,
            item_repo=item_repo,
            movement_repo=movement_repo,
            payment_repo=payment_repo,
        )
        db.commit()
    except WorkOrderNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="work_order_not_found") from exc
    except InvalidStatusTransition as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="invalid_status_transition") from exc
    except WorkOrderHasPayments as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="work_order_has_payments") from exc
    except MovementIdConflict as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="movement_id_conflict") from exc
    except StockOutOfRange as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="stock_out_of_range"
        ) from exc
    return _to_out(
        order,
        workshop_id=workshop_id,
        vehicle_repo=vehicle_repo,
        customer_repo=customer_repo,
        payment_repo=payment_repo,
    )


@work_orders_router.post(
    "/work-orders/{order_id}/lines",
    response_model=WorkOrderOut,
    status_code=status.HTTP_201_CREATED,
)
def add_line_route(
    order_id: uuid.UUID,
    payload: WorkOrderLineCreateRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> WorkOrderOut:
    order_repo = SqlAlchemyWorkOrderRepository(db)
    item_repo = SqlAlchemyItemRepository(db)
    movement_repo = SqlAlchemyMovementRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    customer_repo = SqlAlchemyCustomerRepository(db)
    payment_repo = SqlAlchemyPaymentRepository(db)
    try:
        order, is_new = add_line(
            workshop_id=workshop_id,
            order_id=order_id,
            line_id=payload.id,
            kind=LineKind(payload.kind),
            item_id=payload.item_id,
            description=payload.description,
            quantity=payload.quantity,
            unit_price_cents=payload.unit_price_cents,
            created_by=current_user.id,
            order_repo=order_repo,
            item_repo=item_repo,
            movement_repo=movement_repo,
        )
        db.commit()
    except WorkOrderNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="work_order_not_found") from exc
    except WorkOrderLocked as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="work_order_locked") from exc
    except WorkOrderLineIdConflict as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="work_order_line_id_conflict") from exc
    except ItemNotFoundForLine as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="item_not_found") from exc
    except MovementIdConflict as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="movement_id_conflict") from exc
    except StockOutOfRange as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="stock_out_of_range"
        ) from exc
    if not is_new:
        response.status_code = status.HTTP_200_OK
    return _to_out(
        order,
        workshop_id=workshop_id,
        vehicle_repo=vehicle_repo,
        customer_repo=customer_repo,
        payment_repo=payment_repo,
    )


@work_orders_router.patch("/work-orders/{order_id}/lines/{line_id}", response_model=WorkOrderOut)
def update_line_route(
    order_id: uuid.UUID,
    line_id: uuid.UUID,
    payload: WorkOrderLineUpdateRequest,
    current_user: User = Depends(get_current_user),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> WorkOrderOut:
    order_repo = SqlAlchemyWorkOrderRepository(db)
    item_repo = SqlAlchemyItemRepository(db)
    movement_repo = SqlAlchemyMovementRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    customer_repo = SqlAlchemyCustomerRepository(db)
    payment_repo = SqlAlchemyPaymentRepository(db)
    fields = payload.model_dump(exclude_unset=True)
    try:
        order = update_line(
            workshop_id=workshop_id,
            order_id=order_id,
            line_id=line_id,
            fields=fields,
            created_by=current_user.id,
            order_repo=order_repo,
            item_repo=item_repo,
            movement_repo=movement_repo,
        )
        db.commit()
    except WorkOrderNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="work_order_not_found") from exc
    except WorkOrderLineNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="work_order_line_not_found") from exc
    except WorkOrderLocked as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="work_order_locked") from exc
    except MovementIdConflict as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="movement_id_conflict") from exc
    except StockOutOfRange as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="stock_out_of_range"
        ) from exc
    return _to_out(
        order,
        workshop_id=workshop_id,
        vehicle_repo=vehicle_repo,
        customer_repo=customer_repo,
        payment_repo=payment_repo,
    )


@work_orders_router.delete("/work-orders/{order_id}/lines/{line_id}", response_model=WorkOrderOut)
def remove_line_route(
    order_id: uuid.UUID,
    line_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> WorkOrderOut:
    order_repo = SqlAlchemyWorkOrderRepository(db)
    item_repo = SqlAlchemyItemRepository(db)
    movement_repo = SqlAlchemyMovementRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    customer_repo = SqlAlchemyCustomerRepository(db)
    payment_repo = SqlAlchemyPaymentRepository(db)
    try:
        order = remove_line(
            workshop_id=workshop_id,
            order_id=order_id,
            line_id=line_id,
            created_by=current_user.id,
            order_repo=order_repo,
            item_repo=item_repo,
            movement_repo=movement_repo,
        )
        db.commit()
    except WorkOrderNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="work_order_not_found") from exc
    except WorkOrderLineNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="work_order_line_not_found") from exc
    except WorkOrderLocked as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="work_order_locked") from exc
    except MovementIdConflict as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="movement_id_conflict") from exc
    except StockOutOfRange as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="stock_out_of_range"
        ) from exc
    return _to_out(
        order,
        workshop_id=workshop_id,
        vehicle_repo=vehicle_repo,
        customer_repo=customer_repo,
        payment_repo=payment_repo,
    )


@work_orders_router.post(
    "/work-orders/{order_id}/payments",
    response_model=WorkOrderOut,
    status_code=status.HTTP_201_CREATED,
)
def record_payment_route(
    order_id: uuid.UUID,
    payload: PaymentCreateRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> WorkOrderOut:
    order_repo = SqlAlchemyWorkOrderRepository(db)
    payment_repo = SqlAlchemyPaymentRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    customer_repo = SqlAlchemyCustomerRepository(db)
    try:
        _, is_new = record_payment(
            workshop_id=workshop_id,
            order_id=order_id,
            payment_id=payload.id,
            amount_cents=payload.amount_cents,
            method=PaymentMethod(payload.method),
            note=payload.note,
            created_by=current_user.id,
            order_repo=order_repo,
            payment_repo=payment_repo,
        )
        db.commit()
    except WorkOrderNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="work_order_not_found") from exc
    except PaymentIdConflict as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="payment_id_conflict") from exc
    except WorkOrderNotPayable as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="work_order_not_payable") from exc
    except PaymentExceedsBalance as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="payment_exceeds_balance") from exc

    order = get_work_order(workshop_id=workshop_id, order_id=order_id, order_repo=order_repo)
    if not is_new:
        response.status_code = status.HTTP_200_OK
    return _to_out(
        order,
        workshop_id=workshop_id,
        vehicle_repo=vehicle_repo,
        customer_repo=customer_repo,
        payment_repo=payment_repo,
    )


@work_orders_router.post(
    "/work-orders/{order_id}/payments/{payment_id}/void", response_model=WorkOrderOut
)
def void_payment_route(
    order_id: uuid.UUID,
    payment_id: uuid.UUID,
    payload: VoidPaymentRequest,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> WorkOrderOut:
    order_repo = SqlAlchemyWorkOrderRepository(db)
    payment_repo = SqlAlchemyPaymentRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    customer_repo = SqlAlchemyCustomerRepository(db)
    try:
        void_payment(
            workshop_id=workshop_id,
            order_id=order_id,
            payment_id=payment_id,
            reason=payload.reason,
            order_repo=order_repo,
            payment_repo=payment_repo,
        )
        db.commit()
    except WorkOrderNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="work_order_not_found") from exc
    except PaymentNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="payment_not_found") from exc

    order = get_work_order(workshop_id=workshop_id, order_id=order_id, order_repo=order_repo)
    return _to_out(
        order,
        workshop_id=workshop_id,
        vehicle_repo=vehicle_repo,
        customer_repo=customer_repo,
        payment_repo=payment_repo,
    )


@work_orders_router.get("/cash-summary", response_model=CashSummaryOut)
def daily_cash_summary_route(
    date: date | None = Query(default=None),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    clock: Clock = Depends(get_clock),
    db: Session = Depends(get_db),
) -> CashSummaryOut:
    payment_repo = SqlAlchemyPaymentRepository(db)
    order_repo = SqlAlchemyWorkOrderRepository(db)
    resolved_day, totals_cents, entries = daily_cash_summary(
        workshop_id=workshop_id,
        day=date,
        clock=clock,
        payment_repo=payment_repo,
        order_repo=order_repo,
    )
    return CashSummaryOut.from_domain(resolved_day, totals_cents, entries)
