import { readFileSync } from 'node:fs';
import { beforeAll, expect, it } from 'vitest';
import { createSwissEphemeris } from '../../packages/ephemeris-swiss/src';
import { createVedicEngine } from '../../packages/engine-vedic/src';
import { loadCatalogue } from '../../packages/engine-vedic/src/catalogue';
import { vargaSign, type Point } from '../../packages/engine-vedic/src/vargas';
import births from './vedic.json';
import golden from './vargas.json';

let engine: ReturnType<typeof createVedicEngine>;
beforeAll(async () => {
  engine = createVedicEngine(await createSwissEphemeris());
});

it.each(golden.fixtures)(
  'matches every $name ($precision) varga and sensitivity flag',
  (fixture) => {
    const f = births.fixtures.find(
      (b) => b.name === fixture.name && b.precision === fixture.precision,
    )!;
    const facts = engine.computeFacts({
      birthInstantUtc: f.utc.replace('+00:00', 'Z'),
      timeZone: f.timeZone,
      timePrecision: f.precision === 'unknown' ? 'unknown' : 'known',
      latitude: f.latitude,
      longitude: f.longitude,
    });
    const rows = [];
    expect(Object.keys(facts.vargas).sort()).toEqual(
      Object.keys(fixture.charts).sort(),
    );
    for (const [id, reference] of Object.entries(fixture.charts)) {
      const chart = facts.vargas[id];
      const held = id === 'D60';
      expect(chart.candidate).toBe(held);
      expect(chart.read_access).toBe(
        held ? 'held' : ['D1', 'D9', 'D10'].includes(id) ? 'MVP' : 'R2',
      );
      expect(chart.convention).toEqual({
        methodId:
          golden.provenance.methodIds[
            id as keyof typeof golden.provenance.methodIds
          ],
        ayanamsaId: 'lahiri',
        ephemerisFlag: 'SEFLG_MOSEPH',
        houseSystem: 'whole-sign',
        timePrecision: f.precision,
      });
      if (f.precision === 'unknown') expect(chart.positions.lagna).toBeNull();
      const unstable: string[] = reference.unstable;
      for (const [body, expected] of Object.entries<number>(reference.signs)) {
        const p = chart.positions[body as Point]!;
        const usable =
          !held && f.precision !== 'unknown' && !unstable.includes(body);
        expect(p.sign).toBe(expected);
        expect(p.unstable).toBe(unstable.includes(body));
        expect(p.interpretationSign).toBe(usable ? expected : null);
        const rising = chart.positions.lagna?.interpretationSign;
        expect(p.house).toBe(
          usable && rising ? ((expected - rising + 12) % 12) + 1 : null,
        );
        rows.push({
          fixture: f.name + ' ' + f.precision,
          chart: id,
          body,
          computed: p.sign,
          independent: expected,
          agreement: p.sign === expected,
        });
      }
    }
    // Tab-separated rows avoid console.table's row truncation in benchmark logs.
    console.log(
      'fixture\tchart\tbody\tcomputed\tindependent\tagreement\n' +
        rows.map((r) => Object.values(r).join('\t')).join('\n'),
    );
  },
);

it('assigns whole degrees and both sides of every exported cell boundary', () => {
  const data = JSON.parse(
    readFileSync(
      new URL('../../kb/dist-json/admin/vedic.json', import.meta.url),
      'utf8',
    ),
  );
  const records = data.resources['vedic/vargas/methods.yaml'].methods;
  const signs =
    'aries taurus gemini cancer leo virgo libra scorpio sagittarius capricorn aquarius pisces'.split(
      ' ',
    );
  let comparisons = 0;
  for (const method of loadCatalogue().methods) {
    const ref = records.find(
      (r: { chart: string }) => r.chart === method.chart,
    );
    const cells = signs.flatMap((name, s) => {
      const row: string[] = ref.sign_lookup[name];
      const bounds = ref.degree_boundaries;
      return row.map((target, i) => ({
        start: bounds.equal_parts
          ? (30 * (s * row.length + i)) / row.length
          : s * 30 + (s % 2 ? bounds.even : bounds.odd)[i],
        sign: signs.indexOf(target) + 1,
      }));
    });
    for (const [i, c] of cells.entries()) {
      expect(vargaSign(method, c.start)).toBe(c.sign);
      expect(vargaSign(method, c.start + 1e-9)).toBe(c.sign);
      expect(vargaSign(method, c.start - 1e-9)).toBe(
        cells[(i + cells.length - 1) % cells.length].sign,
      );
      comparisons += 3;
    }
    let index = 0;
    for (let lon = 0; lon < 360; lon++) {
      while (index + 1 < cells.length && cells[index + 1].start <= lon) index++;
      for (const shifted of [lon, lon - 360, lon + 360]) {
        expect(vargaSign(method, shifted)).toBe(cells[index].sign);
        comparisons++;
      }
    }
  }
  console.log('Varga boundary and whole-degree comparisons:', comparisons);
});

it('suppresses a placement that returns across the same edge between samples', () => {
  const f = births.fixtures[0];
  const stationary = createVedicEngine({
    riseSet: () => null,
    ascendant: () => 10,
    lahiriAyanamsa: () => 24,
    longitude(jd, body) {
      const t = ((jd - f.julianDay) * 86400 - 15) / 15;
      return {
        longitude: body === 'mercury' ? 15.001 - 0.002 * t * t : 4,
        speed: body === 'mercury' ? (-0.004 * t * 86400) / 15 : 0,
        flag: 'SEFLG_MOSEPH',
      };
    },
  });
  const { vargas } = stationary.computeFacts({
    birthInstantUtc: f.utc.replace('+00:00', 'Z'),
    timeZone: f.timeZone,
    latitude: f.latitude,
    longitude: f.longitude,
    timePrecision: 'known',
  });
  expect(vargas.D2.positions.mercury).toMatchObject({
    sign: 5,
    unstable: true,
    interpretationSign: null,
    house: null,
  });
});
