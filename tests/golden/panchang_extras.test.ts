import { beforeAll, expect, it } from 'vitest';
import { createSwissEphemeris } from '../../packages/ephemeris-swiss/src';
import { createVedicEngine } from '../../packages/engine-vedic/src';
import {
  lunarCalendar,
  sunriseTithis,
} from '../../packages/engine-vedic/src/lunar-calendar';
import ref from './panchang_extras.json';

let engine: ReturnType<typeof createVedicEngine>;
beforeAll(async () => {
  engine = createVedicEngine(await createSwissEphemeris());
});
function near(actual: string | null, expected: number | null, tolerance = 1) {
  if (expected === null) {
    expect(actual).toBeNull();
    return;
  }
  expect(actual).not.toBeNull();
  expect(Math.abs(Date.parse(actual!) / 1000 - expected)).toBeLessThanOrEqual(
    tolerance,
  );
}
function checkSpan(
  actual: { startUtc: string; endUtc: string },
  edges: number[],
  i = 0,
) {
  near(actual.startUtc, edges[i]);
  near(actual.endUtc, edges[i + 1]);
}
for (const row of ref.rows) {
  for (const calendarProfile of ['amanta', 'purnimanta'] as const) {
    it(row.label + ' / ' + calendarProfile, () => {
      const result = engine.computePanchang({ ...row, calendarProfile });
      near(result.moonriseUtc, row.moonrise, 60);
      near(result.moonsetUtc, row.moonset, 60);
      expect(result.convention).toMatchObject({
        calendarProfile,
        timeZone: row.timeZone,
        latitude: row.latitude,
        longitude: row.longitude,
        sunriseMethod: 'apparent-upper-limb',
        ephemerisFlag: 'SEFLG_MOSEPH',
      });
      expect(result.sunriseTithis).toEqual(row.anomaly);
      expect(result.masa).toMatchObject({
        profile: calendarProfile,
        kind: row.kind,
        lunationNames: row.names,
        name:
          calendarProfile === 'purnimanta'
            ? row.purnimanta
            : row.names.length === 1
              ? row.names[0]
              : null,
      });
      near(result.masa.startUtc, row.start);
      near(result.masa.endUtc, row.end);
      expect(result.masa.ingresses).toHaveLength(
        { ordinary: 1, adhika: 0, kshaya: 2 }[
          row.kind as 'ordinary' | 'adhika' | 'kshaya'
        ],
      );
      expect(result.festivals.map((f) => f.id).sort()).toEqual(
        row.festivals[calendarProfile],
      );
      for (const f of result.festivals) {
        expect(f.date).toBe(row.date);
        if (f.endUtc)
          expect(Date.parse(f.endUtc)).toBeGreaterThan(Date.parse(f.startUtc));
      }
      if (!row.windows) {
        expect(result.windows).toBeNull();
        return;
      }
      const windows = result.windows!,
        gold = row.windows;
      for (const key of [
        'rahuKaal',
        'yamaganda',
        'gulika',
        'abhijit',
        'brahma',
      ] as const)
        checkSpan(windows[key], gold[key]);
      expect(windows.hora.map((h) => h.lord)).toEqual(gold.lords);
      windows.hora.forEach((h, i) => checkSpan(h, gold.hours, i));
      for (const side of ['day', 'night'] as const) {
        expect(windows.choghadiya[side].map((c) => c.label)).toEqual(
          gold[(side + 'Labels') as 'dayLabels' | 'nightLabels'],
        );
        windows.choghadiya[side].forEach((c, i) => checkSpan(c, gold[side], i));
      }
    });
  }
}
it('counts an ingress on the opening new moon and excludes one on the closing new moon', () => {
  const epoch = 2451545;
  const angle = (t: number, rate: number) =>
    ((((t - epoch) * rate) % 360) + 360) % 360;
  const names = Array.from({ length: 12 }, (_, i) => String(i + 1));
  const cal = lunarCalendar(
    (t) => angle(t, 12),
    (t) => angle(t, 1),
    names,
    'amanta',
  );
  expect(cal.month(epoch)).toMatchObject({
    kind: 'ordinary',
    name: '1',
    ingresses: [{ enteredSign: 1 }],
  });
  expect(cal.month(epoch + 30)).toMatchObject({
    kind: 'ordinary',
    name: '2',
    ingresses: [{ enteredSign: 2 }],
  });
});
it('unwraps a skipped Pratipada and distinguishes a repeated sunrise tithi', () => {
  expect(sunriseTithis(1, 2, (t) => (t === 1 ? 356 : 14))).toEqual({
    first: 30,
    next: 2,
    kind: 'kshaya',
    skipped: [1],
  });
  expect(sunriseTithis(1, 2, (t) => (t === 1 ? 121 : 131))).toEqual({
    first: 11,
    next: 11,
    kind: 'adhika',
    skipped: [],
  });
});
