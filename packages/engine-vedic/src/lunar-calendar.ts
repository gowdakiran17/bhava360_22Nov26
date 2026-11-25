import { utcAtJulianDay } from '@bhava360/core';
import { interval, type SolarDay } from './panchang-day';
export type CalendarProfile = 'amanta' | 'purnimanta';
type Angle = (at: number) => number;

// Find the first representable UT Julian day on the incoming side of a crossing.
export function firstCrossing(
  lo: number,
  hi: number,
  entered: (at: number) => boolean,
) {
  while (true) {
    const mid = (lo + hi) / 2;
    if (mid === lo || mid === hi) return hi;
    if (entered(mid)) hi = mid;
    else lo = mid;
  }
}
function newMoon(at: number, direction: -1 | 1, phase: Angle) {
  let inner = at;
  for (let i = 0; i < 18; i++) {
    const outer = inner + direction * 2;
    const lo = Math.min(inner, outer),
      hi = Math.max(inner, outer);
    if (phase(hi) < phase(lo))
      return firstCrossing(lo, hi, (t) => phase(t) < 180);
    inner = outer;
  }
  throw new RangeError('Unbracketed new moon');
}

function solarIngresses(start: number, end: number, sun: Angle) {
  const events: { at: number; sign: number }[] = [];
  // Start before the interval so a crossing exactly at its lower edge is counted.
  let lo = start - 1;
  while (lo < end) {
    const hi = Math.min(lo + 5, end);
    const oldSign = Math.floor(sun(lo) / 30),
      sign = Math.floor(sun(hi) / 30);
    if (sign !== oldSign) {
      const at = firstCrossing(
        lo,
        hi,
        (t) => Math.floor(sun(t) / 30) !== oldSign,
      );
      if (start <= at && at < end) events.push({ at, sign });
    }
    lo = hi;
  }
  return events;
}
export function lunarCalendar(
  phase: Angle,
  sun: Angle,
  names: string[],
  profile: CalendarProfile,
) {
  function compute(at: number) {
    const start = newMoon(at, -1, phase),
      end = newMoon(at, 1, phase);
    const ingresses = solarIngresses(start, end, sun);
    const kind =
      ingresses.length === 0
        ? 'adhika'
        : ingresses.length === 1
          ? 'ordinary'
          : 'kshaya';
    const next =
      ingresses.length === 0 ? solarIngresses(end, end + 34, sun)[0] : null;
    const monthNames = ingresses.length
      ? ingresses.map((e) => names[e.sign])
      : next
        ? [names[next.sign]]
        : [];
    return {
      start,
      end,
      kind,
      names: monthNames,
      name: monthNames.length === 1 ? monthNames[0] : null,
      ingresses: ingresses.map((e) => ({
        instantUtc: utcAtJulianDay(e.at),
        enteredSign: e.sign + 1,
      })),
    };
  }
  const cached: ReturnType<typeof compute>[] = [];
  function lunation(at: number) {
    const found = cached.find((l) => l.start <= at && at < l.end);
    if (found) return found;
    const result = compute(at);
    cached.push(result);
    return result;
  }
  function month(at: number) {
    const current = lunation(at);
    const dark = phase(at) >= 180;
    const display =
      profile === 'purnimanta' && dark ? lunation(current.end) : current;
    return {
      profile,
      kind: current.kind,
      name: current.name === null ? null : display.name,
      lunationNames: current.names,
      ...interval(current.start, current.end),
      ingresses: current.ingresses,
    };
  }
  return { lunation, month };
}

export function sunriseTithis(
  rise: number | null,
  next: number | null,
  phase: Angle,
) {
  if (rise === null || next === null || next <= rise) return null;
  const a = phase(rise),
    b = phase(next);
  const first = Math.floor(a / 12),
    last = Math.floor((b < a ? b + 360 : b) / 12);
  return {
    first: first + 1,
    next: (last % 30) + 1,
    kind: last === first ? 'adhika' : last > first + 1 ? 'kshaya' : 'ordinary',
    skipped: Array.from(
      { length: Math.max(0, last - first - 1) },
      (_, i) => ((first + 1 + i) % 30) + 1,
    ),
  };
}

export type FestivalId =
  | 'ugadi'
  | 'deepavali'
  | 'sankranti'
  | 'ekadashi'
  | 'pradosh'
  | 'purnima'
  | 'amavasya';
interface Festival {
  id: FestivalId;
  date: string;
  startUtc: string;
  endUtc?: string;
  enteredSign?: number;
}
export function festivals(
  day: SolarDay,
  previousDay: SolarDay,
  nextDay: SolarDay,
  sun: Angle,
  calendar: ReturnType<typeof lunarCalendar>,
  sunriseLabels: Record<'ekadashi' | 'purnima' | 'amavasya', number[]>,
  tithiInterval: (at: number) => { start: number; end: number; number: number },
) {
  const { sunrise: rise, sunset: set, date } = day;
  const result: Festival[] = [];
  if (rise === null) return result;
  const next = nextDay.sunrise;
  const atRise = tithiInterval(rise);
  if (calendar.month(rise).name !== null) {
    for (const id of ['ekadashi', 'purnima', 'amavasya'] as const)
      if (sunriseLabels[id].includes(atRise.number))
        result.push({ id, date, ...interval(atRise.start, atRise.end) });
  }
  if (next === null || next <= rise) return result;
  for (const e of solarIngresses(rise, next, sun))
    if (calendar.month(e.at).name !== null)
      result.push({
        id: 'sankranti',
        date,
        startUtc: utcAtJulianDay(e.at),
        enteredSign: e.sign + 1,
      });

  // A skipped Pratipada belongs to the sunrise immediately before it.
  const candidate =
    atRise.number === 1
      ? atRise
      : atRise.number === 30 && atRise.end < next
        ? tithiInterval(atRise.end)
        : null;
  if (candidate?.number === 1) {
    const current = calendar.lunation(candidate.start);
    if (
      current.name === 'chaitra' &&
      !calendar.lunation(current.start - 1).names.includes('chaitra')
    ) {
      const previous = previousDay.sunrise;
      if (
        previous !== null &&
        previous < candidate.start &&
        (atRise.number === 1 || candidate.end <= next)
      )
        result.push({
          id: 'ugadi',
          date,
          ...interval(candidate.start, candidate.end),
        });
    }
  }
  if (set === null || set <= rise || set >= next) return result;
  const eveningEnd = set + (next - set) / 5;
  let cursor = set;
  while (cursor < eveningEnd) {
    const tide = tithiInterval(cursor);
    if (tide.end <= cursor) throw new Error('Non-increasing tithi interval');
    const end = Math.min(tide.end, eveningEnd);
    if ([13, 28, 30].includes(tide.number)) {
      const month = calendar.month(cursor);
      if (month.name !== null && tide.number !== 30) {
        result.push({ id: 'pradosh', date, ...interval(cursor, end) });
      } else if (
        tide.number === 30 &&
        month.kind === 'ordinary' &&
        month.lunationNames[0] === 'ashvina' &&
        month.name === (month.profile === 'amanta' ? 'ashvina' : 'kartika')
      ) {
        const nextSet = nextDay.sunset;
        // Two qualifying evenings give the observance to the later one.
        if (tide.end <= next || (nextSet !== null && tide.end <= nextSet))
          result.push({ id: 'deepavali', date, ...interval(cursor, end) });
      }
    }
    cursor = end;
  }
  return result;
}
