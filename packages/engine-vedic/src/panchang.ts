import {
  birthEpoch,
  localDayBounds,
  utcAtJulianDay,
  type EphemerisPort,
  type SunriseMethod,
} from '@bhava360/core';
import type { Catalogue } from './catalogue';

import { dayWindows, interval, type SolarDay } from './panchang-day';
import {
  lunarCalendar,
  festivals,
  sunriseTithis,
  firstCrossing,
  type CalendarProfile,
} from './lunar-calendar';

export interface PanchangInput {
  instantUtc: string;
  latitude: number;
  longitude: number;
  timeZone: string;
  calendarProfile?: CalendarProfile;
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
    return firstCrossing(lo, hi, (time) => unwrapped(time) >= target);
  }
  return {
    index,
    start: crossing((index * widthSeconds) / 3600, at - 2, at),
    end: crossing(((index + 1) * widthSeconds) / 3600, at, at + 2),
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
    body: 'sun' | 'moon' = 'sun',
  ) {
    const jd = port.riseSet(
      day.start,
      body,
      event,
      latitude,
      longitude,
      elevationM,
      body === 'moon' ? 'apparent-upper-limb' : sunriseMethod,
    );
    return jd !== null && jd >= day.start && jd < day.end ? jd : null;
  }
  const today = localDayBounds(instantUtc, timeZone);
  function solarDay(offset: number): SolarDay {
    const bounds =
      offset === 0 ? today : localDayBounds(instantUtc, timeZone, offset);
    return {
      weekday: bounds.weekday,
      date: bounds.date,
      sunrise: onDay(bounds, 'rise'),
      sunset: onDay(bounds, 'set'),
    };
  }
  const day = solarDay(0),
    previous = solarDay(-1),
    next = solarDay(1);
  const { sunrise: rise, sunset: set } = day;
  const vara =
    rise === null
      ? null
      : at >= rise
        ? day.weekday
        : previous.sunrise === null
          ? null
          : previous.weekday;
  const calendarProfile = input.calendarProfile ?? 'amanta';
  if (calendarProfile !== 'amanta' && calendarProfile !== 'purnimanta')
    throw new RangeError('Unknown calendar profile');
  const resource = (file: string) =>
    kb.resources['vedic/panchang/' + file + '.yaml'];
  const sun = (t: number) => position(t, 'sun');
  const calendar = lunarCalendar(
    elongation,
    sun,
    resource('calendar-profiles').amanta_months_by_entered_sign,
    calendarProfile,
  );
  const labels = (id: string): number[] =>
    kb.rules['vedic.panchang.' + id].rule.conditions.all[0].value;
  function moonEvent(event: 'rise' | 'set') {
    const value = onDay(today, event, 'moon');
    return value === null ? null : utcAtJulianDay(value);
  }
  return {
    moonriseUtc: moonEvent('rise'),
    moonsetUtc: moonEvent('set'),
    masa: calendar.month(at),
    sunriseTithis: sunriseTithis(rise, next.sunrise, elongation),
    windows: dayWindows(
      day,
      previous.sunset,
      next.sunrise,
      resource('day-night'),
      resource('limbs').day_eighths_sunday_first,
      resource('limb-tables').vara,
    ),
    festivals: festivals(
      day,
      previous,
      next,
      sun,
      calendar,
      {
        ekadashi: labels('ekadashi'),
        purnima: labels('purnima'),
        amavasya: labels('amavasya'),
      },
      (instant) => {
        const limb = limbInterval(instant, elongation, kb.widths.tithi);
        return { ...limb, number: limb.index + 1 };
      },
    ),
    sunriseUtc: rise === null ? null : utcAtJulianDay(rise),
    sunsetUtc: set === null ? null : utcAtJulianDay(set),
    vara,
    tithi: {
      ...kb.tables.tithi[t.index],
      ...interval(t.start, t.end),
    },
    nakshatra: {
      ...kb.nakshatras[n.index],
      ...interval(n.start, n.end),
    },
    yoga: {
      number: y.index + 1,
      name: kb.tables.yoga[y.index],
      ...interval(y.start, y.end),
    },
    karana: {
      index: k.index,
      ...interval(k.start, k.end),
      name:
        kb.tables.karana.fixed[k.index] ??
        kb.tables.karana.movable[(k.index - 1) % 7],
    },
    convention: {
      calendarProfile,
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
