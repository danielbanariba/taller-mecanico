export type ButtonVariant = "primary" | "secondary" | "destructive";

/** Shared by `Button` and `LinkButton` so a navigation link styled as a button stays visually identical to one. */
export const BUTTON_VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-brand-primary text-brand-on-primary active:bg-brand-secondary",
  secondary:
    "bg-brand-card text-brand-primary border border-brand-border active:bg-brand-muted",
  destructive: "bg-brand-destructive text-brand-on-destructive active:bg-red-700",
};
