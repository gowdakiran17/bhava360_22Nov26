import type { EphemerisPort } from '@bhava360/core';
import type { Catalogue } from './catalogue';
import { lunarSeed, lunarTimeline, type BirthDashaInput } from './dasha-common';

export interface YoginiInput extends BirthDashaInput {
  yearClock?: 'mean-gregorian' | 'savana';
}
export function computeYogini(
  port: EphemerisPort,
  kb: Catalogue,
  input: YoginiInput,
) {
  const table = kb.resources['vedic/dashas/yogini/periods.yaml'];
  const yearClock: YoginiInput['yearClock'] =
    input.yearClock ?? table.default_year;
  const yearDays = Number(table.year_days[String(yearClock)]);
  if (!Number.isFinite(yearDays))
    throw new RangeError('Unknown Yogini year clock');
  const { epoch, star, fraction, stable, flag } = lunarSeed(
    port,
    input,
    table.star_width_arcseconds,
  );
  const order: string[] = table.lord_order;
  const first = (star + 3) % order.length;
  const lord = order[first];
  const convention = {
    variantId: 'vedic.dashas-yogini.balance-calculation',
    yearClock,
    yearDays,
    seed: stable ? { nakshatra: star + 1, lord } : null,
    timePrecision: input.timePrecision,
    workingInstantUtc: epoch.utc,
    timeZone: input.timeZone,
    ephemerisFlag: flag,
    ayanamsaId: 'lahiri',
  };
  if (!stable) return { convention, birthBalance: null, timeline: null };
  const years = table.sequence[lord],
    elapsedYears = years * fraction;
  return {
    convention,
    birthBalance: { lord, elapsedYears, remainingYears: years - elapsedYears },
    timeline: lunarTimeline(
      epoch.jdUt - elapsedYears * yearDays,
      yearDays,
      first,
      order,
      table.sequence,
      table.cycle_years,
      1,
    ),
  };
}
