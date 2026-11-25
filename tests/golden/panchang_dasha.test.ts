import { beforeAll, expect, it } from 'vitest';
import { createSwissEphemeris } from '../../packages/ephemeris-swiss/src';
import { createVedicEngine } from '../../packages/engine-vedic/src';
import type { EphemerisPort } from '../../packages/core/src';
import reference from './panchang_dasha.json';

let port: EphemerisPort, engine: ReturnType<typeof createVedicEngine>;
beforeAll(async () => {
  port = await createSwissEphemeris();
  engine = createVedicEngine(port);
});
const jd = (s: string) => Date.parse(s) / 86400000 + 2440587.5;
function near(actual: string | null, expected: number | null, seconds: number) {
  if (expected === null) expect(actual).toBeNull();
  else {
    expect(actual).not.toBeNull();
    expect(Math.abs(jd(actual!) - expected) * 86400).toBeLessThanOrEqual(
      seconds,
    );
  }
}
for (const row of reference.rows) {
  it('matches offline Panchang for ' + row.label, () => {
    const result = engine.computePanchang({
      ...row,
      sunriseMethod: row.traditional
        ? 'traditional-disc-centre'
        : 'apparent-upper-limb',
    });
    near(result.sunriseUtc, row.sunrise, 60);
    near(result.sunsetUtc, row.sunset, 60);
    expect(result.vara).toBe(row.vara);
    for (const key of ['tithi', 'nakshatra', 'yoga', 'karana'] as const) {
      const limb = result[key],
        [i, start, end] = row.limbs[key];
      expect('number' in limb ? limb.number - 1 : limb.index).toBe(i);
      near(limb.startUtc, start, 1);
      near(limb.endUtc, end, 1);
    }
    expect(result.tithi.index0).toBe(result.tithi.number - 1);
    expect(result.tithi.paksha).toBe(
      result.tithi.number <= 15 ? 'shukla' : 'krishna',
    );
    expect(result.nakshatra.id).toMatch(/^vedic\.nakshatras\./);
    expect(result.convention.ephemerisFlag).toBe('SEFLG_MOSEPH');
  });
}
for (const row of reference.rows.filter((r) =>
  ['Asha', 'Ravi', 'Meera', 'Kabir', 'Dev'].includes(r.label),
)) {
  it('matches the four active birth periods for ' + row.label, () => {
    const r = engine.computeVimshottari({
      birthInstantUtc: row.instantUtc,
      timeZone: row.timeZone,
      timePrecision: 'known',
      includeSookshma: true,
    });
    expect(r.birthBalance!.remainingYears).toBeCloseTo(row.balanceYears, 8);
    let periods = r.timeline!;
    for (const [lord, start, end] of row.active) {
      const active = periods.find(
        (p) =>
          jd(p.startUtc) <= jd(row.instantUtc) &&
          jd(row.instantUtc) < jd(p.endUtc),
      )!;
      expect(active.lord).toBe(lord);
      near(active.startUtc, Number(start), 1);
      near(active.endUtc, Number(end), 1);
      for (let i = 1; i < periods.length; i++)
        expect(periods[i].startUtc).toBe(periods[i - 1].endUtc);
      if (active.children) {
        expect(active.children[0].startUtc).toBe(active.startUtc);
        expect(active.children.at(-1)!.endUtc).toBe(active.endUtc);
        periods = active.children;
      }
    }
  });
}
it('withholds Dev on an unstable unknown-time day', () => {
  const dev = reference.rows.find((r) => r.label === 'Dev')!;
  expect(
    engine.computeVimshottari({
      birthInstantUtc: dev.instantUtc,
      timeZone: dev.timeZone,
      timePrecision: 'unknown',
    }).timeline,
  ).toBeNull();
});
it('selects the next star at its lower edge and keeps a single clock throughout', () => {
  const fixed = createVedicEngine({
    ...port,
    longitude: () => ({ longitude: 40 / 3, speed: 13, flag: 'SEFLG_MOSEPH' }),
  });
  for (const [clock, days] of [
    ['julian-365.25', 365.25],
    ['savana', 360],
    ['mean-gregorian', 365.2425],
  ] as const) {
    const input = {
      birthInstantUtc: '2000-01-01T12:00:00Z',
      timeZone: 'UTC',
      timePrecision: 'known' as const,
      yearClock: clock,
    };
    const r = fixed.computeVimshottari(input);
    expect(r.birthBalance).toEqual({
      lord: 'venus',
      elapsedYears: 0,
      remainingYears: 20,
    });
    expect(jd(r.timeline![0].startUtc)).toBe(jd(input.birthInstantUtc));
    expect(jd(r.timeline![0].endUtc) - jd(input.birthInstantUtc)).toBeCloseTo(
      20 * days,
      6,
    );
    expect(r.timeline![0].children![0].children![0].children).toBeUndefined();
  }
});

it('selects the incoming limb when a returned crossing is queried again', () => {
  const row = reference.rows[0];
  const before = engine.computePanchang(row);
  for (const key of ['karana', 'tithi', 'nakshatra', 'yoga'] as const) {
    const after = engine.computePanchang({
      ...row,
      instantUtc: before[key].endUtc,
    });
    expect(after[key].startUtc).toBe(before[key].endUtc);
    expect(after[key].name).not.toBe(before[key].name);
  }
});

it('switches lunar fortnight, fixed karana, yoga and star at a single wrapped crossing', () => {
  const epoch = 2451545;
  const fixture = createVedicEngine({
    ...port,
    longitude(at, body) {
      const degrees = (at - epoch) * 12;
      return {
        longitude: body === 'moon' ? ((degrees % 360) + 360) % 360 : 0,
        speed: body === 'moon' ? 12 : 0,
        flag: 'SEFLG_MOSEPH',
      };
    },
  });
  const location = { latitude: 0, longitude: 0, timeZone: 'UTC' };
  const after = fixture.computePanchang({
    ...location,
    instantUtc: '2000-01-01T12:00:00Z',
  });
  const before = fixture.computePanchang({
    ...location,
    instantUtc: '2000-01-01T11:59:59Z',
  });
  expect(before.tithi).toMatchObject({
    number: 30,
    index0: 29,
    paksha: 'krishna',
    name: 'Amavasya',
  });
  expect(after.tithi).toMatchObject({
    number: 1,
    index0: 0,
    paksha: 'shukla',
    name: 'Pratipada',
  });
  expect(before.karana.name).toBe('naga');
  expect(after.karana.name).toBe('kimstughna');
  expect(after.nakshatra.lord).toBe('ketu');
  expect(after.yoga.name).toBe('Vishkambha');
});
