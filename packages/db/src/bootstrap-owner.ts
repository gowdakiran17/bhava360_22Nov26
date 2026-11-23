// Local operator command; credentials are supplied through the process environment.
import { randomBytes, scrypt } from 'node:crypto';
import { promisify } from 'node:util';
import { Client } from 'pg';
import { localTarget } from './local.js';

async function bootstrap() {
  const email = process.env.ADMIN_BOOTSTRAP_OWNER_EMAIL?.trim().toLowerCase();
  const password = process.env.ADMIN_BOOTSTRAP_PASSWORD;
  if (!email || !password || password.length < 16) throw new Error();
  const salt = randomBytes(16).toString('hex');
  const hash = (await promisify(scrypt)(password, salt, 64)) as Buffer;
  const db = new Client(localTarget(process.env.DATABASE_URL));
  await db.connect();
  try {
    await db.query('BEGIN');
    await db.query('LOCK TABLE staff_users IN SHARE ROW EXCLUSIVE MODE');
    if (
      (
        await db.query(
          "SELECT id FROM staff_users WHERE role='owner' AND password_hash IS NOT NULL",
        )
      ).rowCount
    )
      throw new Error();
    const result = await db.query(
      `INSERT INTO staff_users(email,role,password_hash) VALUES($1,'owner',$2)
      ON CONFLICT(email) DO UPDATE SET password_hash=excluded.password_hash
      WHERE staff_users.role='owner' AND staff_users.password_hash IS NULL RETURNING id`,
      [email, salt + ':' + hash.toString('hex')],
    );
    if (!result.rowCount) throw new Error();
    await db.query('COMMIT');
  } catch (error) {
    await db.query('ROLLBACK');
    throw error;
  } finally {
    await db.end();
  }
}
bootstrap().catch(() => {
  console.error(
    'Owner bootstrap refused. Check local configuration and existing owner.',
  );
  process.exitCode = 1;
});
