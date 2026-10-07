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
} as const;
