# Use PostgreSQL-backed jobs

Accepted for groundwork.

Today and report jobs need leases, retries and deduplication. A Postgres queue port can share operational infrastructure. Revisit a separate broker only if measured contention justifies it.
