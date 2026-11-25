import { beforeAll, it, expect } from 'vitest';
import { createVedicEngine } from '../../packages/engine-vedic/src';
import { createSwissEphemeris } from '../../packages/ephemeris-swiss/src';
import type { EphemerisPort } from '../../packages/core/src';
import reference from './strength_yogas.json';

let port: EphemerisPort, engine: ReturnType<typeof createVedicEngine>;
beforeAll(async () => {
  port = await createSwissEphemeris();
  engine = createVedicEngine(port);
});
for (const f of reference.fixtures) {
  it('reproduces the independent strength worksheet for ' + f.name, () => {
    const input = { ...f, timePrecision: 'known' as const };
    const { admin, public: words } = engine.computeStrength(input);
    expect(admin.convention.published_raman).toBe('unverified');
    for (const [g, expected] of Object.entries(f.shadbala)) {
      for (const [k, n] of Object.entries(expected))
        expect(
          admin.shadbala[g][k as keyof typeof expected],
          g + ' ' + k,
        ).toBeCloseTo(n, 5);
      const p = admin.ashtakavarga!.bav[g];
      expect([p.rashiPinda, p.grahaPinda, p.shodhyaPinda]).toEqual(
        f.pinda[g as keyof typeof f.pinda],
      );
    }
    expect(admin.ashtakavarga!.total).toBe(337);
    expect(admin.ashtakavarga!.sav).toEqual(f.sav);
    const sripati = engine.computeStrength({
      ...input,
      variants: { bhava: 'sripati' },
    }).admin.bhavaBala!;
    for (let i = 0; i < 12; i++) {
      expect(admin.bhavaBala![i].total).toBeCloseTo(
        f.houses['whole-sign-middle'][i],
        5,
      );
      expect(sripati[i].total).toBeCloseTo(f.houses.sripati[i], 5);
    }
    for (const [g, row] of Object.entries(admin.planetGrades))
      expect(words.planets[g] === null).toBe(row === null);
    for (const label of [
      ...Object.values(words.planets),
      ...words.houses!,
    ].filter((x) => x !== null)) {
      expect(Object.keys(label!).sort()).toEqual(['en', 'hi', 'kn', 'tone']);
      expect(['well supported', 'steady', 'modest']).toContain(label!.en);
    }
    expect(Object.keys(admin.yogas)).toHaveLength(82);
    for (const [id, formed] of Object.entries(f.formed))
      expect(admin.yogas[id].formed, id).toBe(formed);
  });
}
const base = () => ({
  ...reference.fixtures[0],
  timePrecision: 'known' as const,
});
function engineWith(changes: Record<string, number>) {
  return createVedicEngine({
    ...port,
    longitude(jd, body, frame) {
      const p = port.longitude(jd, body, frame);
      return { ...p, longitude: changes[body] ?? p.longitude };
    },
  });
}
it('resolves the Moon, Mercury and Venus shared endpoints', () => {
  for (const [v, d, alt] of [
    [180, 'moolatrikona', 'moolatrikona'],
    [185, 'moolatrikona', 'own-sign'],
    [194.99, 'moolatrikona', 'own-sign'],
    [195, 'own-sign', 'own-sign'],
  ] as const) {
    const e = engineWith({ venus: v, moon: 33, mercury: 165 });
    expect(e.computeStrength(base()).admin.dignity).toMatchObject({
      venus: d,
      moon: 'exaltation-peak',
      mercury: 'exaltation-peak',
    });
    expect(
      e.computeStrength({
        ...base(),
        variants: { venus: 'saravali-five-degrees' },
      }).admin.dignity.venus,
    ).toBe(alt);
  }
});
it('withholds Lagna and sunrise-time strength for Dev unknown', () => {
  const f = reference.fixtures.at(-1)!;
  const { admin } = engine.computeStrength({ ...f, timePrecision: 'unknown' });
  expect([
    admin.bhavaBala,
    admin.ashtakavarga,
    admin.shadbala.sun.sthana,
    admin.shadbala.sun.dig,
    admin.shadbala.sun.kala,
    admin.doshas['mars-partnership'].formed,
  ]).toEqual(Array(6).fill(null));
  expect(admin.yogas['vedic.yogas.hamsa'].formed).toBeNull();
});

