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

export interface EphemerisPort {
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
