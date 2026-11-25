import { Temporal } from '@js-temporal/polyfill';
import { resolveBirth } from './birth';

export type Orbit =
  | 'sun'
  | 'moon'
  | 'mercury'
  | 'venus'
  | 'mars'
  | 'jupiter'
  | 'saturn'
  | 'meanNode'
  | 'trueNode';
export type Frame = 'tropical' | 'lahiri';
export type EphemerisFlag = 'SEFLG_MOSEPH' | 'SEFLG_SWIEPH';
export type Precision = 'known' | 'approximate' | 'unknown';

export type SunriseMethod = 'apparent-upper-limb' | 'traditional-disc-centre';
export interface EphemerisPort {
  /** Next topocentric event in UT Julian days, or null on circumpolar no-event. */
  riseSet(
    jdUt: number,
    body: 'sun' | 'moon',
    event: 'rise' | 'set',
    latitude: number,
    longitude: number,
    elevationM?: number,
    method?: SunriseMethod,
  ): number | null;
  longitude(
    jdUt: number,
    orbit: Orbit,
    frame: Frame,
  ): {
    longitude: number;
    speed: number;
    flag: EphemerisFlag;
  };
  lahiriAyanamsa(jdUt: number): number;
  ascendant(
    jdUt: number,
    latitude: number,
    longitude: number,
    frame: Frame,
  ): number;
}

export function birthEpoch(utc: string, zone: string, precision: Precision) {
  if (!utc.endsWith('Z'))
    throw new RangeError('Expected an ISO UTC instant ending in Z');
  if (!zone || /^[+-]/.test(zone))
    throw new RangeError('Expected an IANA time zone');
  const instant = Temporal.Instant.from(utc);
  const local = instant.toZonedDateTimeISO(zone);
  const working =
    precision === 'unknown'
      ? Temporal.Instant.from(
          resolveBirth(local.toPlainDate().toString(), '12:00', zone),
        )
      : instant;
  // Gregorian Unix epoch is JD 2440587.5. UTC approximates UT1 for this slice.
  return {
    utc: working.toString(),
    jdUt: 2440587.5 + Number(working.epochNanoseconds) / 86400000000000,
  };
}

const dayMs = 86400000;
export function utcAtJulianDay(jd: number) {
  return Temporal.Instant.fromEpochNanoseconds(
    BigInt(Math.round((jd - 2440587.5) * dayMs * 1000)) * 1000n,
  ).toString();
}

/** Calendar arithmetic preserves short and long civil days at offset transitions. */
export function localDayBounds(utc: string, zone: string, offsetDays = 0) {
  const local = Temporal.Instant.from(utc).toZonedDateTimeISO(zone);
  const start = local
    .toPlainDate()
    .add({ days: offsetDays })
    .toZonedDateTime(zone);
  const end = start.toPlainDate().add({ days: 1 }).toZonedDateTime(zone);
  return {
    start: 2440587.5 + start.epochMilliseconds / dayMs,
    end: 2440587.5 + end.epochMilliseconds / dayMs,
    weekday: start.dayOfWeek % 7,
  };
}