it('keeps the two Drik and war profiles separate and withholds ties', () => {
  const coords = {
    sun: 260,
    moon: 80,
    mercury: 120,
    mars: 120.4,
    jupiter: 2,
    venus: 174,
    saturn: 292,
  };
  const e = engineWith(coords);
  const normal = e.computeStrength(base()).admin;
  const classical = e.computeStrength({
    ...base(),
    variants: { drik: 'fixed-segment', yuddha: 'classical-disc-difference' },
  }).admin;
  const [a, b] = ['mercury', 'mars'].map((p) => classical.shadbala[p]);
  const jd = Date.parse(base().birthInstantUtc) / 86400000 + 2440587.5;
  const diameter = (g: 'mercury' | 'mars') =>
    port.strengthPosition(jd, g).discArcminutes!;
  const preWar = (row: typeof a) => row.sthana! + row.dig! + row.kalaBase!;
  const transfer =
    Math.abs(preWar(a) - preWar(b)) /
    Math.abs(diameter('mercury') - diameter('mars'));
  expect(Math.abs(a.yuddha!)).toBeCloseTo(transfer, 7);
  expect(a.yuddha).toBeCloseTo(-b.yuddha!, 7);
  expect(a.yuddha).not.toBe(normal.shadbala.mercury.yuddha);
  expect(a.drik).not.toBe(normal.shadbala.mercury.drik);
  const overlap = engineWith({ ...coords, venus: 120.2 }).computeStrength(
    base(),
  ).admin.shadbala;
  expect(overlap.mars.yuddha).toBeNull();
  expect(overlap.mercury.total).toBeNull();
});
it('binds Moon phase, Mercury associates and the Moon BAV edition', () => {
  const input = base(),
    e = engineWith({
      sun: 0,
      moon: 270,
      mercury: 1,
      jupiter: 2,
      venus: 75,
      saturn: 95,
      mars: 210,
      meanNode: 120,
    });
  expect(e.computeStrength(input).admin.benefic).toMatchObject({
    mercury: true,
    moon: false,
  });
  expect(
    e.computeStrength({
      ...input,
      variants: { moon: 'bright-72', mercury: 'mercury-strict' },
    }).admin.benefic,
  ).toMatchObject({ mercury: false, moon: true });
  expect(
    e.computeStrength({ ...input, variants: { moon: 'raman-ashtami' } }).admin
      .benefic.moon,
  ).toBe(false);
  const a = e.computeStrength(input).admin.ashtakavarga!,
    b = e.computeStrength({ ...input, variants: { bav: 'pvr-table-20' } }).admin
      .ashtakavarga!;
  expect(b.total).toBe(337);
  expect(a.bav.moon.raw).not.toEqual(b.bav.moon.raw);
  expect(a.bav.sun).toEqual(b.bav.sun);
});
it('binds bhanga and period activation to actual participants', () => {
  const e = engineWith({ sun: 10, mercury: 17, moon: 70, mars: 253 });
  const standard = e.computeStrength(base()).admin.yogas;
  const variant = e.computeStrength({
    ...base(),
    variants: { yoga: 'mutual-full-aspect' },
  }).admin.yogas;
  expect(standard['vedic.yogas.chandra-mangala'].formed).toBe(false);
  expect(
    variant['vedic.yogas.chandra-mangala'].witnesses![0].participants,
  ).toEqual(['mars', 'moon']);
  expect(standard['vedic.yogas.budhaditya'].witnesses![0].effects).toContain(
    'soften',
  );
  const close = e.computeStrength({
    ...base(),
    variants: { yoga: 'budhaditya-close-orb' },
  }).admin.yogas;
  expect(close['vedic.yogas.budhaditya'].witnesses![0].effects).not.toContain(
    'soften',
  );
  const cancelled = engineWith({ sun: 10, mercury: 13 }).computeStrength(base())
    .admin.yogas['vedic.yogas.budhaditya'].witnesses![0];
  expect(cancelled).toMatchObject({
    active: false,
    gate: null,
    display: 'omitted',
  });
  const r = e.computeStrength(base()).admin;
  const witness = r.yogas['vedic.yogas.chandra-mangala'];
  expect(witness.witnesses).toEqual([]);
  const mercury = close['vedic.yogas.budhaditya'].witnesses![0];
  if (mercury.gate)
    expect(mercury.active).toBe(
      r.period.some((p) => ['mercury', 'sun'].includes(p)),
    );
});
it('enforces the house list and reference of each Manglik school', () => {
  const e = engineWith({ mars: 15, moon: 15 });
  const check = (
    manglik: 'rath' | 'raman' | 'library' | 'regional-lagna' | 'sgs',
    marsReference: 'lagna' | 'moon' = 'moon',
  ) =>
    e.computeStrength({ ...base(), variants: { manglik, marsReference } }).admin
      .doshas['mars-partnership'];
  expect(check('rath').formed).toBe(true);
  expect(check('raman').formed).toBe(false);
  expect(check('library').formed).toBe(true);
  expect(() => check('regional-lagna')).toThrow();
  expect(() => check('sgs')).toThrow();
  for (const profile of ['regional-lagna', 'sgs'] as const)
    expect(typeof check(profile, 'lagna').formed).toBe('boolean');
});
