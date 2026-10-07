/// <reference types="vite/client" />

/** Injected by `vite.config.ts` from `package.json`'s version plus a
 * per-build id (`resolveBuildId`: the git short SHA, or a timestamp when
 * git is unavailable). Ties the persisted query cache's `buster` to every
 * build, not only a version bump, so a deploy that changes a response
 * shape never hydrates from an older, incompatible cache. */
declare const __APP_VERSION__: string;

/** Set only when building the public test deployment; see `getDemoAccount`. */
interface ImportMetaEnv {
  readonly VITE_DEMO_PHONE?: string;
  readonly VITE_DEMO_PASSWORD?: string;
}
