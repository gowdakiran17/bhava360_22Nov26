import { utcAtJulianDay } from '@bhava360/core';

export interface SolarDay {
  sunrise: number | null;
  sunset: number | null;
  weekday: number;
  date: string;
}
export const interval = (start: number, end: number) => ({
  startUtc: utcAtJulianDay(start),
  endUtc: utcAtJulianDay(end),
});
export interface WindowTables {
  abhijit: [number, number];
  brahma: [number, number];
  hora_cycle: string[];
  choghadiya_order: string[];
  night_cycle: string[];
  day_first_sun_through_sat: string[];
  night_first_sun_through_sat: string[];
  day_step: number;
  night_step: number;
}

export function dayWindows(
  day: SolarDay,
  previousSet: number | null,
  nextRise: number | null,
  table: WindowTables,
  eighths: Record<'rahu' | 'yamaganda' | 'gulika', number[]>,
  varaLords: Record<string, string>,
) {
  const { sunrise: rise, sunset: set, weekday: w } = day;
  if (
    previousSet === null ||
    rise === null ||
    set === null ||
    nextRise === null ||
    !(previousSet < rise && rise < set && set < nextRise)
  )
    return null;

  function slot(a: number, b: number, j: number, n: number) {
    return interval(a + ((j - 1) * (b - a)) / n, a + (j * (b - a)) / n);
  }
  const hora = table.hora_cycle;
  const first = hora.indexOf(
    varaLords[
      [
        'sunday',
        'monday',
        'tuesday',
        'wednesday',
        'thursday',
        'friday',
        'saturday',
      ][w]
    ],
  );
  function choghadiya(
    a: number,
    b: number,
    cycle: string[],
    label: string,
    step: number,
  ) {
    const index = cycle.indexOf(label);
    return Array.from({ length: 8 }, (_, i) => ({
      ...slot(a, b, i + 1, 8),
      label: cycle[(index + i * step) % cycle.length],
    }));
  }
  return {
    rahuKaal: slot(rise, set, eighths.rahu[w], 8),
    yamaganda: slot(rise, set, eighths.yamaganda[w], 8),
    gulika: slot(rise, set, eighths.gulika[w], 8),
    abhijit: slot(rise, set, ...table.abhijit),
    brahma: slot(previousSet, rise, ...table.brahma),
    hora: Array.from({ length: 24 }, (_, i) => ({
      ...(i < 12
        ? slot(rise, set, i + 1, 12)
        : slot(set, nextRise, i - 11, 12)),
      lord: hora[(first + i) % hora.length],
    })),
    choghadiya: {
      day: choghadiya(
        rise,
        set,
        table.choghadiya_order,
        table.day_first_sun_through_sat[w],
        table.day_step,
      ),
      night: choghadiya(
        set,
        nextRise,
        table.night_cycle,
        table.night_first_sun_through_sat[w],
        table.night_step,
      ),
    },
  };
}
