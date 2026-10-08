"""SQLAlchemy repositories for the fiscal profile and CAI ranges."""

import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from taller.invoicing.adapters.models import (
    CaiRangeModel,
    FiscalInvoiceLineModel,
    FiscalInvoiceModel,
    FiscalProfileModel,
)
from taller.invoicing.domain.document_number import DocumentType
from taller.invoicing.domain.documents import FiscalInvoice, FiscalInvoiceLine
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
    def __init__(self, session: Session) -> None:
        self._session = session

    def list(
        self, *, workshop_id: uuid.UUID, document_type: DocumentType | None = None
    ) -> list[CaiRange]:
        query = self._session.query(CaiRangeModel).filter(CaiRangeModel.workshop_id == workshop_id)
        if document_type is not None:
            query = query.filter(CaiRangeModel.document_type == document_type.value)
        return [_range_from_model(model) for model in query.all()]

    def get_by_id(self, *, workshop_id: uuid.UUID, range_id: uuid.UUID) -> CaiRange | None:
        model = (
            self._session.query(CaiRangeModel)
            .filter(CaiRangeModel.id == range_id, CaiRangeModel.workshop_id == workshop_id)
            .one_or_none()
        )
        return _range_from_model(model) if model is not None else None

    def add(self, cai_range: CaiRange) -> None:
        self._session.add(
            CaiRangeModel(
                id=cai_range.id,
                workshop_id=cai_range.workshop_id,
                document_type=cai_range.document_type.value,
                cai=cai_range.cai,
                establishment_code=cai_range.establishment_code,
                emission_point_code=cai_range.emission_point_code,
                range_start=cai_range.range_start,
                range_end=cai_range.range_end,
                next_number=cai_range.next_number,
                issue_deadline=cai_range.issue_deadline,
                created_by=cai_range.created_by,
                created_at=cai_range.created_at,
                updated_at=cai_range.updated_at,
            )
        )
        self._session.flush()

    def save(self, cai_range: CaiRange) -> None:
        model = self._session.get(CaiRangeModel, cai_range.id)
        assert model is not None  # noqa: S101 - caller always holds an existing row
        model.document_type = cai_range.document_type.value
        model.cai = cai_range.cai
        model.establishment_code = cai_range.establishment_code
        model.emission_point_code = cai_range.emission_point_code
        model.range_start = cai_range.range_start
        model.range_end = cai_range.range_end
        model.next_number = cai_range.next_number
        model.issue_deadline = cai_range.issue_deadline
        model.updated_at = cai_range.updated_at
        self._session.flush()

    def allocate(self, *, range_id: uuid.UUID, now: datetime) -> int | None:
        statement = (
            update(CaiRangeModel)
            .where(
                CaiRangeModel.id == range_id,
                CaiRangeModel.next_number <= CaiRangeModel.range_end,
            )
            .values(next_number=CaiRangeModel.next_number + 1, updated_at=now)
            .returning(CaiRangeModel.next_number - 1)
        )
        row = self._session.execute(statement).first()
        return row[0] if row is not None else None


def _invoice_line_from_model(model: FiscalInvoiceLineModel) -> FiscalInvoiceLine:
    return FiscalInvoiceLine(
        id=model.id,
        position=model.position,
        source_line_id=model.source_line_id,
        kind=model.kind,
        description=model.description,
        quantity=model.quantity,
        unit_price_cents=model.unit_price_cents,
        line_total_cents=model.line_total_cents,
    )


def _invoice_from_model(model: FiscalInvoiceModel, lines: list[FiscalInvoiceLine]) -> FiscalInvoice:
    return FiscalInvoice(
        id=model.id,
        workshop_id=model.workshop_id,
        order_id=model.order_id,
        order_number=model.order_number,
        cai_range_id=model.cai_range_id,
        correlative=model.correlative,
        number=model.number,
        issued_at=model.issued_at,
        issue_date=model.issue_date,
        issuer_rtn=model.issuer_rtn,
        issuer_legal_name=model.issuer_legal_name,
        issuer_trade_name=model.issuer_trade_name,
        issuer_address=model.issuer_address,
        issuer_phone=model.issuer_phone,
        issuer_email=model.issuer_email,
        cai=model.cai,
        range_first_number=model.range_first_number,
        range_last_number=model.range_last_number,
        issue_deadline=model.issue_deadline,
        buyer_name=model.buyer_name,
        buyer_rtn=model.buyer_rtn,
        exempt_cents=model.exempt_cents,
        exonerated_cents=model.exonerated_cents,
        discount_cents=model.discount_cents,
        taxable_15_cents=model.taxable_15_cents,
        isv_15_cents=model.isv_15_cents,
        total_cents=model.total_cents,
        total_in_words=model.total_in_words,
        credited_at=model.credited_at,
        created_by=model.created_by,
        created_at=model.created_at,
        lines=lines,
    )


class SqlAlchemyFiscalInvoiceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _lines_for(self, invoice_id: uuid.UUID) -> list[FiscalInvoiceLine]:
        models = (
            self._session.query(FiscalInvoiceLineModel)
            .filter(FiscalInvoiceLineModel.invoice_id == invoice_id)
            .order_by(FiscalInvoiceLineModel.position)
            .all()
        )
        return [_invoice_line_from_model(model) for model in models]

    def get_by_id(self, *, workshop_id: uuid.UUID, invoice_id: uuid.UUID) -> FiscalInvoice | None:
        model = (
            self._session.query(FiscalInvoiceModel)
            .filter(
                FiscalInvoiceModel.id == invoice_id,
                FiscalInvoiceModel.workshop_id == workshop_id,
            )
            .one_or_none()
        )
        if model is None:
            return None
        return _invoice_from_model(model, self._lines_for(invoice_id))

    def has_active_for_order(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID) -> bool:
        return (
            self._session.query(FiscalInvoiceModel)
            .filter(
                FiscalInvoiceModel.workshop_id == workshop_id,
                FiscalInvoiceModel.order_id == order_id,
                FiscalInvoiceModel.credited_at.is_(None),
            )
            .first()
            is not None
        )

    def list_for_order(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID) -> list[FiscalInvoice]:
        models = (
            self._session.query(FiscalInvoiceModel)
            .filter(
                FiscalInvoiceModel.workshop_id == workshop_id,
                FiscalInvoiceModel.order_id == order_id,
            )
            .order_by(FiscalInvoiceModel.issued_at.desc())
            .all()
        )
        return [_invoice_from_model(model, self._lines_for(model.id)) for model in models]

    def add(self, invoice: FiscalInvoice) -> None:
        self._session.add(
            FiscalInvoiceModel(
                id=invoice.id,
                workshop_id=invoice.workshop_id,
                order_id=invoice.order_id,
                order_number=invoice.order_number,
                cai_range_id=invoice.cai_range_id,
                correlative=invoice.correlative,
                number=invoice.number,
                issued_at=invoice.issued_at,
                issue_date=invoice.issue_date,
                issuer_rtn=invoice.issuer_rtn,
                issuer_legal_name=invoice.issuer_legal_name,
                issuer_trade_name=invoice.issuer_trade_name,
                issuer_address=invoice.issuer_address,
                issuer_phone=invoice.issuer_phone,
                issuer_email=invoice.issuer_email,
                cai=invoice.cai,
                range_first_number=invoice.range_first_number,
                range_last_number=invoice.range_last_number,
                issue_deadline=invoice.issue_deadline,
                buyer_name=invoice.buyer_name,
                buyer_rtn=invoice.buyer_rtn,
                exempt_cents=invoice.exempt_cents,
                exonerated_cents=invoice.exonerated_cents,
                discount_cents=invoice.discount_cents,
                taxable_15_cents=invoice.taxable_15_cents,
                isv_15_cents=invoice.isv_15_cents,
                total_cents=invoice.total_cents,
                total_in_words=invoice.total_in_words,
                credited_at=invoice.credited_at,
                created_by=invoice.created_by,
                created_at=invoice.created_at,
            )
        )
        # Flushed before the lines so the invoice row exists for their FK
        # (mirrors `SqlAlchemyWorkOrderRepository.add`'s order-then-lines
        # ordering): no `relationship()` connects the two mapped classes,
        # so the unit of work has no dependency to sort insertion by.
        self._session.flush()
        for line in invoice.lines:
            self._session.add(
                FiscalInvoiceLineModel(
                    id=line.id,
                    workshop_id=invoice.workshop_id,
                    invoice_id=invoice.id,
                    position=line.position,
                    source_line_id=line.source_line_id,
                    kind=line.kind,
                    description=line.description,
                    quantity=line.quantity,
                    unit_price_cents=line.unit_price_cents,
                    line_total_cents=line.line_total_cents,
                )
            )
        self._session.flush()
