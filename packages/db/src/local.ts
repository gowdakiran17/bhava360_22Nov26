import { readFile } from 'node:fs/promises';
import { Client } from 'pg';

export function localTarget(raw?: string) {
  const reject = () => new Error('Expected a loopback PostgreSQL URL with one database name and no connection options.');
  if (!raw) throw reject();
  let url: URL;
  try { url = new URL(raw); } catch { throw reject(); }
  if (!['postgresql:', 'postgres:'].includes(url.protocol) ||
      !['127.0.0.1', '[::1]', 'localhost'].includes(url.hostname) ||
      !/^\/[\w-]+$/.test(url.pathname) || url.search || url.hash) throw reject();
  return {
    host: url.hostname === '[::1]' ? '::1' : '127.0.0.1',
    port: Number(url.port || 5432),
    database: url.pathname.slice(1),
    user: decodeURIComponent(url.username) || undefined,
    password: decodeURIComponent(url.password) || undefined
  };
}

export type Operation = 'up' | 'down' | 'seed';

export async function run(operation: Operation, url: string | undefined, environment?: string) {
  const target = localTarget(url);
  if (operation === 'seed' && !['development', 'test'].includes(environment ?? '')) {
    throw new Error('Seed requires APP_ENV=development or APP_ENV=test');
  }
  const db = new Client(target);
  await db.connect();
  try {
    await db.query('BEGIN');
    await db.query("SELECT pg_advisory_xact_lock(hashtext('bhava360.db.migrations'))");
    if (operation === 'seed') {
      await db.query(await readFile(new URL('../seed.sql', import.meta.url), 'utf8'));
    } else {
      await db.query('CREATE TABLE IF NOT EXISTS bhava_migrations (version integer PRIMARY KEY)');
      for (const version of operation === 'up' ? [1, 2, 3] : [3, 2, 1]) {
        const applied = await db.query('SELECT version FROM bhava_migrations WHERE version=$1', [version]);
        if (Boolean(applied.rowCount) === (operation === 'up')) continue;
        const file = String(version).padStart(3, '0');
        await db.query(await readFile(new URL(`../drizzle/${file}.${operation}.sql`, import.meta.url), 'utf8'));
        await db.query(operation === 'up'
          ? 'INSERT INTO bhava_migrations VALUES ($1)'
          : 'DELETE FROM bhava_migrations WHERE version=$1', [version]);
      }
    }
    await db.query('COMMIT');
  } catch (error) {
    await db.query('ROLLBACK');
    throw error;
  } finally {
    await db.end();
  }
}
