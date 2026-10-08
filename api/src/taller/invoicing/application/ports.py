"""Ports the invoicing use cases depend on, implemented by adapters."""

import uuid
from typing import Protocol

from taller.invoicing.domain.document_number import DocumentType
from taller.invoicing.domain.profile import FiscalProfile
from taller.invoicing.domain.ranges import CaiRange


class FiscalProfileRepository(Protocol):
    def get(self, *, workshop_id: uuid.UUID) -> FiscalProfile | None: ...

    def get_for_update(self, *, workshop_id: uuid.UUID) -> FiscalProfile | None:
        """Like :meth:`get`, but locks the row (``SELECT ... FOR
        UPDATE``) -- the per-workshop fiscal mutex every other
        invoicing write also takes (AD-5).
        """
        ...

    def add(self, profile: FiscalProfile) -> None: ...

    def save(self, profile: FiscalProfile) -> None:
        """Persist every mutable field of an already-existing profile."""
        ...


class CaiRangeRepository(Protocol):
    """Only `list` is needed by this slice (readiness, the profile's
    code lock). `PA.S4` modifies this port to add `get_by_id`, `add`,
    `save`, and `allocate` for range registration and issuance.
    """

    def list(
        self, *, workshop_id: uuid.UUID, document_type: DocumentType | None = None
    ) -> list[CaiRange]: ...
