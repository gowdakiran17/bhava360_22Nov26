import type { PoolClient } from 'pg';
import { resolveBirth } from '@bhava360/core';
import { ApiError, invalid, text, uuid, type Body } from './common';

const FREE_PROFILE_LIMIT = 3;
const fields = `id, display_name, local_date::text, local_time::text, iana_zone, birth_instant,
  place_id, time_precision, relation, gender, adult_permission`;
export async function profiles(
  db: PoolClient,
  user: string,
  session: string,
  method: string,
  id: string | undefined,
  body: Body,
) {
  if (method === 'GET' && !id) {
    return (
      await db.query(
        `SELECT ${fields} FROM profiles WHERE user_id=$1 AND deleted_at IS NULL ORDER BY id`,
        [user],
      )
    ).rows;
  }
  let previous;
  if (id) {
    previous = (
      await db.query(
        `SELECT ${fields} FROM profiles WHERE id=$1 AND user_id=$2 AND deleted_at IS NULL`,
        [uuid(id), user],
      )
    ).rows[0];
    if (!previous) throw new ApiError(404, 'missing');
    if (method === 'GET') return previous;
    if (method === 'DELETE') {
      await db.query('UPDATE profiles SET deleted_at=now() WHERE id=$1', [id]);
      await db.query(
        'UPDATE sessions SET active_profile_id=NULL WHERE active_profile_id=$1',
        [id],
      );
      return {};
    }
    if (method === 'switch') {
      await db.query('UPDATE sessions SET active_profile_id=$1 WHERE id=$2', [
        id,
        session,
      ]);
      return { active_profile_id: id };
    }
  }
  if (!(id ? method === 'PATCH' : method === 'POST'))
    throw new ApiError(405, 'invalid');
  if (!previous) {
    // The calling transaction holds the user row lock, serializing cap checks.
    const cap = await db.query(
      `SELECT count(*) >= $2::integer AND NOT EXISTS
      (SELECT 1 FROM entitlements WHERE user_id=$1 AND capability='plus' AND (expires_at IS NULL OR expires_at>now())) AS reached
      FROM profiles WHERE user_id=$1 AND deleted_at IS NULL`,
      [user, FREE_PROFILE_LIMIT],
    );
    if (cap.rows[0].reached) throw new ApiError(409, 'profileCap');
  }
  const input = { ...previous, ...body };
  const name = text(input.display_name);
  const relation = text(input.relation, 40);
  const permission = input.adult_permission ?? false;
  if (
    typeof permission !== 'boolean' ||
    (relation !== 'self' && relation !== 'child' && !permission)
  )
    throw new ApiError(400, 'permission');
  const gender = input.gender == null ? null : text(input.gender, 40);
  const precision = input.time_precision;
  if (!['known', 'unknown', 'approximate'].includes(precision))
    return invalid();
  const date = text(input.local_date);
  const time = precision === 'unknown' ? '12:00' : text(input.local_time);
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(date) ||
    !/^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$/.test(time)
  )
    return invalid();
  const choice = body.disambiguation;
  if (choice !== undefined && choice !== 'earlier' && choice !== 'later')
    return invalid();
  const place = uuid(input.place_id);
  const zone = (
    await db.query('SELECT iana_zone FROM places WHERE id=$1', [place])
  ).rows[0]?.iana_zone;
  if (!zone) return invalid();
  let instant = previous?.birth_instant;
  if (
    !previous ||
    date !== previous.local_date ||
    (time.length === 5 ? time + ':00' : time) !== previous.local_time ||
    place !== previous.place_id ||
    choice !== undefined
  ) {
    try {
      instant = resolveBirth(date, time, zone, choice);
    } catch (err) {
      if (err instanceof RangeError && err.message === 'chooseTime')
        throw new ApiError(409, 'chooseTime');
      return invalid();
    }
  }
  const values = [
    name,
    relation,
    gender,
    permission,
    date,
    time,
    zone,
    instant,
    precision,
    place,
    user,
  ];
  if (id) {
    return (
      await db.query(
        `UPDATE profiles SET (display_name,relation,gender,adult_permission,local_date,local_time,
      iana_zone,birth_instant,time_precision,place_id)=($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
      WHERE user_id=$11 AND id=$12 RETURNING ${fields}`,
        [...values, id],
      )
    ).rows[0];
  }
  return (
    await db.query(
      `INSERT INTO profiles(display_name,relation,gender,adult_permission,local_date,local_time,
    iana_zone,birth_instant,time_precision,place_id,user_id) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11) RETURNING ${fields}`,
      values,
    )
  ).rows[0];
}

export async function consents(
  db: PoolClient,
  user: string,
  method: string,
  body: Body,
) {
  const required = ['adult', 'terms', 'birthDetails'];
  const purposes = [...required, 'ai', 'updates', 'analytics'];
  if (method === 'POST') {
    const version = text(body.consent_version);
    if (required.some((k) => body[k] !== true))
      throw new ApiError(400, 'requiredConsent');
    for (const purpose of purposes) {
      const granted = body[purpose] ?? false;
      if (typeof granted !== 'boolean') return invalid();
      await db.query(
        'INSERT INTO consents(user_id,purpose,version,required,granted) VALUES ($1,$2,$3,$4,$5)',
        [user, purpose, version, required.includes(purpose), granted],
      );
    }
  } else if (method !== 'GET') throw new ApiError(405, 'invalid');
  return (
    await db.query(
      'SELECT purpose,version,required,granted,recorded_at FROM consents WHERE user_id=$1 ORDER BY recorded_at,purpose',
      [user],
    )
  ).rows;
}
