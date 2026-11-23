# Prefer an exported consumer shell with a hosted API for mobile

Accepted for groundwork.

A fully static export starts offline but cannot perform server rendering or secure remote writes alone. A hosted WebView shell preserves SSR and conventional cookies but needs connectivity to start. Choose the hybrid for STEP-13b: bundle exported assets and call a hosted API for protected operations. Keep the browser app deployable on the web. Before packaging, move server-only page inputs such as searchParams to client navigation and supply build-time display settings. Test origin allowlists, cookie behavior, offline states and session revocation on devices. Keep staff routes outside the export.
