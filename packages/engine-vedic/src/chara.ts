import {
  utcAtJulianDay,
  type EphemerisPort,
  type ClassicalPlanet,
} from '@bhava360/core';
import type { Catalogue, YearClock } from './catalogue';
import { birthWindow, type BirthDashaInput } from './dasha-common';
import { mod, planets } from './strength-chart';

export interface CharaInput extends BirthDashaInput {
  latitude: number;
  longitude: number;
  nodeType?: 'mean' | 'true';
  yearClock?: YearClock;
}
interface Sign {
  id: string;
  lord: ClassicalPlanet;
}
interface Dignity {
  exaltation: string;
  debilitation: string;
}
interface CharaMajor {
  sign: string;
  lord: string;
  cycle: number;
  years: number;
  startUtc: string;
  endUtc: string;
  children: {
    sign: string;
    startUtc: string;
    endUtc: string;
    verification: 'unverified';
    visibility: 'admin-only';
  }[];
}
function connected(source: number, target: number) {
  if (source === target) return true;
  const a = source % 3,
    b = target % 3;
  if (a === 2 || b === 2) return a === b;
  const offset = mod(source - target, 12);
  return a !== b && offset !== 1 && offset !== 11;
}
// The two dual signs use the period-specific last comparison, before the first-pass cap.
function resolvePeriod(
  sign: number,
  signs: Sign[],
  positions: Record<string, number>,
  dignities: Record<string, Dignity>,
  step: number,
) {
  const usual = signs[sign].lord;
  function adjustment(lord: string) {
    const dignity = dignities[lord],
      occupied = signs[positions[lord]].id;
    return (
      Number(occupied === dignity?.exaltation) -
      Number(occupied === dignity?.debilitation)
    );
  }
  function years(lord: string) {
    return (mod(step * (positions[lord] - sign), 12) || 12) + adjustment(lord);
  }
  function rank(lord: string) {
    const occupied = positions[lord];
    const companions = Object.entries(positions).filter(
      ([body, s]) => body !== lord && s === occupied,
    ).length;
    const support = ['jupiter', 'mercury', signs[occupied].lord].filter(
      (body) => connected(positions[body], occupied),
    ).length;
    return [
      companions,
      support,
      Number(adjustment(lord) > 0),
      occupied % 3,
      years(lord),
    ];
  }
  let lord: string = usual;
  const other =
    signs[sign].id === 'scorpio'
      ? 'ketu'
      : signs[sign].id === 'aquarius'
        ? 'rahu'
        : null;
  if (other) {
    if (positions[usual] === sign)
      lord = positions[other] === sign ? usual : other;
    else if (positions[other] !== sign) {
      const a = rank(usual),
        b = rank(other);
      const i = a.findIndex((v, j) => v !== b[j]);
      if (i < 0) return null;
      lord = a[i] > b[i] ? usual : other;
    }
  }
  return { lord, years: years(lord) };
}
export function computeChara(
  port: EphemerisPort,
  kb: Catalogue,
  input: CharaInput,
) {
  const table = kb.resources['vedic/dashas/chara/periods.yaml'];
  const signs: Sign[] = kb.resources['vedic/signs/catalog.yaml'].signs;
  const dignities = kb.resources['vedic/dignity/sign-dignities.yaml'].grahas;
  const yearClock: YearClock = input.yearClock ?? table.default_year;
  const yearDays = Number(table.year_days[yearClock]);
  if (!Number.isFinite(yearDays))
    throw new RangeError('Unknown Chara year clock');
  const { latitude, longitude, nodeType = 'mean' } = input;
  if (
    !Number.isFinite(latitude) ||
    Math.abs(latitude) > 90 ||
    !Number.isFinite(longitude) ||
    Math.abs(longitude) > 180 ||
    !['mean', 'true'].includes(nodeType)
  )
    throw new RangeError('Invalid birthplace or node type');
  const { epoch, bounds } = birthWindow(input);
  const base = {
    variantId: table.profile as string,
    yearClock,
    yearDays,
    workingInstantUtc: epoch.utc,
    timeZone: input.timeZone,
    timePrecision: input.timePrecision,
    nodeType,
    ayanamsaId: 'lahiri',
    houseSystem: 'whole-sign',
  };
  function withheld(reason: string, seed: string | null = null) {
    return { convention: { ...base, seed }, timeline: null, withheld: reason };
  }
  if (
    input.timePrecision === 'unknown' ||
    input.timePrecision === '±1 h' ||
    Math.abs(latitude) === 90
  )
    return withheld('lagna-unavailable');
  function ascSign(t: number) {
    try {
      return Math.floor(port.ascendant(t, latitude, longitude, 'lahiri') / 30);
    } catch (error) {
      if (
        error instanceof RangeError &&
        error.message === 'Ascendant unavailable'
      )
        return NaN;
      throw error;
    }
  }
  const seed = ascSign(epoch.jdUt);
  if (!signs[seed]) return withheld('lagna-unavailable');
  // Include both endpoints and the interior, including fast motion at high latitudes.
  const count = Math.ceil((bounds[1] - bounds[0]) * 2880);
  for (let i = 0; i <= count; i++) {
    if (ascSign(bounds[0] + ((bounds[1] - bounds[0]) * i) / count) !== seed)
      return withheld('lagna-unstable');
  }
  const positions: Record<string, number> = {};
  const node = port.longitude(
    epoch.jdUt,
    nodeType === 'mean' ? 'meanNode' : 'trueNode',
    'lahiri',
  );
  positions.rahu = Math.floor(node.longitude / 30);
  positions.ketu = (positions.rahu + 6) % 12;
  for (const planet of planets) {
    const value = port.longitude(epoch.jdUt, planet, 'lahiri');
    if (value.flag !== node.flag)
      throw new Error('Mixed ephemerides in Chara chart');
    positions[planet] = Math.floor(value.longitude / 30);
  }
  const foot = (s: number) =>
    table.even_footed.includes(signs[s].id) ? -1 : 1;
  const step = foot((seed + 8) % 12);
  const order = Array.from({ length: 12 }, (_, i) => mod(seed + i * step, 12));
  const timeline: CharaMajor[] = [];
  let elapsed = 0;
  const instant = (years: number) =>
    utcAtJulianDay(epoch.jdUt + years * yearDays);
  const resolved = order.map((sign) =>
    resolvePeriod(sign, signs, positions, dignities, foot(sign)),
  );
  if (resolved.some((value) => value === null))
    return withheld('dual-lord-tie', signs[seed].id);
  for (let cycle = 1; cycle <= table.cycles; cycle++) {
    for (const [i, s] of order.entries()) {
      const period = resolved[i]!;
      const first = Math.min(table.first_pass_max_years, period.years);
      const years = cycle === 1 ? first : 12 - first;
      if (!years) continue;
      const sign = signs[s].id,
        antarStep = table.antar_forward.includes(sign) ? 1 : -1;
      const children: CharaMajor['children'] = Array.from(
        { length: 12 },
        (_, j) => ({
          sign: signs[mod(s + (j + 1) * antarStep, 12)].id,
          startUtc: instant(elapsed + (years * j) / 12),
          endUtc: instant(elapsed + (years * (j + 1)) / 12),
          verification: 'unverified',
          visibility: 'admin-only',
        }),
      );
      timeline.push({
        sign,
        lord: period.lord,
        cycle,
        years,
        startUtc: instant(elapsed),
        endUtc: instant(elapsed + years),
        children,
      });
      elapsed += years;
    }
  }
  return {
    convention: { ...base, ephemerisFlag: node.flag, seed: signs[seed].id },
    timeline,
    withheld: null,
  };
}
