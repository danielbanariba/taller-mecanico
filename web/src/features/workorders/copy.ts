import type { LineKind, WorkOrderStatus } from "./api";

/** All Spanish user-facing strings for the work-orders feature live here, in one module. */
export const workOrdersCopy = {
  status: {
    quote: "Cotización",
    approved: "Aprobada",
    in_progress: "En proceso",
    completed: "Terminada",
    delivered: "Entregada",
    cancelled: "Cancelada",
  },
  lineKind: {
    labor: "Mano de obra",
    inventory_part: "Repuesto de inventario",
    external_part: "Repuesto externo",
  },
  list: {
    title: "Órdenes",
    newOrder: "Nueva orden",
    tabOpen: "Abiertas",
    tabHistory: "Historial",
    loadMore: "Ver más",
    emptyTitle: "Todavía no hay órdenes",
    emptyBody: "Las órdenes que registre aparecerán aquí.",
  },
  detail: {
    backToList: "Volver a órdenes",
    orderTitle: (number: number) => `Orden #${number}`,
    complaintLabel: "Motivo",
    linesTitle: "Líneas",
    linesEmpty: "Esta orden todavía no tiene líneas.",
    totalLabel: "Total",
  },
  newOrder: {
    title: "Nueva orden",
    customerSearchLabel: "Buscar cliente",
    customerSearchPlaceholder: "Nombre o teléfono",
    changeCustomer: "Cambiar cliente",
    changeVehicle: "Cambiar vehículo",
    submit: "Crear orden",
    submitPending: "Creando...",
  },
  offline: {
    createOrderDisabled: "Conéctese a internet para crear órdenes.",
    lineEditDisabled: "Conéctese a internet para editar líneas.",
    statusChangeDisabled: "Conéctese a internet para cambiar el estado de la orden.",
  },
  statusActions: {
    // `quote` is never a reachable target (`TRANSITIONS` has no edge into
    // it, per `design.md`'s AD-7), so this label is never shown; it is
    // declared anyway to keep the map total over `WorkOrderStatus`.
    quote: "Volver a cotización",
    approved: "Aprobar",
    in_progress: "Iniciar trabajo",
    completed: "Marcar como terminada",
    delivered: "Marcar como entregada",
    cancelled: "Cancelar orden",
  },
  cancelConfirm: {
    title: "Cancelar orden",
    body: "Una orden cancelada no se puede volver a abrir.",
    bodyInProgress: "Los repuestos que ya consumió esta orden se devolverán al inventario.",
    keep: "No cancelar",
    confirm: "Sí, cancelar orden",
  },
  share: {
    shareButton: "Compartir por WhatsApp",
    dialogTitle: "Compartir por WhatsApp",
    photosLabel: "Fotos (opcional)",
    photosSelected: (count: number) =>
      `${count} foto${count === 1 ? "" : "s"} seleccionada${count === 1 ? "" : "s"}`,
    send: "Enviar",
    cancel: "Cancelar",
    greeting: (workshopName: string) => `Hola, le escribimos desde ${workshopName}.`,
    orderLine: (number: number, vehicleLabel: string) => `Orden #${number} · ${vehicleLabel}`,
    linesHeading: "Detalle:",
    lineItem: (description: string, quantity: number, unitPrice: string) =>
      `• ${description} (${quantity} x ${unitPrice})`,
    totalLine: (total: string) => `Total: ${total}`,
  },
  lineEditor: {
    addLine: "Agregar línea",
    editLine: "Editar",
    removeLine: "Eliminar",
    addLineTitle: "Agregar línea",
    editLineTitle: "Editar línea",
    kindLabel: "Tipo de línea",
    itemLabel: "Repuesto",
    pickItem: "Seleccionar repuesto",
    changeItem: "Cambiar repuesto",
    itemRequired: "Seleccione un repuesto.",
    descriptionLabel: "Descripción",
    descriptionRequired: "La descripción es obligatoria.",
    quantityLabel: "Cantidad",
    quantityInvalid: "La cantidad debe ser un número entre 1 y 10,000.",
    priceLabel: "Precio unitario",
    priceInvalid: "El precio no es válido.",
    subtotalLabel: "Subtotal",
    cancel: "Cancelar",
    save: "Guardar línea",
    savePending: "Guardando...",
  },
  itemPicker: {
    searchLabel: "Buscar repuesto",
    searchPlaceholder: "Nombre o categoría",
    emptyTitle: "No se encontraron repuestos",
    changeItem: "Cambiar repuesto",
    back: "Cancelar",
  },
} as const;

export function statusLabel(status: WorkOrderStatus): string {
  return workOrdersCopy.status[status];
}

export function lineKindLabel(kind: LineKind): string {
  return workOrdersCopy.lineKind[kind];
}

/** The Spanish verb for triggering a transition to `status` (e.g. `in_progress` -> "Iniciar trabajo"), never the status's own name (`statusLabel`). */
export function statusActionLabel(status: WorkOrderStatus): string {
  return workOrdersCopy.statusActions[status];
}

/**
 * Maps an API error `code` (the `detail` string) to a Spanish message the
 * user can act on. Unknown codes (including the array `detail` FastAPI
 * sends for unhandled 422s) fall back to a generic message.
 */
const ERROR_MESSAGES: Record<string, string> = {
  work_order_not_found: "No se encontró la orden.",
  work_order_id_conflict: "No se pudo crear la orden. Intente de nuevo.",
  work_order_create_failed: "No se pudo crear la orden. Intente de nuevo.",
  vehicle_not_found: "No se encontró el vehículo.",
  item_not_found: "No se encontró el repuesto.",
  work_order_line_id_conflict: "No se pudo guardar la línea. Intente de nuevo.",
  work_order_line_not_found: "No se encontró la línea.",
  work_order_locked: "Esta orden ya no se puede editar.",
  invalid_status_transition: "No se puede cambiar la orden a ese estado.",
  movement_id_conflict: "No se pudo registrar el movimiento. Intente de nuevo.",
  stock_out_of_range: "La cantidad está fuera de rango.",
  not_authenticated: "Debe iniciar sesión para continuar.",
  network_error: "No se pudo conectar. Verifique su conexión e intente de nuevo.",
};

const GENERIC_ERROR_MESSAGE = "Ocurrió un error. Intente de nuevo.";

export function getWorkOrdersErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] ?? GENERIC_ERROR_MESSAGE;
}
