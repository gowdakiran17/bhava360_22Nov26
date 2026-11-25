import type { ClassicalPlanet } from '@bhava360/core';
import type { Catalogue } from './catalogue';
import { vargaSign } from './vargas';
import type { VedicFacts } from './index';

export const planets: ClassicalPlanet[] = [
  'sun',
  'moon',
  'mars',
  'mercury',
  'jupiter',
  'venus',
  'saturn',
];
export const bodies = [...planets, 'rahu', 'ketu'] as const;
export const mod = (n: number, period = 360) =>
  ((n % period) + period) % period;
export const arc = (a: number, b: number) => Math.abs(mod(a - b + 180) - 180);
export const distance = (sign: number, origin: number) =>
  mod(sign - origin, 12) + 1;
export const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
export const mapValues = <T>(
  keys: readonly string[],
  fn: (g: string) => T,
): Record<string, T> => Object.fromEntries(keys.map((g) => [g, fn(g)]));
export const resource = (kb: Catalogue, path: string) =>
  kb.resources['vedic/' + path + '.yaml'];
export const rule = (kb: Catalogue, id: string) => kb.rules['vedic.' + id].rule;
export const calc = (kb: Catalogue, id: string) =>
  rule(kb, 'strength-shadbala.' + id).calculation;

export const defaults = {
  drik: 'interpolated-peak',
  yuddha: 'modern-kala-transfer',
  bhava: 'whole-sign-middle',
  moon: 'shukla',
  mercury: 'predominance',
  venus: 'bphs-fifteen-degrees',
  bav: 'bphs-seven-graha-337',
  yoga: 'default',
  manglik: 'library',
  marsReference: 'lagna',
} as const;
export interface StrengthOptions {
  drik?: 'interpolated-peak' | 'fixed-segment';
  yuddha?: 'modern-kala-transfer' | 'classical-disc-difference';
  bhava?: 'whole-sign-middle' | 'sripati';
  moon?: 'shukla' | 'raman-ashtami' | 'bright-72';
  mercury?: 'mercury-strict' | 'predominance';
  venus?: 'saravali-five-degrees' | 'bphs-fifteen-degrees';
  bav?: 'pvr-table-20' | 'bphs-seven-graha-337';
  yoga?: 'default' | 'mutual-full-aspect' | 'budhaditya-close-orb';
  manglik?: 'library' | 'regional-lagna' | 'raman' | 'rath' | 'sgs';
  marsReference?: 'lagna' | 'moon' | 'venus';
  regionalList?: 'lagna_five' | 'four';
}
export type Profile = Required<Omit<StrengthOptions, 'regionalList'>> &
  Pick<StrengthOptions, 'regionalList'>;

