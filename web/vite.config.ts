import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icons/icon.svg", "icons/apple-touch-icon-180x180.png", "favicon.ico"],
      manifest: {
        name: "Inventario Taller",
        short_name: "Taller",
        description: "Control de inventario de repuestos para talleres mecánicos",
        lang: "es",
        display: "standalone",
        start_url: "/",
        scope: "/",
        theme_color: "#0f172a",
        background_color: "#f8fafc",
        icons: [
          {
            src: "icons/pwa-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "icons/pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
          {
            src: "icons/maskable-icon-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
      // T6 wires offline API runtime caching; keep this scaffold to app-shell only.
      workbox: {
        navigateFallbackDenylist: [/^\/api\//],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8010",
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    environmentOptions: {
      jsdom: {
        // Matches the dev proxy origin; MSW matches handler paths against
        // any origin anyway, but a stable base avoids relative-URL surprises.
        url: "http://localhost:5173/",
      },
    },
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: true,
  },
});
