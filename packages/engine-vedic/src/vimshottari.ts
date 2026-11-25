import type { EphemerisPort } from '@bhava360/core';
import type { Catalogue, YearClock } from './catalogue';
import { lunarSeed, lunarTimeline, type BirthDashaInput } from './dasha-common';
export type { Period } from './dasha-common';
export interface VimshottariInput extends BirthDashaInput {
  yearClock?: YearClock;
  includeSookshma?: boolean;
}

export function computeVimshottari(
  port: EphemerisPort,
  kb: Catalogue,
  input: VimshottariInput,
) {
  const table = kb.periods;
  const { timeZone, timePrecision, yearClock = table.default_year } = input;
  const yearDays = Number(table.year_days[yearClock]);
  if (!Number.isFinite(yearDays)) throw new RangeError('Unknown dasha clock');
  const { epoch, star, stable, fraction, flag } = lunarSeed(
    port,
    input,
    table.star_width_arcseconds,
  );
  const convention = {
    yearClock,
    yearDays,
    timePrecision,
    timeZone,
    ayanamsaId: 'lahiri',
    siderealMode: 1,
    ephemerisFlag: flag,
    workingInstantUtc: epoch.utc,
  };
  if (!stable) return { convention, birthBalance: null, timeline: null };
  const order = table.lord_order;
  const first = order.indexOf(kb.nakshatras[star].lord);
  if (first < 0) throw new Error('Unknown birth nakshatra lord');
  const years = table.sequence[order[first]];
  const elapsedYears = years * fraction;
  const origin = epoch.jdUt - elapsedYears * yearDays;
  const maxDepth = input.includeSookshma ? 3 : 2;
  return {
    convention,
    birthBalance: {
      lord: order[first],
      elapsedYears,
      remainingYears: years - elapsedYears,
    },
    timeline: lunarTimeline(
      origin,
      yearDays,
      first,
      order,
      table.sequence,
      table.cycle_years,
      maxDepth,
    ),
  };
}
