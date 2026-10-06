/**
 * All Spanish user-facing strings for the auth feature live here, in one
 * module, so they are easy to review and later translate.
 */

export const authCopy = {
  login: {
    title: "Iniciar sesión",
    phoneLabel: "Teléfono",
    phonePlaceholder: "9999-9999",
    passwordLabel: "Contraseña",
    submit: "Iniciar sesión",
    submitPending: "Ingresando...",
    goToRegister: "¿No tiene cuenta? Regístrese",
  },
  register: {
    title: "Crear cuenta",
    workshopNameLabel: "Nombre del taller",
    ownerNameLabel: "Nombre del propietario",
    phoneLabel: "Teléfono",
    phonePlaceholder: "9999-9999",
    passwordLabel: "Contraseña",
    passwordHelper: "Mínimo 8 caracteres.",
    passwordTooShort: "La contraseña debe tener al menos 8 caracteres.",
    submit: "Crear cuenta",
    submitPending: "Creando cuenta...",
    goToLogin: "¿Ya tiene cuenta? Inicie sesión",
  },
  logout: {
    submit: "Cerrar sesión",
  },
} as const;

/**
 * Maps an API error `code` (the `detail` string) to a Spanish message the
 * user can act on. Unknown codes (including the array `detail` FastAPI
 * sends for unhandled 422s) fall back to a generic message.
 */
const ERROR_MESSAGES: Record<string, string> = {
  phone_already_registered: "Ese número de teléfono ya está registrado.",
  invalid_credentials: "Teléfono o contraseña incorrectos.",
  not_authenticated: "Debe iniciar sesión para continuar.",
  network_error: "No se pudo conectar. Verifique su conexión e intente de nuevo.",
};

const GENERIC_ERROR_MESSAGE = "Ocurrió un error. Intente de nuevo.";

export function getAuthErrorMessage(code: string): string {
  return ERROR_MESSAGES[code] ?? GENERIC_ERROR_MESSAGE;
}
