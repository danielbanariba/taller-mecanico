import { useNavigate } from "react-router";

import { ApiError } from "../../../shared/api/http";
import { useOnlineStatus } from "../../../shared/offline/useOnlineStatus";
import { Alert } from "../../../shared/ui/Alert";
import { Button } from "../../../shared/ui/Button";
import { Spinner } from "../../../shared/ui/Spinner";
import { getInvoicingErrorMessage, invoicingCopy } from "../copy";
import { useInvoicingSettings } from "../hooks";
import { CaiRangeList } from "./CaiRangeList";
import { RangeWarnings } from "./RangeWarnings";
import { ReadinessSummary } from "./ReadinessSummary";
import { SarNotice } from "./SarNotice";

/**
 * Container: the fiscal settings screen (`design.md`'s AD-15), reached
 * from the shell's "Más" menu. Always shows the SAR notice (`fiscal-profile`
 * spec), whether or not a profile exists -- it is the only way to reach
 * the profile form that creates the first one. Reads come from the
 * persisted query cache, so a previously visited settings screen still
 * renders offline; writes (the profile form, range forms) are reached
 * from here but disabled offline themselves.
 */
export function InvoicingSettingsPage() {
  const navigate = useNavigate();
  const isOffline = useOnlineStatus();
  const settings = useInvoicingSettings();

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-3xl font-bold text-brand-primary">{invoicingCopy.settings.title}</h1>

      <SarNotice />

      {settings.isPending ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : settings.error || !settings.data ? (
        <Alert variant="error">
          {getInvoicingErrorMessage(settings.error instanceof ApiError ? settings.error.code : "unknown_error")}
        </Alert>
      ) : (
        <>
          <ReadinessSummary documents={settings.data.documents} />
          <RangeWarnings documents={settings.data.documents} />

          <section className="flex flex-col gap-3">
            <h2 className="text-lg font-bold text-brand-primary">{invoicingCopy.settings.profileTitle}</h2>
            {settings.data.profile ? (
              <div className="flex flex-col gap-1 rounded-xl border border-brand-border p-3">
                <p className="font-semibold text-brand-foreground">{settings.data.profile.legal_name}</p>
                <p className="text-sm text-brand-muted-foreground">RTN: {settings.data.profile.rtn}</p>
              </div>
            ) : (
              <p className="text-base text-brand-muted-foreground">{invoicingCopy.settings.noProfile}</p>
            )}
            {isOffline ? <Alert variant="info">{invoicingCopy.offline.profileWriteDisabled}</Alert> : null}
            <Button
              variant="secondary"
              onClick={() => navigate("/ordenes/facturacion/datos")}
              disabled={isOffline}
            >
              {settings.data.profile
                ? invoicingCopy.settings.editProfileAction
                : invoicingCopy.settings.configureAction}
            </Button>
          </section>

          <section className="flex flex-col gap-3">
            <h2 className="text-lg font-bold text-brand-primary">{invoicingCopy.settings.rangesTitle}</h2>
            <CaiRangeList ranges={settings.data.ranges} />
            {isOffline ? <Alert variant="info">{invoicingCopy.offline.rangeWriteDisabled}</Alert> : null}
            <Button
              variant="secondary"
              onClick={() => navigate("/ordenes/facturacion/rangos/nuevo")}
              disabled={isOffline}
            >
              {invoicingCopy.settings.registerRangeAction}
            </Button>
          </section>
        </>
      )}
    </div>
  );
}
