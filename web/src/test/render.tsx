import type { ReactElement } from "react";
import { render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

/**
 * Renders `ui` under a fresh `QueryClient` (no retries, so a mocked 401/409
 * fails the test instantly instead of after a backoff delay). Wrap `ui` in
 * its own `MemoryRouter`/`Routes` when the component under test navigates.
 */
export function renderWithQueryClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}
