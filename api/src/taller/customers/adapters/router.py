"""HTTP routes for customer records."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from taller.customers.adapters.repositories import SqlAlchemyCustomerRepository
from taller.customers.adapters.schemas import (
    CustomerCreateRequest,
    CustomerOut,
    CustomerUpdateRequest,
)
from taller.customers.application.use_cases import (
    archive_customer,
    create_customer,
    get_customer,
    list_customers,
    update_customer,
)
from taller.customers.domain.entities import Customer
from taller.customers.domain.errors import CustomerIdConflict, CustomerNotFound
from taller.identity.adapters.dependencies import get_current_workshop_id
from taller.identity.domain.errors import InvalidPhoneNumber
from taller.shared.db import get_db

customers_router = APIRouter(tags=["customers"])

#: Default PostgreSQL primary key constraint name. Customer ids are global
#: primary keys, not scoped to a workshop, so a client-supplied id
#: colliding with another workshop's row surfaces here as a violation of
#: this constraint, never as the workshop-scoped pre-check (which cannot
#: see the other workshop's row at all). Mirrors
#: `taller.inventory.adapters.router._ITEM_PK_CONSTRAINT`.
_CUSTOMER_PK_CONSTRAINT = "customers_pkey"


def _violated_constraint(exc: IntegrityError) -> str | None:
    """Mirrors `taller.identity.adapters.router._violated_constraint`."""
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)


@customers_router.get("/customers", response_model=list[CustomerOut])
def list_customers_route(
    q: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> list[CustomerOut]:
    customer_repo = SqlAlchemyCustomerRepository(db)
    customers = list_customers(
        workshop_id=workshop_id,
        query=q,
        include_archived=include_archived,
        customer_repo=customer_repo,
    )
    return [CustomerOut.from_domain(customer) for customer in customers]


@customers_router.post(
    "/customers", response_model=CustomerOut, status_code=status.HTTP_201_CREATED
)
def create_customer_route(
    payload: CustomerCreateRequest,
    response: Response,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> CustomerOut:
    customer_repo = SqlAlchemyCustomerRepository(db)

    def _attempt() -> tuple[Customer, bool]:
        result = create_customer(
            workshop_id=workshop_id,
            customer_id=payload.id,
            full_name=payload.full_name,
            phone=payload.phone,
            notes=payload.notes,
            customer_repo=customer_repo,
        )
        db.commit()
        return result

    try:
        customer, is_new = _attempt()
    except InvalidPhoneNumber as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_phone") from exc
    except CustomerIdConflict as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="customer_id_conflict") from exc
    except IntegrityError as first_exc:
        db.rollback()
        # Another request committed a colliding id between our pre-check
        # and our insert. Retry once: the pre-check now sees the committed
        # row and raises the precise conflict instead of a raw database
        # error.
        try:
            customer, is_new = _attempt()
        except CustomerIdConflict as exc:
            db.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, detail="customer_id_conflict") from exc
        except IntegrityError as exc:
            db.rollback()
            # A client-supplied id already used by another workshop: our
            # tenant-scoped pre-check cannot see that row even on retry, so
            # it never resolves into CustomerIdConflict above. Report the
            # same 409 a same-workshop id conflict gets, and nothing else
            # about the other workshop's row. Any other integrity error
            # here is a genuine bug and must not be reported as a conflict.
            if _violated_constraint(exc) == _CUSTOMER_PK_CONSTRAINT:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, detail="customer_id_conflict"
                ) from exc
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, detail="customer_create_failed"
            ) from (exc or first_exc)

    if not is_new:
        response.status_code = status.HTTP_200_OK
    return CustomerOut.from_domain(customer)


@customers_router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer_route(
    customer_id: uuid.UUID,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> CustomerOut:
    customer_repo = SqlAlchemyCustomerRepository(db)
    try:
        customer = get_customer(
            workshop_id=workshop_id, customer_id=customer_id, customer_repo=customer_repo
        )
    except CustomerNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="customer_not_found") from exc
    return CustomerOut.from_domain(customer)


@customers_router.patch("/customers/{customer_id}", response_model=CustomerOut)
def update_customer_route(
    customer_id: uuid.UUID,
    payload: CustomerUpdateRequest,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> CustomerOut:
    customer_repo = SqlAlchemyCustomerRepository(db)
    fields = payload.model_dump(exclude_unset=True)
    try:
        customer = update_customer(
            workshop_id=workshop_id,
            customer_id=customer_id,
            fields=fields,
            customer_repo=customer_repo,
        )
        db.commit()
    except CustomerNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="customer_not_found") from exc
    except InvalidPhoneNumber as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_phone") from exc
    return CustomerOut.from_domain(customer)


@customers_router.post("/customers/{customer_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_customer_route(
    customer_id: uuid.UUID,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> None:
    customer_repo = SqlAlchemyCustomerRepository(db)
    try:
        archive_customer(
            workshop_id=workshop_id, customer_id=customer_id, customer_repo=customer_repo
        )
        db.commit()
    except CustomerNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="customer_not_found") from exc
