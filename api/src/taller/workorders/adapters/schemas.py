"""Pydantic request/response schemas for the work-orders HTTP API."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from taller.customers.domain.entities import Customer, Vehicle, VehicleType
from taller.workorders.domain.entities import (
    CashSummaryEntry,
    InvoiceRef,
    LineKind,
    Payment,
    PaymentMethod,
    WorkOrder,
    WorkOrderLine,
)
from taller.workorders.domain.money import (
    balance_cents,
    line_subtotal_cents,
    order_total_cents,
    paid_cents,
)
from taller.workorders.domain.status import EDITABLE, PAYABLE, TRANSITIONS, WorkOrderStatus

#: Design's bound for `odometer_km`.
MAX_ODOMETER_KM = 2_000_000


class WorkOrderCreateRequest(BaseModel):
    """`id` is required, unlike items/customers/vehicles: an order create
    without a client id cannot be made retry-safe, and a retry would burn
    a number (`design.md`'s AD-14).
    """

    id: uuid.UUID
    vehicle_id: uuid.UUID
    complaint: str | None = Field(default=None, max_length=1000)
    odometer_km: int | None = Field(default=None, ge=0, le=MAX_ODOMETER_KM)
    notes: str | None = None


class WorkOrderUpdateRequest(BaseModel):
    """Only explicitly set fields are applied. Every field is nullable at
    the domain level, so an explicit `null` is a valid way to clear it --
    unlike `CustomerUpdateRequest.full_name`, none of these need a
    reject-null guard.
    """

    complaint: str | None = Field(default=None, max_length=1000)
    odometer_km: int | None = Field(default=None, ge=0, le=MAX_ODOMETER_KM)
    notes: str | None = None


class WorkOrderStatusUpdateRequest(BaseModel):
    """`PUT /work-orders/{id}/status` body (`design.md`'s AD-7): an
    idempotent `PUT` of a target status over the acyclic machine.
    """

    status: WorkOrderStatus


class WorkOrderLineCreateRequest(BaseModel):
    id: uuid.UUID
    kind: Literal["labor", "inventory_part", "external_part"]
    item_id: uuid.UUID | None = None
    description: str = Field(min_length=1, max_length=200)
    quantity: int = Field(ge=1, le=10_000)
    unit_price_cents: int = Field(ge=0, le=1_000_000_000)

    @model_validator(mode="after")
    def _item_matches_kind(self) -> "WorkOrderLineCreateRequest":
        """Mirrors `ck_work_order_lines_item_matches_kind`: an
        `inventory_part` line must reference an item, and no other kind
        may.
        """
        if (self.kind == "inventory_part") != (self.item_id is not None):
            raise ValueError("item_id is required for inventory_part lines only")
        return self


class WorkOrderLineUpdateRequest(BaseModel):
    """`kind` and `item_id` are intentionally absent: a line's part is
    immutable after creation (see the `work-orders` capability spec).
    """

    description: str | None = Field(default=None, min_length=1, max_length=200)
    quantity: int | None = Field(default=None, ge=1, le=10_000)
    unit_price_cents: int | None = Field(default=None, ge=0, le=1_000_000_000)

    @field_validator("description")
    @classmethod
    def _reject_null_description(cls, value: str | None) -> str:
        """Reject an explicit `description: null` (mirrors
        `CustomerUpdateRequest._reject_null_full_name`): without this
        guard the `None` union branch bypasses `min_length`, and
        `update_line` would crash calling `.strip()` on `None`.
        """
        if value is None:
            raise ValueError("description cannot be null")
        return value

    @field_validator("quantity")
    @classmethod
    def _reject_null_quantity(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("quantity cannot be null")
        return value

    @field_validator("unit_price_cents")
    @classmethod
    def _reject_null_unit_price(cls, value: int | None) -> int:
        if value is None:
            raise ValueError("unit_price_cents cannot be null")
        return value


class PaymentCreateRequest(BaseModel):
    """`id` is required, like every other create in this feature (an order
    without a client id cannot be made retry-safe, `design.md`'s AD-14).
    `method` is a closed `Literal`, so an unsupported value (the Spanish
    label, or any other string) is rejected as a standard 422 -- the
    `payments` spec's own requirement, with nothing further to validate.
    """

    id: uuid.UUID
    amount_cents: int = Field(gt=0)
    method: Literal["cash", "transfer", "card", "other"]
    note: str | None = Field(default=None, max_length=200)


class VoidPaymentRequest(BaseModel):
    """`reason` is required (not optional/nullable): an explicit `null` or
    a missing field are both rejected as a standard 422, per the
    `payments` spec's "Voiding a payment requires a reason".
    """

    reason: str = Field(min_length=1, max_length=200)


class PaymentOut(BaseModel):
    """`voided_at`/`void_reason` are not in `design.md`'s original
    `PaymentOut` shape, which predates the voiding resolved question (the
    same delta `tasks.md`'s P3.S1.T3 applies to the `payments` table): the
    web needs them to render a voided payment struck through, with its
    reason.
    """

    id: uuid.UUID
    amount_cents: int
    method: Literal["cash", "transfer", "card", "other"]
    note: str | None
    paid_at: datetime
    voided_at: datetime | None
    void_reason: str | None

    @classmethod
    def from_domain(cls, payment: Payment) -> "PaymentOut":
        return cls(
            id=payment.id,
            amount_cents=payment.amount_cents,
            method=payment.method,
            note=payment.note,
            paid_at=payment.paid_at,
            voided_at=payment.voided_at,
            void_reason=payment.void_reason,
        )


class WorkOrderVehicleOut(BaseModel):
    id: uuid.UUID
    vehicle_type: VehicleType
    make: str
    model: str | None
    year: int | None
    plate: str | None

    @classmethod
    def from_domain(cls, vehicle: Vehicle) -> "WorkOrderVehicleOut":
        return cls(
            id=vehicle.id,
            vehicle_type=vehicle.vehicle_type,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            plate=vehicle.plate,
        )


class WorkOrderCustomerOut(BaseModel):
    id: uuid.UUID
    full_name: str

    @classmethod
    def from_domain(cls, customer: Customer) -> "WorkOrderCustomerOut":
        return cls(id=customer.id, full_name=customer.full_name)


class WorkOrderCustomerDetailOut(WorkOrderCustomerOut):
    phone: str | None
    phone_is_mobile: bool | None

    @classmethod
    def from_domain(cls, customer: Customer) -> "WorkOrderCustomerDetailOut":  # type: ignore[override]
        return cls(
            id=customer.id,
            full_name=customer.full_name,
            phone=customer.phone,
            phone_is_mobile=customer.phone_is_mobile,
        )


class WorkOrderLineOut(BaseModel):
    id: uuid.UUID
    kind: LineKind
    item_id: uuid.UUID | None
    description: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int
    stock_posted_quantity: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, line: WorkOrderLine) -> "WorkOrderLineOut":
        return cls(
            id=line.id,
            kind=line.kind,
            item_id=line.item_id,
            description=line.description,
            quantity=line.quantity,
            unit_price_cents=line.unit_price_cents,
            line_total_cents=line_subtotal_cents(line),
            stock_posted_quantity=line.stock_posted_quantity,
            created_at=line.created_at,
            updated_at=line.updated_at,
        )


class WorkOrderSummaryOut(BaseModel):
    id: uuid.UUID
    number: int
    status: WorkOrderStatus
    vehicle: WorkOrderVehicleOut
    customer: WorkOrderCustomerOut
    total_cents: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(
        cls, order: WorkOrder, *, vehicle: Vehicle, customer: Customer, total_cents: int
    ) -> "WorkOrderSummaryOut":
        return cls(
            id=order.id,
            number=order.number,
            status=order.status,
            vehicle=WorkOrderVehicleOut.from_domain(vehicle),
            customer=WorkOrderCustomerOut.from_domain(customer),
            total_cents=total_cents,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


class InvoiceRefOut(BaseModel):
    id: uuid.UUID
    number: str

    @classmethod
    def from_domain(cls, invoice_ref: InvoiceRef) -> "InvoiceRefOut":
        return cls(id=invoice_ref.id, number=invoice_ref.number)


class WorkOrderOut(BaseModel):
    id: uuid.UUID
    number: int
    status: WorkOrderStatus
    vehicle: WorkOrderVehicleOut
    customer: WorkOrderCustomerDetailOut
    complaint: str | None
    odometer_km: int | None
    notes: str | None
    lines: list[WorkOrderLineOut]
    total_cents: int
    allowed_transitions: list[WorkOrderStatus]
    lines_editable: bool
    active_invoice: InvoiceRefOut | None
    payments: list[PaymentOut]
    paid_cents: int
    balance_cents: int
    accepts_payments: bool
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    delivered_at: datetime | None
    cancelled_at: datetime | None

    @classmethod
    def from_domain(
        cls,
        order: WorkOrder,
        *,
        vehicle: Vehicle,
        customer: Customer,
        payments: list[Payment],
        active_invoice: InvoiceRef | None,
    ) -> "WorkOrderOut":
        return cls(
            id=order.id,
            number=order.number,
            status=order.status,
            vehicle=WorkOrderVehicleOut.from_domain(vehicle),
            customer=WorkOrderCustomerDetailOut.from_domain(customer),
            complaint=order.complaint,
            odometer_km=order.odometer_km,
            notes=order.notes,
            lines=[
                WorkOrderLineOut.from_domain(line)
                for line in order.lines
                if line.removed_at is None
            ],
            total_cents=order_total_cents(order.lines),
            allowed_transitions=sorted(TRANSITIONS[order.status]),
            lines_editable=order.status in EDITABLE and active_invoice is None,
            active_invoice=(
                InvoiceRefOut.from_domain(active_invoice) if active_invoice is not None else None
            ),
            payments=[PaymentOut.from_domain(payment) for payment in payments],
            paid_cents=paid_cents(payments),
            balance_cents=balance_cents(order.lines, payments),
            accepts_payments=order.status in PAYABLE,
            created_at=order.created_at,
            updated_at=order.updated_at,
            approved_at=order.approved_at,
            started_at=order.started_at,
            completed_at=order.completed_at,
            delivered_at=order.delivered_at,
            cancelled_at=order.cancelled_at,
        )


class CashSummaryTotalsOut(BaseModel):
    cash: int
    transfer: int
    card: int
    other: int


class CashSummaryPaymentOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    order_number: int
    amount_cents: int
    method: Literal["cash", "transfer", "card", "other"]
    paid_at: datetime

    @classmethod
    def from_domain(cls, entry: CashSummaryEntry) -> "CashSummaryPaymentOut":
        return cls(
            id=entry.payment.id,
            order_id=entry.payment.order_id,
            order_number=entry.order_number,
            amount_cents=entry.payment.amount_cents,
            method=entry.payment.method,
            paid_at=entry.payment.paid_at,
        )


class CashSummaryOut(BaseModel):
    date: date
    totals_cents: CashSummaryTotalsOut
    total_cents: int
    payments: list[CashSummaryPaymentOut]

    @classmethod
    def from_domain(
        cls,
        day: date,
        totals_cents: dict[PaymentMethod, int],
        entries: list[CashSummaryEntry],
    ) -> "CashSummaryOut":
        return cls(
            date=day,
            totals_cents=CashSummaryTotalsOut(
                cash=totals_cents[PaymentMethod.cash],
                transfer=totals_cents[PaymentMethod.transfer],
                card=totals_cents[PaymentMethod.card],
                other=totals_cents[PaymentMethod.other],
            ),
            total_cents=sum(totals_cents.values()),
            payments=[CashSummaryPaymentOut.from_domain(entry) for entry in entries],
        )
