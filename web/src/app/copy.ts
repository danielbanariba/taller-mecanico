/**
 * All Spanish user-facing strings for the app shell (the bottom nav and
 * the header it renders above every protected screen) live here, in one
 * module, mirroring every feature's own `copy.ts`.
 */
export const appCopy = {
  nav: {
    label: "Navegación principal",
    inventario: "Inventario",
    clientes: "Clientes",
    ordenes: "Órdenes",
  },
  logout: {
    submit: "Cerrar sesión",
  },
  more: {
    trigger: "Más",
    title: "Más opciones",
    cashSummary: "Caja del día",
    exportAction: "Exportar todo",
    exportPending: "Exportando...",
    exportOfflineDisabled: "Conéctese a internet para exportar los datos.",
  },
  error: {
    title: "Algo salió mal",
    message: "Ocurrió un error inesperado. Intente recargar la página.",
    reload: "Recargar",
  },
} as const;

/**
 * Maps an API error `code` (the `detail` string) or a client-side code
 * raised by `exportData.ts` to a Spanish message, mirroring every
 * feature's own `copy.ts` convention.
 */
const ERROR_MESSAGES: Record<string, string> = {
  not_authenticated: "Debe iniciar sesión para continuar.",
  network_error: "No se pudo conectar. Verifique su conexión e intente de nuevo.",
  export_failed: "No se pudo generar el archivo. Intente de nuevo.",
};

const GENERIC_ERROR_MESSAGE = "Ocurrió un error. Intente de nuevo.";

export function getAppErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] ?? GENERIC_ERROR_MESSAGE;
}
