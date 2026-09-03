/**
 * API base configuration.
 *
 * Resolution order:
 *   1. `window.__API_BASE__` — injected at runtime (e.g. by Vercel via an env var
 *      or an inline <script> in index.html), so no code edit is required per env.
 *   2. Falls back to the local dev backend on localhost:5000.
 *
 * To point the deployed site at a hosted API, set the runtime global, for example:
 *   <script>window.__API_BASE__ = 'https://your-api.onrender.com/api';</script>
 * or via Vercel's build-time env, inject it into index.html before the bundle.
 */

export function getApiBase(): string {
  const injected =
    typeof window !== 'undefined' &&
    (window as unknown as { __API_BASE__?: string }).__API_BASE__;
  return injected && injected !== '' ? injected : 'http://localhost:5000/api';
}
