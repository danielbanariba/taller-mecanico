import type { MovementOut } from "./api";

/**
 * All Spanish user-facing strings for the inventory feature live here, in
 * one module, so they are easy to review and later translate.
 */
export const inventoryCopy = {
  list: {
    greeting: "Taller",
    searchLabel: "Buscar repuesto",
    searchPlaceholder: "Nombre del repuesto",
    filterGroupLabel: "Filtros de inventario",
    filterAll: "Todos",
    filterLow: "Por acabarse",
    filterNeedsReview: "Revisar",
    addItem: "Agregar repuesto",
    emptyTitle: "Todavía no hay repuestos",
    emptyBody: "Agregue su primer repuesto para empezar a controlar el inventario.",
    emptyFilteredTitle: "No se encontraron repuestos",
    emptyFilteredBody: "Pruebe con otra búsqueda o quite el filtro.",
    decrementLabel: (name: string) => `Quitar una unidad de ${name}`,
    incrementLabel: (name: string) => `Agregar una unidad de ${name}`,
  },
  badges: {
    lowStock: "Por acabarse",
    needsReview: "Revisar",
  },
  create: {
    title: "Agregar repuesto",
    nameLabel: "Nombre",
    nameRequired: "El nombre es obligatorio.",
    initialStockLabel: "Cantidad actual",
    unitLabel: "Unidad",
    categoryLabel: "Categoría",
    minStockLabel: "Mínimo para avisar",
    minStockHelper: "Avisamos cuando el inventario llegue a esta cantidad o menos.",
    priceLabel: "Precio de venta (Lempiras)",
    pricePlaceholder: "0.00",
    priceInvalid: "Ingrese un precio válido, por ejemplo 125.50.",
    notesLabel: "Notas",
    submit: "Guardar repuesto",
    submitPending: "Guardando...",
  },
  edit: {
    title: "Editar repuesto",
    submit: "Guardar cambios",
    submitPending: "Guardando...",
  },
  detail: {
    stockLabel: "En inventario",
    countAction: "Contar",
    countDialogTitle: "Contar repuesto",
    countLabel: "Cantidad contada",
    countSubmit: "Guardar conteo",
    countCancel: "Cancelar",
    editAction: "Editar",
    archiveAction: "Archivar",
    archiveConfirmTitle: "Archivar repuesto",
    archiveConfirmBody: "Ya no aparecerá en la lista de inventario. Esta acción no se puede deshacer desde aquí.",
    archiveConfirmSubmit: "Archivar",
    archiveConfirmCancel: "Cancelar",
    historyTitle: "Historial de movimientos",
    historyEmpty: "Todavía no hay movimientos.",
  },
  units: ["unidad", "galón", "litro", "juego", "par", "caja"],
  offline: {
    offlineMessage: "Sin conexión. Los cambios se guardan en el teléfono.",
    syncingMessage: "Sincronizando...",
    pendingCount: (count: number) => `${count} cambio${count === 1 ? "" : "s"} por enviar`,
    createDisabled: "Conéctese a internet para agregar repuestos.",
    editDisabled: "Conéctese a internet para editar repuestos.",
  },
} as const;

/** Builds the Spanish label for one movement row, e.g. "Entrada +3". */
export function movementLabel(movement: Pick<MovementOut, "kind" | "quantity" | "delta">): string {
  if (movement.kind === "in") {
    return `Entrada +${movement.quantity}`;
  }
  if (movement.kind === "out") {
    return `Salida −${movement.quantity}`;
  }
  const deltaLabel = movement.delta >= 0 ? `+${movement.delta}` : `−${Math.abs(movement.delta)}`;
  return `Conteo: ${movement.quantity} (${deltaLabel})`;
}

/**
 * Maps an API error `code` (the `detail` string) to a Spanish message the
 * user can act on. Unknown codes (including the array `detail` FastAPI
 * sends for unhandled 422s) fall back to a generic message.
 */
const ERROR_MESSAGES: Record<string, string> = {
  item_name_taken: "Ya existe un repuesto con ese nombre.",
  item_id_conflict: "No se pudo guardar el repuesto. Intente de nuevo.",
  item_not_found: "No se encontró el repuesto.",
  movement_id_conflict: "No se pudo registrar el movimiento. Intente de nuevo.",
  stock_out_of_range: "La cantidad ingresada no es válida.",
  not_authenticated: "Debe iniciar sesión para continuar.",
  network_error: "No se pudo conectar. Verifique su conexión e intente de nuevo.",
};

const GENERIC_ERROR_MESSAGE = "Ocurrió un error. Intente de nuevo.";

export function getInventoryErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] ?? GENERIC_ERROR_MESSAGE;
}
