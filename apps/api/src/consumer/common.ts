import type { Pool, PoolClient } from 'pg';
import type { catalogue } from '@bhava360/i18n';

export type Body = Record<string, unknown>;
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly key: keyof ReturnType<typeof catalogue>,
  ) {
    super(key);
  }
}
export function invalid(): never {
  throw new ApiError(400, 'invalid');
}
export function text(value: unknown, max = 120): string {
  if (typeof value !== 'string' || !value.trim() || value.length > max)
    return invalid();
  return value.trim();
}
export function uuid(value: unknown) {
  const id = text(value);
  if (!/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(id))
    return invalid();
  return id;
}
export function locale(value: unknown) {
  if (value !== 'en' && value !== 'kn' && value !== 'hi') return invalid();
  return value;
}
export async function transaction<T>(
  pool: Pool,
  work: (db: PoolClient) => Promise<T>,
) {
  const db = await pool.connect();
  try {
    await db.query('BEGIN');
    const result = await work(db);
    await db.query('COMMIT');
    return result;
  } catch (error) {
    await db.query('ROLLBACK');
    throw error;
  } finally {
    db.release();
  }
}
