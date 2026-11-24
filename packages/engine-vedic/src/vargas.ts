import type { EphemerisFlag, Precision } from '@bhava360/core';

const signs =
  'aries taurus gemini cancer leo virgo libra scorpio sagittarius capricorn aquarius pisces'.split(
    ' ',
  );
export type Point =
  | 'sun'
  | 'moon'
  | 'mercury'
  | 'venus'
  | 'mars'
  | 'jupiter'
  | 'saturn'
  | 'rahu'
  | 'ketu'
  | 'lagna';
export type Longitudes = Record<Exclude<Point, 'lagna'>, number> & {
  lagna: number | null;
};

interface Method {
  chart: string;
  id: string;
  read_access: string;
  degree_boundaries:
    | { equal_parts: number; sign_span_arcsec: number }
    | { odd: number[]; even: number[] };
  sign_lookup: Record<string, string[]>;
}

export interface VargaMethod {
  chart: string;
  id: string;
  access: 'MVP' | 'R2' | 'held';
  starts: number[];
  signs: number[];
}

export function prepareMethods(methods: Method[]): VargaMethod[] {
  return methods.map((method) => {
    const starts: number[] = [];
    const targets: number[] = [];
    const bounds = method.degree_boundaries;
    for (const [s, name] of signs.entries()) {
      const row = method.sign_lookup[name];
      const offsets =
        'equal_parts' in bounds
          ? Array.from(
              { length: bounds.equal_parts },
              (_, i) =>
                ((s * bounds.equal_parts + i) * 30) / bounds.equal_parts,
            )
          : (s % 2 === 0 ? bounds.odd : bounds.even)
              .slice(0, -1)
              .map((x) => s * 30 + x);
      if (row.length !== offsets.length)
        throw new Error('Incomplete varga lookup: ' + method.id);
      for (const [i, start] of offsets.entries()) {
        const target = signs.indexOf(row[i]);
        if (target < 0) throw new Error('Invalid varga sign: ' + row[i]);
        starts.push(start);
        targets.push(target + 1);
      }
    }
    const access = method.chart === 'D60' ? 'held' : method.read_access;
    if (access !== 'MVP' && access !== 'R2' && access !== 'held')
      throw new Error('Unexpected varga access: ' + access);
    return {
      chart: method.chart,
      id: method.id,
      access,
      starts,
      signs: targets,
    };
  });
}

function cell(method: VargaMethod, degrees: number) {
  if (!Number.isFinite(degrees))
    throw new RangeError('Invalid varga longitude');
  let lon = degrees % 360;
  if (lon < 0) lon += 360;
  let low = 0,
    high = method.starts.length;
  while (low + 1 < high) {
    const mid = Math.floor((low + high) / 2);
    if (method.starts[mid] <= lon) low = mid;
    else high = mid;
  }
  return low;
}

export function vargaSign(method: VargaMethod, degrees: number) {
  return method.signs[cell(method, degrees)];
}

// Check intermediate cells as well: divisional signs may repeat across an arc.
function stable(method: VargaMethod, series: number[], sign: number) {
  let previous = cell(method, series[0]);
  if (method.signs[previous] !== sign) return false;
  const count = method.starts.length;
  for (let i = 1; i < series.length; i++) {
    const next = cell(method, series[i]);
    const delta = series[i] - series[i - 1];
    const step = (Math.abs(delta) <= 180 ? delta : -delta) < 0 ? -1 : 1;
    while (previous !== next) {
      previous = (previous + step + count) % count;
      if (method.signs[previous] !== sign) return false;
    }
  }
  return true;
}

interface Placement {
  sign: number;
  unstable: boolean;
  interpretationSign: number | null;
  house: number | null;
}
interface Chart {
  read_access: VargaMethod['access'];
  candidate: boolean;
  convention: {
    methodId: string;
    ayanamsaId: 'lahiri';
    houseSystem: 'whole-sign';
    ephemerisFlag: EphemerisFlag;
    timePrecision: Precision;
  };
  positions: Record<Exclude<Point, 'lagna'>, Placement> & {
    lagna: Placement | null;
  };
}

export function computeVargas(
  methods: VargaMethod[],
  center: Longitudes,
  samples: Longitudes[],
  flag: EphemerisFlag,
  precision: Precision,
) {
  const charts: Record<string, Chart> = {};
  for (const method of methods) {
    const interpret = method.access !== 'held' && precision !== 'unknown';
    function placement(point: Point, lon: number): Placement {
      const sign = vargaSign(method, lon);
      const series = samples.map((sample) => sample[point] as number);
      const unstable = !stable(method, series, sign);
      return {
        sign,
        unstable,
        interpretationSign: interpret && !unstable ? sign : null,
        house: null,
      };
    }
    const lagna =
      center.lagna === null ? null : placement('lagna', center.lagna);
    if (lagna?.interpretationSign) lagna.house = 1;
    const positions = { lagna } as Chart['positions'];
    for (const key of Object.keys(center) as Point[]) {
      if (key === 'lagna') continue;
      const p = placement(key, center[key]);
      if (p.interpretationSign && lagna?.interpretationSign)
        p.house = ((p.sign - lagna.sign + 12) % 12) + 1;
      positions[key] = p;
    }
    charts[method.chart] = {
      read_access: method.access,
      candidate: method.chart === 'D60',
      convention: {
        methodId: method.id,
        ayanamsaId: 'lahiri',
        houseSystem: 'whole-sign',
        ephemerisFlag: flag,
        timePrecision: precision,
      },
      positions,
    };
  }
  return charts;
}
