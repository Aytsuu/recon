/**
 * API error utility.
 * Handles alerting or logging API errors consistently across the application.
 */
export function alertApiError(error: unknown): void {
  const message = error instanceof Error ? error.message : String(error);

  if (typeof window !== 'undefined') {
    // In browser, log to console. If desired, can trigger a toast notification or alert
    console.error('API Error:', message);
  } else {
    // On server / SSR, log error context
    console.error('Server API Error:', message);
  }
}
