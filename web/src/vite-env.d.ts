/// <reference types="vite/client" />

/** Injected by `vite.config.ts` from `package.json`'s version; ties the
 * persisted query cache's `buster` to the deployed app version so a new
 * release never hydrates from an older, incompatible shape. */
declare const __APP_VERSION__: string;
