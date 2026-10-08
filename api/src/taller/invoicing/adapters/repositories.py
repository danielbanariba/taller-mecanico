"""SQLAlchemy repositories for the fiscal profile and CAI ranges."""

import uuid

from sqlalchemy.orm import Session

from taller.invoicing.adapters.models import CaiRangeModel, FiscalProfileModel
from taller.invoicing.domain.document_number import DocumentType
from taller.invoicing.domain.profile import FiscalProfile
from taller.invoicing.domain.ranges import CaiRange


def _profile_from_model(model: FiscalProfileModel) -> FiscalProfile:
    return FiscalProfile(
        workshop_id=model.workshop_id,
        rtn=model.rtn,
        legal_name=model.legal_name,
        trade_name=model.trade_name,
        address=model.address,
        phone=model.phone,
        email=model.email,
        establishment_code=model.establishment_code,
        emission_point_code=model.emission_point_code,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _range_from_model(model: CaiRangeModel) -> CaiRange:
    return CaiRange(
        id=model.id,
        workshop_id=model.workshop_id,
        document_type=DocumentType(model.document_type),
        cai=model.cai,
        establishment_code=model.establishment_code,
        emission_point_code=model.emission_point_code,
        range_start=model.range_start,
        range_end=model.range_end,
        next_number=model.next_number,
        issue_deadline=model.issue_deadline,
        created_by=model.created_by,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyFiscalProfileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, *, workshop_id: uuid.UUID) -> FiscalProfile | None:
        model = self._session.get(FiscalProfileModel, workshop_id)
        return _profile_from_model(model) if model is not None else None

    def get_for_update(self, *, workshop_id: uuid.UUID) -> FiscalProfile | None:
        model = (
            self._session.query(FiscalProfileModel)
            .filter(FiscalProfileModel.workshop_id == workshop_id)
            .with_for_update()
            .one_or_none()
        )
        return _profile_from_model(model) if model is not None else None

    def add(self, profile: FiscalProfile) -> None:
        self._session.add(
            FiscalProfileModel(
                workshop_id=profile.workshop_id,
                rtn=profile.rtn,
                legal_name=profile.legal_name,
                trade_name=profile.trade_name,
                address=profile.address,
                phone=profile.phone,
                email=profile.email,
                establishment_code=profile.establishment_code,
                emission_point_code=profile.emission_point_code,
                created_at=profile.created_at,
                updated_at=profile.updated_at,
            )
        )
        self._session.flush()

    def save(self, profile: FiscalProfile) -> None:
        model = self._session.get(FiscalProfileModel, profile.workshop_id)
        assert model is not None  # noqa: S101 - caller always holds a locked, existing row
        model.rtn = profile.rtn
        model.legal_name = profile.legal_name
        model.trade_name = profile.trade_name
        model.address = profile.address
        model.phone = profile.phone
        model.email = profile.email
        model.establishment_code = profile.establishment_code
        model.emission_point_code = profile.emission_point_code
        model.updated_at = profile.updated_at
        self._session.flush()


class SqlAlchemyCaiRangeRepository:
    """Implements `CaiRangeRepository.list` for now; `PA.S4` extends
    this class with `get_by_id`, `add`, `save`, and `allocate`.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def list(
        self, *, workshop_id: uuid.UUID, document_type: DocumentType | None = None
    ) -> list[CaiRange]:
        query = self._session.query(CaiRangeModel).filter(CaiRangeModel.workshop_id == workshop_id)
        if document_type is not None:
            query = query.filter(CaiRangeModel.document_type == document_type.value)
        return [_range_from_model(model) for model in query.all()]
