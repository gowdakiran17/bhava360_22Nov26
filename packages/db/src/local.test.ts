import { randomBytes } from 'node:crypto';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createServer, type AddressInfo } from 'node:net';
import EmbeddedPostgres from 'embedded-postgres';
import { expect, it } from 'vitest';
import { localTarget, run } from './local';

it.each([
  'postgres://example.test/demo', 'postgres://127.0.0.1/demo?host=example.test',
  'postgres://localhost/demo?hostaddr=192.0.2.1', 'postgres:///demo',
  'postgres://127.0.0.1@example.test/demo', 'https://localhost/demo'
])('rejects unsafe targets before connecting', url => {
  expect(() => localTarget(url)).toThrow(/loopback/);
});

it('round trips the schema, protects sensitive fields and cascades deletes', async () => {
  const socket = createServer();
  await new Promise<void>(resolve => socket.listen(0, '127.0.0.1', resolve));
  const { port } = socket.address() as AddressInfo;
  await new Promise<void>(resolve => socket.close(() => resolve()));
  const password = randomBytes(24).toString('hex');
  const directory = await mkdtemp(join(tmpdir(), 'bhava-pg-'));
  const server = new EmbeddedPostgres({
    databaseDir: directory, user: 'postgres', password, port, persistent: false,
    postgresFlags: ['-c', 'listen_addresses=127.0.0.1', '-k', directory],
    autoRehydrateSymlinks: true, onLog: () => {}
  });
  const url = `postgres://postgres:${password}@127.0.0.1:${port}/postgres`;
  await server.initialise();
  await server.start();
  const db = server.getPgClient('postgres', '127.0.0.1');
  try {
    await db.connect();
    await Promise.all([run('up', url), run('up', url)]);
    await expect(run('seed', url, 'production')).rejects.toThrow(/APP_ENV/);
    await run('seed', url, 'test');
    await run('seed', url, 'test');
    const count = async (query: string, args: unknown[] = []) =>
      (await db.query(query, args)).rowCount;
    expect(await count('SELECT id FROM users')).toBe(5);
    expect(await count('SELECT id FROM profiles')).toBe(6);
    expect(await count('SELECT id FROM staff_users')).toBe(6);
    expect(await count("SELECT id FROM places WHERE 'Mysore'=ANY(aliases) AND city='Mysuru'")).toBe(1);
    const fixture = (await db.query("SELECT * FROM profiles WHERE display_name='Asha'")).rows[0];
    expect(fixture.birth_instant.toISOString()).toBe('1992-03-12T00:10:00.000Z');
    const { user_id, id } = fixture;
    await db.query("INSERT INTO sessions(user_id,token_hash,expires_at) VALUES ($1,'synthetic-hash',now())", [user_id]);
    await db.query("INSERT INTO consents(user_id,purpose,version,required,granted) VALUES ($1,'profile','v1',true,true)", [user_id]);
    await db.query("INSERT INTO identities(user_id,kind,identifier_digest) VALUES ($1,'phone','synthetic-phone-digest')", [user_id]);
    await expect(db.query("INSERT INTO palm_sessions(profile_id,storage_pointer) VALUES ($1,'test')",[id])).rejects.toThrow(/opted_in_storage/);
    await expect(db.query("INSERT INTO check_requests(profile_id,tool_type,inputs) VALUES ($1,'vehicle','{}')",[id])).rejects.toThrow(/explicit_save/);
    await expect(db.query("UPDATE audit_log SET action='test'")).rejects.toThrow(/append-only/);
    const names = (await db.query("SELECT column_name FROM information_schema.columns WHERE table_schema='public'")).rows.map(r => r.column_name);
    expect(names.filter(n => /^(pan|cvv|raw_otp|otp_code|gps_trace|raw_phone|image_bytes|prompt)$/.test(n))).toEqual([]);
    await db.query("UPDATE users SET deactivated_at=now(), delete_by=now()+interval '30 days' WHERE id=$1", [user_id]);
    await db.query('DELETE FROM users WHERE id=$1', [user_id]);
    for (const table of ['profiles','identities','sessions','consents']) {
      expect(await count(`SELECT id FROM ${table} WHERE user_id=$1`,[user_id])).toBe(0);
    }
    expect(await count('SELECT id FROM profiles WHERE birth_instant=$1',[fixture.birth_instant])).toBe(0);
    await run('down',url);
    expect(await count("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename <> 'bhava_migrations'")).toBe(0);
    await run('up',url);
  } finally {
    await db.end();
    await server.stop();
  }
}, 60000);
