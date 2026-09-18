/**
 * API base configuration.
 *
 * Resolution order:
 *   1. `window.__API_BASE__` — injected at runtime (e.g. by Vercel via an env var
 *      or an inline <script> in index.html), so no code edit is required per env.
 *   2. Same-origin `/api` when served over HTTP(S) (Vercel serves the site and
 *      the Flask serverless function from the same domain).
 *   3. Local dev backend on localhost:5000 (file:// usage).
 *
 * To point the deployed site at a hosted API, set the runtime global, for example:
 *   <script>window.__API_BASE__ = 'https://your-api.onrender.com/api';</script>
 */
export function getApiBase() {
    const injected = typeof window !== 'undefined' &&
        window.__API_BASE__;
    if (injected && injected !== '') {
        return injected.replace(/\/$/, '');
    }
    if (typeof window !== 'undefined' && window.location.protocol.startsWith('http')) {
        return '/api';
    }
    return 'http://localhost:5000/api';
}
//# sourceMappingURL=config.js.map