import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";

import packageJson from "./package.json" with { type: "json" };

export default defineConfig({
  define: {
    // Ties the persisted query cache's buster (see src/app/providers.tsx)
    // to the app version, so a new release never hydrates an old,
    // incompatible IndexedDB cache shape.
    __APP_VERSION__: JSON.stringify(packageJson.version),
  },
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
      workbox: {
        navigateFallbackDenylist: [/^\/api\//],
        // `/api/*` is served by the same origin but must never be answered
        // from the service worker's cache: the persisted TanStack Query
        // cache (src/shared/offline/idbPersister.ts) is the offline data
        // source, so API responses stay network-only (NetworkOnly never
        // caches), and a stale cached API response can never win a race
        // against the real backend.
        //
        // A match callback on the pathname, not a RegExp: Workbox tests a
        // RegExp against the full URL (`https://host/api/...`), so
        // `/^\/api\//` never matched any request. Same-origin only, since
        // that is the only origin the session cookie and the API live on.
        runtimeCaching: [
          {
            urlPattern: ({ url, sameOrigin }) => sameOrigin && url.pathname.startsWith("/api/"),
            handler: "NetworkOnly",
          },
        ],
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