export function strengthChart(kb: Catalogue, f: VedicFacts, o: Profile) {
  const signs: { id: string; lord: string }[] = resource(
    kb,
    'signs/catalog',
  ).signs;
  const lon: Record<string, number> = Object.fromEntries(
    Object.entries(f.grahas).map(([g, p]) => [g, p.longitude]),
  );
  const sign = mapValues(bodies, (g) => Math.floor(lon[g] / 30));
  const unstable = mapValues(bodies, (g) => {
    const body = g as keyof typeof f.grahas;
    return (
      f.vargas.D1.positions[body].unstable ||
      f.vargas.D9.positions[body].unstable
    );
  });
  const asc = f.vargas.D1.positions.lagna?.unstable
    ? null
    : (f.lagna?.longitude ?? null);
  const rising = asc === null ? null : Math.floor(asc / 30);
  const dignity = resource(kb, 'dignity/sign-dignities'),
    rel = resource(kb, 'dignity/relationships');
  const natural = resource(kb, 'planets/benefic-profile'),
    orbs = resource(kb, 'states/combustion-orbs').orbs;
  const phase = mod(lon.moon - lon.sun),
    window = natural.moon.variants[o.moon];
  const benefic = mapValues(
    bodies,
    (g) => natural.always_benefic.includes(g) as boolean,
  );
  benefic.moon =
    (phase > window.lower_deg ||
      (window.lower_inclusive && phase === window.lower_deg)) &&
    (phase < window.upper_deg ||
      (window.upper_inclusive && phase === window.upper_deg));
  const companions: string[] = natural.mercury.associates.filter(
    (g: string) => sign[g] === sign.mercury,
  );
  benefic.mercury =
    o.mercury === 'mercury-strict'
      ? companions.every((g) => benefic[g])
      : sum(companions.map((g) => (benefic[g] ? 1 : -1))) >= 0;
  const friendships = mapValues(planets, (g) =>
    mapValues(planets, (other) => {
      const table = rule(kb, 'planets.' + g).graha.natural_friendships;
      const nature = table.friends.includes(other)
        ? 'friend'
        : table.enemies.includes(other)
          ? 'enemy'
          : 'neutral';
      return rel.matrix[nature][
        rel.temporary_friends.includes(distance(sign[other], sign[g]))
          ? 'friend'
          : 'enemy'
      ] as string;
    }),
  );
  function division(g: string, n: number) {
    const m = kb.methods.find((m) => m.chart === 'D' + n)!;
    return vargaSign(m, lon[g]) - 1;
  }
  function mt(g: string, s: number, deg: number) {
    const [lo, hi] =
      g === 'venus' && o.venus === 'saravali-five-degrees'
        ? dignity.venus_variant.bounds
        : dignity.label_policy.mt_degrees[g];
    return (
      dignity.grahas[g].moolatrikona_sign === signs[s].id &&
      deg >= lo &&
      deg < hi
    );
  }
  function label(g: string, s: number, deg: number) {
    const d = dignity.grahas[g];
    if (!d) return null;
    const { id, lord } = signs[s];
    if (id === d.exaltation && deg === d.peak_degree_within_sign)
      return 'exaltation-peak';
    if (mt(g, s, deg)) return 'moolatrikona';
    if (
      g === 'mercury' &&
      id === d.exaltation &&
      deg < d.peak_degree_within_sign
    )
      return 'exaltation-sign';
    if (g === lord) return 'own-sign';
    if (id === d.exaltation) return 'exaltation-sign';
    if (id === d.debilitation) return 'debilitation-sign';
    return friendships[g][lord];
  }
  const full = resource(kb, 'aspects/full-graha').inclusive_distances;
  const aspect = (a: string, b: string) =>
    full[a].includes(distance(sign[b], sign[a])) as boolean;
  const retro = mapValues(
    bodies,
    (g) => f.grahas[g as keyof typeof f.grahas].retrograde,
  );
  const combust = mapValues(
    bodies,
    (g) => arc(lon.sun, lon[g]) <= orbs[retro[g] ? 'retrograde' : 'direct'][g],
  );
  const labels = mapValues(bodies, (g) => label(g, sign[g], lon[g] % 30));
  return {
    asc,
    rising,
    unstable,
    signs,
    lon,
    sign,
    division,
    mt,
    label,
    labels,
    aspect,
    retro,
    combust,
    benefic,
    friendships,
    phase,
  };
}
export type Chart = ReturnType<typeof strengthChart>;

export function aspectStrength(
  kb: Catalogue,
  g: string,
  degrees: number,
  method: Profile['drik'],
) {
  const d = calc(kb, 'drik'),
    angle = mod(degrees),
    knots: number[] = d.knots_degrees;
  const i = knots.findIndex((k) => k > angle) - 1;
  const peaks: number[] = d.special[g] ?? [];
  const weight = (j: number) =>
    method === 'interpolated-peak' && peaks.includes(knots[j])
      ? 60
      : (d.common[j] as number);
  const bonus =
    method === 'fixed-segment' &&
    peaks.some((k) => k <= angle && angle < k + d.segment_width_degrees)
      ? d.fixed_segment_bonus[g]
      : 0;
  return (
    weight(i) +
    ((weight(i + 1) - weight(i)) * (angle - knots[i])) /
      (knots[i + 1] - knots[i]) +
    bonus
  );
}
