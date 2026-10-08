"""Domain errors for the customers feature (customers and vehicles)."""

import uuid


class CustomerNotFound(Exception):
    """Raised when a customer does not exist in the caller's workshop.

    Also used when the customer exists but belongs to another workshop, so
    tenant isolation never leaks whether the customer exists at all.
    """

    def __init__(self, customer_id: uuid.UUID) -> None:
        super().__init__(f"Customer not found: {customer_id}")
        self.customer_id = customer_id


class CustomerIdConflict(Exception):
    """Raised when a client-supplied customer id exists with different fields."""

    def __init__(self, customer_id: uuid.UUID) -> None:
        super().__init__(f"Customer id already exists with different fields: {customer_id}")
        self.customer_id = customer_id


class VehicleNotFound(Exception):
    """Raised when a vehicle does not exist in the caller's workshop.

    Also used when the vehicle exists but belongs to another workshop.
    """

    def __init__(self, vehicle_id: uuid.UUID) -> None:
        super().__init__(f"Vehicle not found: {vehicle_id}")
        self.vehicle_id = vehicle_id


class VehicleIdConflict(Exception):
    """Raised when a client-supplied vehicle id exists with different fields."""

    def __init__(self, vehicle_id: uuid.UUID) -> None:
        super().__init__(f"Vehicle id already exists with different fields: {vehicle_id}")
        self.vehicle_id = vehicle_id


class PlateTaken(Exception):
    """Raised when another active vehicle in the workshop already has this plate."""

    def __init__(self, plate: str) -> None:
        super().__init__(f"Plate already in use: {plate}")
        self.plate = plate


class InvalidPlate(ValueError):
    """Raised when a value cannot be normalized into a valid plate."""

    def __init__(self, raw: str) -> None:
        super().__init__(f"Invalid plate: {raw!r}")
        self.raw = raw


class InvalidRtn(ValueError):
    """Raised when a value cannot be normalized into a valid 14-digit RTN."""

    def __init__(self, raw: str) -> None:
        super().__init__(f"Invalid RTN: {raw!r}")
        self.raw = raw
