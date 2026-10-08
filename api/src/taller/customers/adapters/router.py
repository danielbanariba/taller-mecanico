"""HTTP routes for customer records."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from taller.customers.adapters.repositories import (
    SqlAlchemyCustomerRepository,
    SqlAlchemyVehicleRepository,
)
from taller.customers.adapters.schemas import (
    CustomerCreateRequest,
    CustomerOut,
    CustomerUpdateRequest,
    VehicleCreateRequest,
    VehicleDetailOut,
    VehicleOut,
    VehicleUpdateRequest,
)
from taller.customers.application.use_cases import (
    archive_customer,
    archive_vehicle,
    create_customer,
    create_vehicle,
    get_customer,
    get_vehicle,
    list_customers,
    list_vehicles_for_customer,
    update_customer,
    update_vehicle,
)
from taller.customers.domain.entities import Customer, Vehicle
from taller.customers.domain.errors import (
    CustomerIdConflict,
    CustomerNotFound,
    InvalidPlate,
    InvalidRtn,
    PlateTaken,
    VehicleIdConflict,
    VehicleNotFound,
)
from taller.identity.adapters.dependencies import get_current_workshop_id
from taller.identity.domain.errors import InvalidPhoneNumber
from taller.shared.db import get_db

customers_router = APIRouter(tags=["customers"])
vehicles_router = APIRouter(tags=["vehicles"])

#: Default PostgreSQL primary key constraint name. Customer ids are global
#: primary keys, not scoped to a workshop, so a client-supplied id
#: colliding with another workshop's row surfaces here as a violation of
#: this constraint, never as the workshop-scoped pre-check (which cannot
#: see the other workshop's row at all). Mirrors
#: `taller.inventory.adapters.router._ITEM_PK_CONSTRAINT`.
_CUSTOMER_PK_CONSTRAINT = "customers_pkey"
_VEHICLE_PK_CONSTRAINT = "vehicles_pkey"

#: The partial unique index on active vehicle plates (declared on
#: `VehicleModel`, see `taller.customers.adapters.models`).
_ACTIVE_PLATE_INDEX = "uq_vehicles_workshop_plate_active"


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
            billing_name=payload.billing_name,
            rtn=payload.rtn,
            customer_repo=customer_repo,
        )
        db.commit()
        return result

    try:
        customer, is_new = _attempt()
    except InvalidPhoneNumber as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_phone") from exc
    except InvalidRtn as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_rtn") from exc
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
    except InvalidRtn as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_rtn") from exc
    return CustomerOut.from_domain(customer)


@customers_router.post("/customers/{customer_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_customer_route(
    customer_id: uuid.UUID,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> None:
    customer_repo = SqlAlchemyCustomerRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    try:
        archive_customer(
            workshop_id=workshop_id,
            customer_id=customer_id,
            customer_repo=customer_repo,
            vehicle_repo=vehicle_repo,
        )
        db.commit()
    except CustomerNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="customer_not_found") from exc


def _vehicle_conflict(exc: Exception) -> HTTPException:
    if isinstance(exc, VehicleIdConflict):
        return HTTPException(status.HTTP_409_CONFLICT, detail="vehicle_id_conflict")
    return HTTPException(status.HTTP_409_CONFLICT, detail="plate_taken")


@vehicles_router.get("/customers/{customer_id}/vehicles", response_model=list[VehicleOut])
def list_vehicles_for_customer_route(
    customer_id: uuid.UUID,
    include_archived: bool = Query(default=False),
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> list[VehicleOut]:
    customer_repo = SqlAlchemyCustomerRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    try:
        vehicles = list_vehicles_for_customer(
            workshop_id=workshop_id,
            customer_id=customer_id,
            include_archived=include_archived,
            customer_repo=customer_repo,
            vehicle_repo=vehicle_repo,
        )
    except CustomerNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="customer_not_found") from exc
    return [VehicleOut.from_domain(vehicle) for vehicle in vehicles]


@vehicles_router.post("/vehicles", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle_route(
    payload: VehicleCreateRequest,
    response: Response,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> VehicleOut:
    customer_repo = SqlAlchemyCustomerRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)

    def _attempt() -> tuple[Vehicle, bool]:
        result = create_vehicle(
            workshop_id=workshop_id,
            vehicle_id=payload.id,
            customer_id=payload.customer_id,
            vehicle_type=payload.vehicle_type,
            make=payload.make,
            model=payload.model,
            year=payload.year,
            color=payload.color,
            plate=payload.plate,
            notes=payload.notes,
            customer_repo=customer_repo,
            vehicle_repo=vehicle_repo,
        )
        db.commit()
        return result

    try:
        vehicle, is_new = _attempt()
    except CustomerNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="customer_not_found") from exc
    except InvalidPlate as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_plate") from exc
    except (VehicleIdConflict, PlateTaken) as exc:
        db.rollback()
        raise _vehicle_conflict(exc) from exc
    except IntegrityError:
        db.rollback()
        # Another request committed a colliding id, or claimed the plate,
        # between our pre-checks and our insert. Retry once: the
        # pre-checks now see the committed row and raise the precise
        # conflict instead of a raw database error.
        try:
            vehicle, is_new = _attempt()
        except CustomerNotFound as exc:
            db.rollback()
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="customer_not_found") from exc
        except InvalidPlate as exc:
            db.rollback()
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_plate"
            ) from exc
        except (VehicleIdConflict, PlateTaken) as exc:
            db.rollback()
            raise _vehicle_conflict(exc) from exc
        except IntegrityError as exc:
            db.rollback()
            # The pre-checks still cannot see the race (e.g. monkeypatched
            # away in a test, or a client-supplied id already used by
            # another workshop, invisible to our tenant-scoped pre-check
            # even on retry): the database's constraints are the real
            # guarantee. Map the two conflicts we expect to their precise
            # detail; any other integrity error here is a genuine bug and
            # must not be reported as one of those conflicts (AD-9).
            violated = _violated_constraint(exc)
            if violated == _ACTIVE_PLATE_INDEX:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="plate_taken") from exc
            if violated == _VEHICLE_PK_CONSTRAINT:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="vehicle_id_conflict") from exc
            raise

    if not is_new:
        response.status_code = status.HTTP_200_OK
    return VehicleOut.from_domain(vehicle)


@vehicles_router.get("/vehicles/{vehicle_id}", response_model=VehicleDetailOut)
def get_vehicle_route(
    vehicle_id: uuid.UUID,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> VehicleDetailOut:
    customer_repo = SqlAlchemyCustomerRepository(db)
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    try:
        vehicle = get_vehicle(
            workshop_id=workshop_id, vehicle_id=vehicle_id, vehicle_repo=vehicle_repo
        )
        owner = get_customer(
            workshop_id=workshop_id, customer_id=vehicle.customer_id, customer_repo=customer_repo
        )
    except (VehicleNotFound, CustomerNotFound) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="vehicle_not_found") from exc
    return VehicleDetailOut.from_domain(vehicle, owner)


@vehicles_router.patch("/vehicles/{vehicle_id}", response_model=VehicleOut)
def update_vehicle_route(
    vehicle_id: uuid.UUID,
    payload: VehicleUpdateRequest,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> VehicleOut:
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    fields = payload.model_dump(exclude_unset=True)
    try:
        vehicle = update_vehicle(
            workshop_id=workshop_id,
            vehicle_id=vehicle_id,
            fields=fields,
            vehicle_repo=vehicle_repo,
        )
        db.commit()
    except VehicleNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="vehicle_not_found") from exc
    except InvalidPlate as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="invalid_plate") from exc
    except PlateTaken as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="plate_taken") from exc
    except IntegrityError as exc:
        db.rollback()
        # A concurrent create/edit committed the same plate after our
        # pre-check: the unique index is the real guarantee. Any other
        # integrity error is a bug and must not be reported as a taken
        # plate.
        if _violated_constraint(exc) != _ACTIVE_PLATE_INDEX:
            raise
        raise HTTPException(status.HTTP_409_CONFLICT, detail="plate_taken") from exc
    return VehicleOut.from_domain(vehicle)


@vehicles_router.post("/vehicles/{vehicle_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_vehicle_route(
    vehicle_id: uuid.UUID,
    workshop_id: uuid.UUID = Depends(get_current_workshop_id),
    db: Session = Depends(get_db),
) -> None:
    vehicle_repo = SqlAlchemyVehicleRepository(db)
    try:
        archive_vehicle(workshop_id=workshop_id, vehicle_id=vehicle_id, vehicle_repo=vehicle_repo)
        db.commit()
    except VehicleNotFound as exc:
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="vehicle_not_found") from exc
