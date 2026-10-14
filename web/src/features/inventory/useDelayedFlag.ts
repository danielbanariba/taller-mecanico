import { useEffect, useState } from "react";

/**
 * True only once `active` has stayed continuously true for at least
 * `delayMs`; flips back to false the instant `active` turns false. Lets a
 * UI stay silent for a transient condition that resolves quickly (a flush
 * pass, an outbox drain) and only surface it once it has genuinely
 * lingered long enough to be worth telling the user about.
 *
 * Both `setDelayed` calls happen outside the effect's synchronous setup
 * body -- `true` from the timer's own (async) callback, `false` from the
 * cleanup that runs when `active` stops being true -- so this never trips
 * `react-hooks/set-state-in-effect`'s rule against deriving state
 * synchronously inside an effect.
 */
export function useDelayedFlag(active: boolean, delayMs: number): boolean {
  const [delayed, setDelayed] = useState(false);

  useEffect(() => {
    if (!active) {
      return;
    }

    const timer = setTimeout(() => setDelayed(true), delayMs);
    return () => {
      clearTimeout(timer);
      setDelayed(false);
    };
  }, [active, delayMs]);

  return delayed;
}
