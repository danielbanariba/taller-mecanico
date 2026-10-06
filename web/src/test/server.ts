import { setupServer } from "msw/node";

import { handlers } from "./handlers";

/**
 * Shared MSW server for every test. Add a test-specific handler with
 * `server.use(http.get("/api/...", () => HttpResponse.json({...})))` inside
 * the test; `setup.ts` resets handlers after each test automatically.
 */
export const server = setupServer(...handlers);
