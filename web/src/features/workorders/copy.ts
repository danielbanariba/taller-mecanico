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
} as const;

export function statusLabel(status: WorkOrderStatus): string {
  return workOrdersCopy.status[status];
}

export function lineKindLabel(kind: LineKind): string {
  return workOrdersCopy.lineKind[kind];
}

/**
 * Maps an API error `code` (the `detail` string) to a Spanish message the
 * user can act on. Unknown codes (including the array `detail` FastAPI
 * sends for unhandled 422s) fall back to a generic message.
 */
const ERROR_MESSAGES: Record<string, string> = {
  work_order_not_found: "No se encontró la orden.",
  not_authenticated: "Debe iniciar sesión para continuar.",
  network_error: "No se pudo conectar. Verifique su conexión e intente de nuevo.",
};

const GENERIC_ERROR_MESSAGE = "Ocurrió un error. Intente de nuevo.";

export function getWorkOrdersErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] ?? GENERIC_ERROR_MESSAGE;
}
