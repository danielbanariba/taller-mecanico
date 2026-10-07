import { useState } from "react";

import { Button } from "../../../shared/ui/Button";
import { Dialog } from "../../../shared/ui/Dialog";
import { workOrdersCopy } from "../copy";

export interface ShareSheetProps {
  /** The prefilled `wa.me` link, already built by `ShareWhatsAppButton`. */
  url: string;
  /** The same Spanish summary the `url` carries, reused for the clipboard copy and the Web Share payload. */
  summary: string;
  onClose: () => void;
}

/**
 * Lazy-loaded photo-attach step, mounted only once `ShareWhatsAppButton`
 * confirms the browser supports file sharing and the mechanic opens it
 * (`design.md`'s AD-18). Picked `File` objects live only in this
 * component's own state and are discarded the moment it unmounts --
 * never uploaded to the API, never written to any client-side storage
 * (the `whatsapp-sharing` spec's "Photos Are Never Uploaded To Or
 * Stored By The App").
 */
export function ShareSheet({ url, summary, onClose }: ShareSheetProps) {
  const [files, setFiles] = useState<File[]>([]);

  function openWhatsAppLink() {
    window.open(url, "_blank", "noopener,noreferrer");
  }

  async function handleSend() {
    if (files.length === 0) {
      openWhatsAppLink();
      onClose();
      return;
    }

    try {
      // Best-effort safeguard per AD-18: some WhatsApp builds drop `text`
      // when files are attached, so the user can paste the summary
      // manually. A clipboard failure must never block sharing.
      await navigator.clipboard?.writeText(summary);
    } catch {
      // Intentionally ignored -- see comment above.
    }

    try {
      await navigator.share({ files, text: summary });
      onClose();
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        // The mechanic cancelled the native share sheet; leave this
        // dialog open so they can retry or pick different photos.
        return;
      }
      openWhatsAppLink();
      onClose();
    }
  }

  return (
    <Dialog open title={workOrdersCopy.share.dialogTitle} onClose={onClose}>
      <div className="flex flex-col gap-4">
        <label className="flex flex-col gap-1.5">
          <span className="text-base font-medium text-brand-foreground">{workOrdersCopy.share.photosLabel}</span>
          <input
            type="file"
            accept="image/*"
            capture="environment"
            multiple
            onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
          />
        </label>
        {files.length > 0 ? (
          <p className="text-sm text-brand-muted-foreground">{workOrdersCopy.share.photosSelected(files.length)}</p>
        ) : null}
        <div className="flex gap-3">
          <Button variant="secondary" onClick={onClose}>
            {workOrdersCopy.share.cancel}
          </Button>
          <Button onClick={handleSend}>{workOrdersCopy.share.send}</Button>
        </div>
      </div>
    </Dialog>
  );
}
