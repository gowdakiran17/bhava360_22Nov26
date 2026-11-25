import {
  birthEpoch,
  localDayBounds,
  utcAtJulianDay,
  type EphemerisPort,
  type Precision,
} from '@bhava360/core';
import type { Catalogue, YearClock } from './catalogue';

type TimePrecision = Precision | 'exact' | '±5 min' | '±15 min' | '±1 h';
export interface VimshottariInput {
  birthInstantUtc: string;
  timeZone: string;
  timePrecision: TimePrecision;
  yearClock?: YearClock;
  includeSookshma?: boolean;
}
export interface Period {
  level: 'maha' | 'antar' | 'pratyantar' | 'sookshma';
  lord: string;
  startUtc: string;
  endUtc: string;
  children?: Period[];
}
const levels = ['maha', 'antar', 'pratyantar', 'sookshma'] as const;
const radiusMinutes = {
  known: 2,
  exact: 2,
  approximate: 15,
  '±5 min': 5,
  '±15 min': 15,
  '±1 h': 60,
};

export function computeVimshottari(
  port: EphemerisPort,
  kb: Catalogue,
  input: VimshottariInput,
) {
  const table = kb.periods;
  const {
    birthInstantUtc,
    timeZone,
    timePrecision,
    yearClock = table.default_year,
  } = input;
  const yearDays = Number(table.year_days[yearClock]);
  if (!Number.isFinite(yearDays)) throw new RangeError('Unknown dasha clock');
  const epoch = birthEpoch(
    birthInstantUtc,
    timeZone,
    timePrecision === 'unknown' ? 'unknown' : 'known',
  );
  const central = port.longitude(epoch.jdUt, 'moon', 'lahiri');
  const convention = {
    yearClock,
    yearDays,
    timePrecision,
    timeZone,
    ayanamsaId: 'lahiri',
    siderealMode: 1,
    ephemerisFlag: central.flag,
    workingInstantUtc: epoch.utc,
  };
  const width = table.star_width_arcseconds;
  const arc = central.longitude * 3600;
  const star = Math.floor(arc / width);
  const day = localDayBounds(birthInstantUtc, timeZone);
  const radius =
    timePrecision === 'unknown' ? 0 : radiusMinutes[timePrecision] / 1440;
  const bounds =
    timePrecision === 'unknown'
      ? [day.start, day.end - 1 / 86400000]
      : [epoch.jdUt - radius, epoch.jdUt + radius];
  // The geocentric Moon advances monotonically and cannot make a full turn within a civil day.
  if (
    bounds.some((t) => {
      const moon = port.longitude(t, 'moon', 'lahiri');
      if (moon.flag !== central.flag)
        throw new Error('Mixed ephemerides in birth window');
      return Math.floor((moon.longitude * 3600) / width) !== star;
    })
  )
    return { convention, birthBalance: null, timeline: null };
  const order = table.lord_order;
  const first = order.indexOf(kb.nakshatras[star].lord);
  if (first < 0) throw new Error('Unknown birth nakshatra lord');
  const years = table.sequence[order[first]];
  const elapsedYears = (years * (arc - star * width)) / width;
  const origin = epoch.jdUt - elapsedYears * yearDays;
  const maxDepth = input.includeSookshma ? 3 : 2;
  // Accumulate each level from its full parent, pinning its final end to that parent.
  function subdivide(
    start: number,
    end: number,
    firstIndex: number,
    depth: number,
  ): Period[] {
    let previous = start,
      sum = 0;
    return order.map((_, i) => {
      const idx = (firstIndex + i) % order.length,
        lord = order[idx];
      sum += table.sequence[lord];
      const next =
        i === order.length - 1
          ? end
          : start + ((end - start) * sum) / table.cycle_years;
      const item: Period = {
        level: levels[depth],
        lord,
        startUtc: utcAtJulianDay(previous),
        endUtc: utcAtJulianDay(next),
      };
      if (depth < maxDepth)
        item.children = subdivide(previous, next, idx, depth + 1);
      previous = next;
      return item;
    });
  }
  return {
    convention,
    birthBalance: {
      lord: order[first],
      elapsedYears,
      remainingYears: years - elapsedYears,
    },
    timeline: subdivide(
      origin,
      origin + table.cycle_years * yearDays,
      first,
      0,
    ),
  };
}
