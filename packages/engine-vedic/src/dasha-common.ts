import {
  birthEpoch,
  localDayBounds,
  utcAtJulianDay,
  type EphemerisPort,
  type Precision,
} from '@bhava360/core';

export type TimePrecision = Precision | 'exact' | '±5 min' | '±15 min' | '±1 h';
const radiusMinutes = {
  known: 2,
  exact: 2,
  approximate: 15,
  '±5 min': 5,
  '±15 min': 15,
  '±1 h': 60,
};

export interface BirthDashaInput {
  birthInstantUtc: string;
  timeZone: string;
  timePrecision: TimePrecision;
}
export function birthWindow({
  birthInstantUtc,
  timeZone,
  timePrecision,
}: BirthDashaInput) {
  const epoch = birthEpoch(
    birthInstantUtc,
    timeZone,
    timePrecision === 'unknown' ? 'unknown' : 'known',
  );
  const day = localDayBounds(birthInstantUtc, timeZone);
  const radius =
    timePrecision === 'unknown' ? 0 : radiusMinutes[timePrecision] / 1440;
  const bounds =
    timePrecision === 'unknown'
      ? [day.start, day.end - 1 / 86400000]
      : [epoch.jdUt - radius, epoch.jdUt + radius];
  if (!bounds.every(Number.isFinite))
    throw new RangeError('Invalid time precision');
  return { epoch, bounds };
}
export function lunarSeed(
  port: EphemerisPort,
  input: BirthDashaInput,
  width: number,
) {
  const { epoch, bounds } = birthWindow(input);
  const central = port.longitude(epoch.jdUt, 'moon', 'lahiri');
  const arc = central.longitude * 3600;
  const star = Math.floor(arc / width);
  const stable = bounds.every((t) => {
    const moon = port.longitude(t, 'moon', 'lahiri');
    if (moon.flag !== central.flag)
      throw new Error('Mixed ephemerides in birth window');
    return Math.floor((moon.longitude * 3600) / width) === star;
  });
  return {
    epoch,
    star,
    stable,
    fraction: (arc - star * width) / width,
    flag: central.flag,
  };
}
export interface Period {
  level: 'maha' | 'antar' | 'pratyantar' | 'sookshma';
  lord: string;
  startUtc: string;
  endUtc: string;
  children?: Period[];
}
const levels = ['maha', 'antar', 'pratyantar', 'sookshma'] as const;
export function lunarTimeline(
  origin: number,
  yearDays: number,
  first: number,
  order: string[],
  weights: Record<string, number>,
  cycle: number,
  maxDepth: number,
) {
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
      sum += weights[lord];
      const next =
        i === order.length - 1 ? end : start + ((end - start) * sum) / cycle;
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
  return subdivide(origin, origin + cycle * yearDays, first, 0);
}
