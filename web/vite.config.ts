/// <reference types="vitest/importMeta" />
import { execSync } from "node:child_process";

import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";

import packageJson from "./package.json" with { type: "json" };

// Public hostnames `vite preview` may answer for (comma-separated), e.g. the
// test deployment in deploy/demo/. Vite rejects any request whose Host
// header is not listed, so a tunnel forwarding the public hostname would get
// a 403 otherwise. Empty by default: local preview needs no extra hosts.
const previewAllowedHosts = (process.env.TALLER_PREVIEW_ALLOWED_HOSTS ?? "")
  .split(",")
  .map((host) => host.trim())
  .filter((host) => host.length > 0);

/**
 * A per-build identifier appended to the app version for the persisted
 * query cache's buster (see `src/app/providers.tsx`). `package.json`'s
 * `version` alone stayed `0.1.0` across every phase of this change, so a
 * deploy that changed a response shape (phase 3 added `payments` to a
 * work order) never busted a browser's previously persisted,
 * now-incompatible IndexedDB cache -- the app crashed reading a field the
 * cached shape never had. Falls back to a timestamp when `git` is
 * unavailable (e.g. a build context with no `.git` checkout), so the
 * buster still changes on every build instead of crashing the build.
 *
 * Exported with injectable dependencies so the fallback path is unit
 * testable without a real git checkout (see the in-source test below).
 */
export function resolveBuildId(
  readGitShortSha: () => string = () => execSync("git rev-parse --short HEAD").toString(),
  currentTimestamp: () => number = () => Date.now(),
): string {
  try {
    const sha = readGitShortSha().trim();
    if (sha) {
      return sha;
    }
  } catch {
    // No git checkout, or the `git` binary is unavailable -- fall through
    // to the timestamp fallback below.
  }
  return String(currentTimestamp());
}

export default defineConfig({
  define: {
    // See `resolveBuildId` above: the buster is the app version plus a
    // per-build id, so every build -- not just every version bump -- is
    // a cache bust.
    __APP_VERSION__: JSON.stringify(`${packageJson.version}+${resolveBuildId()}`),
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
  preview: {
    allowedHosts: previewAllowedHosts,
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
    // Lets `resolveBuildId`'s in-source test below run under `npm test`;
    // `vite.config.ts` is never part of the shipped app bundle (the web
    // app never imports it), so `import.meta.vitest` below is always
    // `undefined` outside the test runner and this block is a no-op for
    // `vite dev`/`vite build`.
    includeSource: ["vite.config.ts"],
  },
});

if (import.meta.vitest) {
  const { describe, it, expect } = import.meta.vitest;

  describe("resolveBuildId", () => {
    it("returns the trimmed git short SHA when git succeeds", () => {
      expect(resolveBuildId(() => "abc1234\n")).toBe("abc1234");
    });

    it("falls back to a timestamp when git fails", () => {
      const failingGit = () => {
        throw new Error("not a git repository");
      };

      expect(resolveBuildId(failingGit, () => 1700000000000)).toBe("1700000000000");
    });

    it("falls back to a timestamp when git succeeds but prints nothing", () => {
      expect(resolveBuildId(() => "   ", () => 1700000000000)).toBe("1700000000000");
    });
  });
}
