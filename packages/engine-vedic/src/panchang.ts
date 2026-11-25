import {
  birthEpoch,
  localDayBounds,
  utcAtJulianDay,
  type EphemerisPort,
  type SunriseMethod,
} from '@bhava360/core';
import type { Catalogue } from './catalogue';

export interface PanchangInput {
  instantUtc: string;
  latitude: number;
  longitude: number;
  timeZone: string;
  elevationM?: number;
  nodeType?: 'mean' | 'true';
  sunriseMethod?: SunriseMethod;
}

function normalize(x: number) {
  const remainder = x % 360;
  return remainder < 0 ? (remainder + 360) % 360 : remainder;
}

// Over the bracketing window each lunar angle moves forward by less than half a turn.
function limbInterval(
  at: number,
  angle: (t: number) => number,
  widthSeconds: number,
) {
  const origin = angle(at);
  const index = Math.floor((origin * 3600) / widthSeconds);
  function unwrapped(t: number) {
    const value = angle(t);
    if (value - origin > 180) return value - 360;
    if (origin - value > 180) return value + 360;
    return value;
  }
  function crossing(target: number, lo: number, hi: number) {
    if (unwrapped(lo) > target || unwrapped(hi) < target)
      throw new RangeError('Lunar crossing outside bracket');
    while (true) {
      const mid = (lo + hi) / 2;
      if (mid === lo || mid === hi) return utcAtJulianDay(hi);
      if (unwrapped(mid) >= target) hi = mid;
      else lo = mid;
    }
  }
  return {
    index,
    startUtc: crossing((index * widthSeconds) / 3600, at - 2, at),
    endUtc: crossing(((index + 1) * widthSeconds) / 3600, at, at + 2),
  };
}

export function computePanchang(
  port: EphemerisPort,
  kb: Catalogue,
  input: PanchangInput,
) {
  const {
    instantUtc,
    timeZone,
    latitude,
    longitude,
    elevationM = kb.observer.elevation_default_m,
    sunriseMethod = 'apparent-upper-limb',
    nodeType = 'mean',
  } = input;
  if (
    !Number.isFinite(latitude) ||
    Math.abs(latitude) > 90 ||
    !Number.isFinite(longitude) ||
    Math.abs(longitude) > 180 ||
    !Number.isFinite(elevationM)
  )
    throw new RangeError('Invalid observer');
  const at = birthEpoch(instantUtc, timeZone, 'known').jdUt;
  const flag = port.longitude(at, 'sun', 'lahiri').flag;
  function position(t: number, body: 'moon' | 'sun') {
    const p = port.longitude(t, body, 'lahiri');
    if (p.flag !== flag) throw new Error('Mixed ephemerides in Panchang');
    return p.longitude;
  }
  const moon = (t: number) => position(t, 'moon');
  const elongation = (t: number) => normalize(moon(t) - position(t, 'sun'));
  const t = limbInterval(at, elongation, kb.widths.tithi);
  const k = limbInterval(at, elongation, kb.widths.karana);
  const n = limbInterval(at, moon, kb.widths.nakshatra);
  const y = limbInterval(
    at,
    (t) => normalize(moon(t) + position(t, 'sun')),
    kb.widths.yoga,
  );
  function onDay(
    day: ReturnType<typeof localDayBounds>,
    event: 'rise' | 'set',
  ) {
    const jd = port.riseSet(
      day.start,
      'sun',
      event,
      latitude,
      longitude,
      elevationM,
      sunriseMethod,
    );
    return jd !== null && jd >= day.start && jd < day.end ? jd : null;
  }
  const today = localDayBounds(instantUtc, timeZone);
  const rise = onDay(today, 'rise'),
    set = onDay(today, 'set');
  let vara: number | null = null;
  if (rise !== null) {
    if (at >= rise) vara = today.weekday;
    else {
      const previous = localDayBounds(instantUtc, timeZone, -1);
      if (onDay(previous, 'rise') !== null) vara = previous.weekday;
    }
  }
  return {
    sunriseUtc: rise === null ? null : utcAtJulianDay(rise),
    sunsetUtc: set === null ? null : utcAtJulianDay(set),
    vara,
    tithi: {
      ...kb.tables.tithi[t.index],
      startUtc: t.startUtc,
      endUtc: t.endUtc,
    },
    nakshatra: {
      ...kb.nakshatras[n.index],
      startUtc: n.startUtc,
      endUtc: n.endUtc,
    },
    yoga: {
      number: y.index + 1,
      name: kb.tables.yoga[y.index],
      startUtc: y.startUtc,
      endUtc: y.endUtc,
    },
    karana: {
      ...k,
      name:
        kb.tables.karana.fixed[k.index] ??
        kb.tables.karana.movable[(k.index - 1) % 7],
    },
    convention: {
      ayanamsaId: 'lahiri',
      siderealMode: 1,
      ephemerisFlag: flag,
      nodeType,
      sunriseMethod,
      latitude,
      longitude,
      timeZone,
      elevationM,
      pressureHpa: kb.observer.pressure_hpa,
      temperatureC: kb.observer.temperature_c,
    },
  };
}
