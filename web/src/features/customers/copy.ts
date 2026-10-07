/**
 * All Spanish user-facing strings for the customers feature live here, in
 * one module, so they are easy to review and later translate. This folder
 * also owns vehicles from Slice 5 on, and their strings join this same
 * file then -- the two entities share one error-code map (see below), so
 * keeping their copy together avoids a second map drifting from this one.
 */
export const customersCopy = {
  list: {
    searchLabel: "Buscar cliente",
    searchPlaceholder: "Nombre o teléfono",
    addCustomer: "Agregar cliente",
    emptyTitle: "Todavía no hay clientes",
    emptyBody: "Agregue su primer cliente para empezar a registrar sus vehículos y órdenes.",
    emptyFilteredTitle: "No se encontraron clientes",
    emptyFilteredBody: "Pruebe con otra búsqueda.",
    mobileBadge: "móvil",
    landlineBadge: "fijo",
  },
  form: {
    nameLabel: "Nombre completo",
    nameRequired: "El nombre es obligatorio.",
    nameTooLong: "El nombre no puede tener más de 120 caracteres.",
    phoneLabel: "Teléfono",
    phoneHelper: "Opcional. Por ejemplo 9876-5432.",
    notesLabel: "Notas",
  },
  create: {
    title: "Agregar cliente",
    submit: "Guardar cliente",
    submitPending: "Guardando...",
  },
  edit: {
    title: "Editar cliente",
    submit: "Guardar cambios",
    submitPending: "Guardando...",
    backToList: "Volver a clientes",
    archiveAction: "Archivar cliente",
    archiveConfirmTitle: "Archivar cliente",
    archiveConfirmBody:
      "El cliente y sus vehículos activos se archivarán. Podrá seguir viéndolos en el historial de órdenes.",
    archiveConfirmCancel: "Cancelar",
    archiveConfirmSubmit: "Archivar",
  },
  offline: {
    createDisabled: "Conéctese a internet para agregar clientes.",
    editDisabled: "Conéctese a internet para editar clientes.",
    archiveDisabled: "Conéctese a internet para archivar clientes.",
  },
};

/**
 * Error-code to Spanish message mapping. Shared by customers and, from
 * Slice 5, vehicles -- both features live in this one folder, so both
 * entities' error codes are mapped together here rather than duplicated.
 * `plate_taken`/`invalid_plate`/`vehicle_*` are added now even though no
 * screen in this slice can trigger them yet, so Slice 5's vehicle form
 * finds a ready mapping instead of falling back to the generic message.
 * Unknown codes (including the array `detail` FastAPI sends for unhandled
 * 422s) fall back to a generic message.
 */
const ERROR_MESSAGES: Record<string, string> = {
  customer_id_conflict: "No se pudo guardar el cliente. Intente de nuevo.",
  customer_not_found: "No se encontró el cliente.",
  invalid_phone: "El teléfono no es válido. Use un número hondureño de 8 dígitos.",
  vehicle_id_conflict: "No se pudo guardar el vehículo. Intente de nuevo.",
  vehicle_not_found: "No se encontró el vehículo.",
  plate_taken: "Ya existe un vehículo activo con esa placa.",
  invalid_plate: "La placa no es válida.",
  not_authenticated: "Debe iniciar sesión para continuar.",
  network_error: "No se pudo conectar. Verifique su conexión e intente de nuevo.",
};

const GENERIC_ERROR_MESSAGE = "Ocurrió un error. Intente de nuevo.";

export function getCustomersErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] ?? GENERIC_ERROR_MESSAGE;
}
