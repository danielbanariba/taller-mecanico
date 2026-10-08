import { useState } from "react";
import { useNavigate, useParams } from "react-router";

import { ApiError } from "../../../shared/api/http";
import { useOnlineStatus } from "../../../shared/offline/useOnlineStatus";
import { Alert } from "../../../shared/ui/Alert";
import { LinkButton } from "../../../shared/ui/LinkButton";
import { Spinner } from "../../../shared/ui/Spinner";
import type { DocumentType } from "../api";
import { getInvoicingErrorMessage, invoicingCopy } from "../copy";
import { useCreateCaiRange, useInvoicingSettings, useUpdateCaiRange } from "../hooks";
import { CaiRangeForm, type CaiRangeFormSubmitValues } from "./CaiRangeForm";

/**
 * Container: both `/ordenes/facturacion/rangos/nuevo` (create) and
 * `/ordenes/facturacion/rangos/:rangeId` (edit while unused) share this
 * one screen (`design.md`'s AD-15). There is no single-range read
 * endpoint, so edit mode finds the range inside `GET
 * /invoicing/settings`'s own `ranges` list -- the same data the
 * settings screen that linked here already fetched.
 */
export function CaiRangePage() {
  const { rangeId } = useParams<{ rangeId?: string }>();
  const isEdit = rangeId !== undefined;
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();
  const settings = useInvoicingSettings();
  const [newRangeId] = useState(() => crypto.randomUUID());
  const createRange = useCreateCaiRange();
  const updateRange = useUpdateCaiRange(rangeId ?? "");

  if (settings.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const existing = isEdit ? settings.data?.ranges.find((range) => range.id === rangeId) ?? null : null;

  if (isEdit && !existing) {
    return (
      <div className="flex flex-col gap-4">
        <Alert variant="error">{getInvoicingErrorMessage("cai_range_not_found")}</Alert>
        <LinkButton to="/ordenes/facturacion" variant="secondary">
          {invoicingCopy.settings.backToSettings}
        </LinkButton>
      </div>
    );
  }

  function handleSubmit(values: CaiRangeFormSubmitValues) {
    const fields = {
      document_type: values.documentType,
      cai: values.cai,
      range_start: values.rangeStart,
      range_end: values.rangeEnd,
      issue_deadline: values.issueDeadline,
    };
    if (isEdit) {
      updateRange.mutate(fields, { onSuccess: () => navigate("/ordenes/facturacion") });
      return;
    }
    createRange.mutate({ id: newRangeId, ...fields }, { onSuccess: () => navigate("/ordenes/facturacion") });
  }

  const mutation = isEdit ? updateRange : createRange;
  const errorMessage = mutation.error instanceof ApiError ? getInvoicingErrorMessage(mutation.error.code) : undefined;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-bold text-brand-primary">
        {isEdit ? invoicingCopy.settings.rangeForm.editTitle : invoicingCopy.settings.rangeForm.createTitle}
      </h1>
      <CaiRangeForm
        initialValues={
          existing
            ? {
                documentType: existing.document_type as DocumentType,
                cai: existing.cai,
                rangeStart: String(existing.range_start),
                rangeEnd: String(existing.range_end),
                issueDeadline: existing.issue_deadline,
              }
            : undefined
        }
        inUse={existing?.in_use ?? false}
        onSubmit={handleSubmit}
        pending={mutation.isPending}
        errorMessage={errorMessage}
        offline={isOffline}
      />
      <LinkButton to="/ordenes/facturacion" variant="secondary">
        {invoicingCopy.settings.backToSettings}
      </LinkButton>
    </div>
  );
}
