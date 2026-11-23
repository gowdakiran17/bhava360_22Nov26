# Use Next.js route handlers for the shared API

Accepted for groundwork.

A separate server entry point serves both clients and keeps database, credentials and authorization logic out of browser bundles. A small health route exercises the production runtime before feature endpoints arrive.
