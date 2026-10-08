import { useNavigate } from "react-router";

import { ApiError } from "../../../shared/api/http";
import { useOnlineStatus } from "../../../shared/offline/useOnlineStatus";
import { LinkButton } from "../../../shared/ui/LinkButton";
import { Spinner } from "../../../shared/ui/Spinner";
import { getInvoicingErrorMessage, invoicingCopy } from "../copy";
import { useInvoicingSettings, useSaveProfile } from "../hooks";
import { FiscalProfileForm, type FiscalProfileFormValues } from "./FiscalProfileForm";

/**
 * Container: `/ordenes/facturacion/datos` (`design.md`'s AD-15). Prefills
 * from the current profile when one exists -- saving is otherwise an
 * idempotent upsert either way (AD-3), so this screen needs no separate
 * create/edit mode.
 */
export function FiscalProfilePage() {
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();
  const settings = useInvoicingSettings();
  const saveProfile = useSaveProfile();

  if (settings.isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const profile = settings.data?.profile ?? null;

  function handleSubmit(values: FiscalProfileFormValues) {
    saveProfile.mutate(
      {
        rtn: values.rtn,
        legal_name: values.legalName,
        trade_name: values.tradeName,
        address: values.address,
        phone: values.phone,
        email: values.email,
        establishment_code: values.establishmentCode,
        emission_point_code: values.emissionPointCode,
      },
      { onSuccess: () => navigate("/ordenes/facturacion") },
    );
  }

  const errorMessage =
    saveProfile.error instanceof ApiError ? getInvoicingErrorMessage(saveProfile.error.code) : undefined;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-bold text-brand-primary">{invoicingCopy.settings.profileForm.title}</h1>
      <FiscalProfileForm
        initialValues={
          profile
            ? {
                rtn: profile.rtn,
                legalName: profile.legal_name,
                tradeName: profile.trade_name,
                address: profile.address,
                phone: profile.phone,
                email: profile.email,
                establishmentCode: profile.establishment_code,
                emissionPointCode: profile.emission_point_code,
              }
            : undefined
        }
        onSubmit={handleSubmit}
        pending={saveProfile.isPending}
        errorMessage={errorMessage}
        offline={isOffline}
      />
      <LinkButton to="/ordenes/facturacion" variant="secondary">
        {invoicingCopy.settings.backToSettings}
      </LinkButton>
    </div>
  );
}
