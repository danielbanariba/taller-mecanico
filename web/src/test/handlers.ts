import type { HttpHandler } from "msw";

/**
 * Default handlers shared by every test file. Deliberately empty: each test
 * adds the handlers it needs with `server.use(...)` (see `./server.ts`),
 * which keeps every test's network behavior visible at the call site.
 */
export const handlers: HttpHandler[] = [];
