import { beforeAll, expect, it } from 'vitest';
import { createSwissEphemeris } from '../../packages/ephemeris-swiss/src';
import { createVedicEngine } from '../../packages/engine-vedic/src';
import type { EphemerisPort } from '../../packages/core/src';
import reference from './yogini_chara.json';

let port: EphemerisPort, engine: ReturnType<typeof createVedicEngine>;
beforeAll(async () => {
  port = await createSwissEphemeris();
  engine = createVedicEngine(port);
});
const clocks = {
  'mean-gregorian': 365.2425,
  savana: 360,
  'julian-365.25': 365.25,
};
function near(utc: string, jd: number) {
  expect(
    Math.abs(Date.parse(utc) / 86400000 + 2440587.5 - jd) * 86400,
  ).toBeLessThan(1);
}
const order = [
  'Mangala',
  'Pingala',
  'Dhanya',
  'Bhramari',
  'Bhadrika',
  'Ulka',
  'Siddha',
  'Sankata',
];
for (const row of reference.rows) {
  const input = {
    ...row,
    timePrecision: row.timePrecision as 'known' | 'unknown',
  };
  for (const clock of ['mean-gregorian', 'savana'] as const) {
    it(row.label + ' Yogini ' + clock, () => {
      const result = engine.computeYogini(
        clock === 'mean-gregorian' ? input : { ...input, yearClock: clock },
      );
      const year = clocks[clock];
      expect(result.convention).toMatchObject({
        variantId: 'vedic.dashas-yogini.balance-calculation',
        yearClock: clock,
        yearDays: year,
      });
      if (!row.yogini) {
        expect(result.timeline).toBeNull();
        expect(result.birthBalance).toBeNull();
        expect(result.convention.seed).toBeNull();
        return;
      }
      const gold = row.yogini;
      expect(result.convention.seed?.nakshatra).toBe(gold.star);
      expect(result.birthBalance?.lord).toBe(gold.majors[0][0]);
      expect(result.birthBalance?.elapsedYears).toBeCloseTo(gold.elapsed, 7);
      expect(result.birthBalance?.remainingYears).toBeCloseTo(gold.balance, 7);
      expect(result.timeline).toHaveLength(8);
      gold.majors.forEach(([lord, left, right], i) => {
        const major = result.timeline![i],
          start = row.jd + Number(left) * year;
        expect(major.lord).toBe(lord);
        near(major.startUtc, start);
        near(major.endUtc, row.jd + Number(right) * year);
        let parts = 0;
        expect(major.children).toHaveLength(8);
        major.children!.forEach((child, j) => {
          const index = (order.indexOf(major.lord) + j) % 8;
          expect(child.lord).toBe(order[index]);
          near(
            child.startUtc,
            start + (parts / 36) * (Number(right) - Number(left)) * year,
          );
          parts += index + 1;
          near(
            child.endUtc,
            start + (parts / 36) * (Number(right) - Number(left)) * year,
          );
          if (j > 0) expect(child.startUtc).toBe(major.children![j - 1].endUtc);
        });
        expect(major.children!.at(-1)!.endUtc).toBe(major.endUtc);
      });
    });
  }
  for (const clock of ['julian-365.25', 'mean-gregorian', 'savana'] as const) {
    it(row.label + ' Chara ' + clock, () => {
      const result = engine.computeChara(
        clock === 'julian-365.25' ? input : { ...input, yearClock: clock },
      );
      const year = clocks[clock];
      expect(result.convention).toMatchObject({
        variantId: 'pyjhora-kn-rao-candidate-v1',
        yearClock: clock,
        yearDays: year,
        seed: row.seed,
      });
      if (!row.chara) {
        expect(result.timeline).toBeNull();
        return;
      }
      expect(result.timeline).toHaveLength(row.chara.length);
      row.chara.forEach((g, i) => {
        const major = result.timeline![i],
          years = g.end - g.start;
        expect(major).toMatchObject({
          sign: g.sign,
          lord: g.lord,
          cycle: g.cycle,
          years,
        });
        near(major.startUtc, row.jd + g.start * year);
        near(major.endUtc, row.jd + g.end * year);
        if (i > 0) expect(major.startUtc).toBe(result.timeline![i - 1].endUtc);
        expect(major.children.map((c) => c.sign)).toEqual(g.children);
        major.children.forEach((child, j) => {
          expect(child).toMatchObject({
            verification: 'unverified',
            visibility: 'admin-only',
          });
          near(child.startUtc, row.jd + (g.start + (years * j) / 12) * year);
          near(
            child.endUtc,
            row.jd + (g.start + (years * (j + 1)) / 12) * year,
          );
        });
        expect(major.children[11].endUtc).toBe(major.endUtc);
      });
    });
  }
}

const probe = { ...reference.rows[0], timePrecision: '±5 min' as const };
it('withholds Chara at a rising-sign boundary even for a known instant', () => {
  const crossing = createVedicEngine({
    ...port,
    ascendant: (t) => (t < probe.jd ? 29.9 : 30.1),
  });
  expect(crossing.computeChara(probe)).toMatchObject({
    withheld: 'lagna-unstable',
    timeline: null,
  });
});
it('withholds a Yogini balance across a mansion boundary', () => {
  const crossing = createVedicEngine({
    ...port,
    longitude: (t) => ({
      longitude: t < probe.jd ? 79.99 : 80.01,
      speed: 12,
      flag: 'SEFLG_MOSEPH',
    }),
  });
  expect(crossing.computeYogini(probe)).toMatchObject({
    timeline: null,
    birthBalance: null,
  });
});
it('withholds an unresolved co-lord ranking', () => {
  const tie = createVedicEngine({
    ...port,
    ascendant: () => 2,
    longitude: (_t, body) => ({
      longitude: body === 'meanNode' ? 183 : 3,
      speed: 0,
      flag: 'SEFLG_MOSEPH',
    }),
  });
  expect(tie.computeChara(probe)).toMatchObject({
    withheld: 'dual-lord-tie',
    timeline: null,
  });
});
it('rejects a clock outside the Yogini profile', () => {
  expect(() =>
    engine.computeYogini({ ...probe, yearClock: 'julian-365.25' as 'savana' }),
  ).toThrow('clock');
});
