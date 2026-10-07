import { customersCopy } from "./copy";
import type { VehicleOut } from "./api";

export interface VehicleListProps {
  vehicles: VehicleOut[];
  onOpen: (vehicle: VehicleOut) => void;
}

/** Presentational: a customer's vehicle list, with an empty state. */
export function VehicleList({ vehicles, onOpen }: VehicleListProps) {
  if (vehicles.length === 0) {
    return (
      <div className="flex flex-col items-center gap-1 rounded-2xl border border-dashed border-brand-border px-4 py-10 text-center">
        <p className="text-lg font-semibold text-brand-foreground">{customersCopy.vehicles.emptyTitle}</p>
        <p className="text-base text-brand-muted-foreground">{customersCopy.vehicles.emptyBody}</p>
      </div>
    );
  }

  return (
    <ul className="flex flex-col gap-2">
      {vehicles.map((vehicle) => (
        <li key={vehicle.id}>
          <button
            type="button"
            onClick={() => onOpen(vehicle)}
            className="flex w-full flex-col items-start gap-0.5 rounded-2xl border border-brand-border bg-brand-card px-4 py-3 text-left"
          >
            <span className="text-lg font-semibold text-brand-foreground">
              {[vehicle.make, vehicle.model].filter(Boolean).join(" ")}
            </span>
            <span className="text-sm text-brand-muted-foreground">
              {customersCopy.vehicles.typeLabels[vehicle.vehicle_type]}
              {vehicle.plate ? ` · ${vehicle.plate}` : ""}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
