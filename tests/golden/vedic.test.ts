import { beforeAll, describe, expect, it } from 'vitest';
import { resolveBirth } from '../../packages/core/src';
import { createSwissEphemeris } from '../../packages/ephemeris-swiss/src';
import {
  createVedicEngine,
  type VedicInput,
} from '../../packages/engine-vedic/src';
import reference from './vedic.json';

type Fixture = (typeof reference.fixtures)[number];
function input(f: Fixture): VedicInput {
  return {
    birthInstantUtc: resolveBirth(f.date, f.time, f.timeZone),
    timeZone: f.timeZone,
    latitude: f.latitude,
    longitude: f.longitude,
    timePrecision: f.precision === 'unknown' ? 'unknown' : 'known',
  };
}
let engine: ReturnType<typeof createVedicEngine>;
beforeAll(async () => {
  engine = createVedicEngine(await createSwissEphemeris());
});
const angularDelta = (a: number, b: number) =>
  Math.abs(((a - b + 540) % 360) - 180);

describe.each(reference.fixtures)('$name ($precision)', (f) => {
  it('matches the independent Swiss reference and classifies the positions', () => {
    const chart = engine.computeFacts(input(f));
    const rows: {
      fixture: string;
      quantity: string;
      computed: number;
      independent: number;
      delta: number;
      provenance: string;
    }[] = [];
    const provenance = [
      reference.provenance.binding,
      reference.provenance.library,
      chart.convention.ephemerisFlag,
      'Lahiri 1',
      'mean',
    ].join(' / ');
    function compare(
      quantity: string,
      actual: number,
      expected: number,
      tolerance: number,
      angle = false,
    ) {
      const delta = angle
        ? angularDelta(actual, expected)
        : Math.abs(actual - expected);
      rows.push({
        fixture: f.name + ' ' + f.precision,
        quantity,
        computed: actual,
        independent: expected,
        delta,
        provenance,
      });
      expect(delta, quantity).toBeLessThanOrEqual(tolerance);
    }
    compare('JD UT', chart.julianDayUt, f.julianDay, 1e-8);
    compare('ayanamsa', chart.ayanamsa, f.ayanamsa, 0.001, true);
    expect(chart.convention).toEqual({
      ayanamsaId: 'lahiri',
      siderealMode: 1,
      calendar: 'proleptic-gregorian',
      houseSystem: 'whole-sign',
      ephemerisFlag: 'SEFLG_MOSEPH',
      nodeType: 'mean',
      timePrecision: f.precision,
    });
    function checkDivision(
      p: typeof chart.grahas.sun | NonNullable<typeof chart.lagna>,
      lon: number,
    ) {
      expect(p.sign).toBe(Math.floor(lon / 30) + 1);
      const segment = Math.floor(lon / (360 / 27));
      expect(p.nakshatra.number).toBe(segment + 1);
      expect(p.nakshatra.id).toMatch(/^vedic\.nakshatras\./);
      expect(p.nakshatra.name).toBeTruthy();
      expect(p.nakshatra.lord).toBeTruthy();
      expect(p.pada).toBe(1 + (Math.floor(lon / (360 / 108)) % 4));
      expect(p.house).toBe(
        f.lagna === null
          ? null
          : ((Math.floor(lon / 30) - Math.floor(f.lagna / 30) + 12) % 12) + 1,
      );
    }
    if (f.lagna === null) expect(chart.lagna).toBeNull();
    else {
      compare('Lagna', chart.lagna!.longitude, f.lagna, 0.01, true);
      checkDivision(chart.lagna!, f.lagna);
    }
    for (const id of Object.keys(
      f.positions,
    ) as (keyof Fixture['positions'])[]) {
      const body = chart.grahas[id],
        expected = f.positions[id];
      compare(id, body.longitude, expected.longitude, 0.002, true);
      compare(id + ' speed', body.speed, expected.speed, 0.0001);
      expect(body.retrograde).toBe(expected.speed < 0);
      checkDivision(body, expected.longitude);
    }
    console.table(rows);
  });
});
it('keeps true-node selection per request and Ketu opposite Rahu', () => {
  const birth = input(reference.fixtures[0]);
  const mean = engine.computeFacts(birth),
    chosen = engine.computeFacts({ ...birth, nodeType: 'true' });
  expect(chosen.convention.nodeType).toBe('true');
  expect(chosen.grahas.rahu.longitude).not.toBeCloseTo(
    mean.grahas.rahu.longitude,
    3,
  );
  expect(
    angularDelta(chosen.grahas.rahu.longitude, chosen.grahas.ketu.longitude),
  ).toBeCloseTo(180, 9);
  expect(chosen.grahas.rahu.speed).toBe(chosen.grahas.ketu.speed);
  expect(engine.computeFacts(birth)).toEqual(mean);
});
it('uses local noon for unknown time even if supplied another working hour', () => {
  const birth = input(reference.fixtures[5]);
  expect(
    engine.computeFacts({ ...birth, birthInstantUtc: '1995-01-05T00:00:00Z' }),
  ).toEqual(engine.computeFacts(birth));
});
