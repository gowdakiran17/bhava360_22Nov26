import type { Catalogue } from './catalogue';
import {
  arc,
  bodies,
  distance,
  mapValues,
  mod,
  planets,
  resource,
  rule,
  sum,
  type Chart,
  type Profile,
} from './strength-chart';
import type { computeBala } from './bala';
export type Bala = ReturnType<typeof computeBala>;
export const angles = [1, 4, 7, 10],
  anglesTrines = [...angles, 5, 9];
export function reliefs(kb: Catalogue, c: Chart, g: string) {
  if (c.labels[g] !== 'debilitation-sign' || c.rising === null) return [];
  const defs = resource(kb, 'dignity/sign-dignities').grahas;
  const house = (p: string) => distance(c.sign[p], c.rising!);
  const angular = (p: string) =>
    angles.includes(house(p)) ||
    angles.includes(distance(c.sign[p], c.sign.moon));
  const host = (p: string) => c.signs[c.sign[p]].lord;
  const d = host(g),
    e = c.signs.find((s) => s.id === defs[g].exaltation)!.lord;
  const navLord = c.signs[c.division(g, 9)].lord,
    lagnaLord = c.signs[c.rising].lord;
  const causes: string[][] = [];
  if (d !== g && host(d) === g) causes.push([g, d, 'exchange']);
  for (const p of new Set([
    d,
    e,
    ...planets.filter((p) => defs[p].exaltation === c.signs[c.sign[g]].id),
  ]))
    if (angular(p)) causes.push([g, p, 'angular']);
  if (d !== e && angles.includes(distance(c.sign[d], c.sign[e])))
    causes.push([g, d, e, 'mutual']);
  if (c.aspect(d, g)) causes.push([g, d, 'aspect']);
  if (c.signs[c.division(g, 9)].id === defs[g].exaltation)
    causes.push([g, 'navamsa']);
  if (
    anglesTrines.includes(house(navLord)) &&
    (c.rising % 3 === 0 || c.division(lagnaLord, 9) % 3 === 0)
  )
    causes.push([g, navLord, lagnaLord, 'navamsa-support']);
  return causes;
}

export function grades(kb: Catalogue, c: Chart, b: Bala) {
  const policy = resource(kb, 'strength/grade'),
    natural = resource(kb, 'planets/benefic-profile');
  return mapValues(bodies, (g) => {
    if (c.rising === null || c.unstable[g]) return null; // working-noon D9 is insufficient for a natal grade
    const node = c.labels[g] === null,
      d9 = c.division(g, 9);
    const label9 = c.label(g, d9, mod(c.lon[g] * 9, 30));
    const w = b.shadbala[g]?.warLoser;
    if (w === null) return null;
    const house = distance(c.sign[g], c.rising);
    const aq = sum(
      bodies
        .filter((p) => p !== g && c.aspect(p, g))
        .map((p) => (c.benefic[p] ? policy.aspect_unit : -policy.aspect_unit)),
    );
    let dignity = node ? 0 : policy.dignity[c.labels[g]!];
    if (c.labels[g] === 'debilitation-sign')
      dignity =
        policy.cancellation_awards[Math.min(2, reliefs(kb, c, g).length)];
    const terms = {
      dignity,
      house: anglesTrines.includes(house)
        ? 1
        : natural.always_malefic.includes(g) && [3, 6, 11].includes(house)
          ? 1
          : [6, 8, 12].includes(house)
            ? -1
            : 0,
      aspects: Math.min(
        policy.aspect_net_cap,
        Math.max(-policy.aspect_net_cap, aq),
      ),
      combust: c.combust[g] ? (policy.combust[g] ?? policy.combust.other) : 0,
      war: w ? policy.war_loser : 0,
      retrograde: c.retro[g] && c.benefic[g] ? policy.retrograde_benefic : 0,
      d9: node ? 0 : policy.dignity[label9!] * policy.d9_factor,
      vargottama: d9 === c.sign[g] ? policy.vargottama : 0,
      paksha: g === 'moon' ? arc(c.lon.sun, c.lon.moon) / 180 - 0.5 : 0,
    };
    const total = sum(Object.values(terms));
    return {
      terms,
      total,
      grade:
        total >= policy.bands.Strong
          ? 'Strong'
          : total >= policy.bands.Moderate
            ? 'Moderate'
            : 'Weak',
    };
  });
}
export type Grades = ReturnType<typeof grades>;
type Predicate =
  | { all: Predicate[] }
  | { any: Predicate[] }
  | { not: Predicate }
  | { fact: string; op: 'eq' | 'in'; value: unknown };
export type Facts = Record<string, unknown>;
export function evaluate(p: Predicate, facts: Facts): boolean | null {
  if ('all' in p || 'any' in p) {
    const all = 'all' in p,
      items = (all ? p.all : p.any).map((child) => evaluate(child, facts));
    return items.includes(!all) ? !all : items.includes(null) ? null : all;
  }
  if ('not' in p) {
    const result = evaluate(p.not, facts);
    return result === null ? null : !result;
  }
  const actual = facts[p.fact];
  if (actual == null) return null;
  return p.op === 'eq'
    ? actual === p.value
    : Array.isArray(p.value) && p.value.includes(actual);
}
export function doshas(kb: Catalogue, c: Chart, o: Profile) {
  const cfg = resource(kb, 'doshas/profiles').manglik;
  const ref = o.marsReference,
    profile = o.manglik;
  if (
    (['sgs', 'regional-lagna'].includes(profile) && ref !== 'lagna') ||
    (profile === 'rath' && ref === 'venus') ||
    (o.regionalList && profile !== 'regional-lagna')
  )
    throw new RangeError('Incompatible Manglik profile and origin');
  const list =
    profile === 'library'
      ? 'inclusive'
      : profile === 'regional-lagna'
        ? (o.regionalList ?? 'lagna_five')
        : profile === 'rath' && ref === 'moon'
          ? 'lagna_five'
          : 'family_five';
  const origin = ref === 'lagna' ? c.rising : c.sign[ref],
    h = origin === null ? null : distance(c.sign.mars, origin),
    s = c.signs[c.sign.mars].id;
  const mf = {
    house_list: list,
    reference_distance: h,
    relief_profile: profile,
    pair_balanced: false,
    dignity_exception:
      c.signs[c.sign.mars].lord === 'mars' ||
      s === resource(kb, 'dignity/sign-dignities').grahas.mars.exaltation,
    benefic_contact: bodies.some(
      (p) => c.benefic[p] && (c.sign[p] === c.sign.mars || c.aspect(p, 'mars')),
    ),
    raman_house_sign:
      h === null ? null : (cfg.raman_house_sign_pairs[h] ?? []).includes(s),
    raman_sign: cfg.raman_exempt_signs.includes(s),
    raman_companion: ['moon', 'jupiter'].some((g) => c.sign[g] === c.sign.mars),
    raman_ascendant:
      c.rising === null
        ? null
        : [c.sign.jupiter, c.sign.venus].includes(c.rising),
    sgs_lagna_exempt:
      c.rising === null
        ? null
        : cfg.sgs_exempt_lagnas.includes(c.signs[c.rising].id),
    sgs_aspects_candidate:
      h === null
        ? null
        : resource(kb, 'aspects/full-graha').inclusive_distances.mars.some(
            (v: number) =>
              cfg.house_lists[list].includes(mod(h + v - 2, 12) + 1),
          ),
  };
  const facts: Facts = Object.fromEntries(
    Object.entries(mf).map(([k, v]) => ['dosha.mars.' + k, v]),
  );
  facts['dosha.axis.confined'] = planets.every(
    (g) => mod(c.lon[g] - c.lon.rahu) <= 180,
  );
  for (const g of ['sun', 'moon', 'jupiter'])
    facts['dosha.node.shares_' + g] = [c.sign.rahu, c.sign.ketu].includes(
      c.sign[g],
    );
  facts['dosha.rahu.shares_saturn'] = c.sign.saturn === c.sign.rahu;
  facts['dosha.pitru.ninth_node_luminary'] =
    c.rising === null
      ? null
      : ['sun', 'moon'].some(
          (g) =>
            facts['dosha.node.shares_' + g] &&
            distance(c.sign[g], c.rising!) === 9,
        );
  return mapValues(
    [
      'mars-partnership',
      'nodal-axis',
      'grahan',
      'shrapit',
      'guru-chandal',
      'pitru',
    ],
    (slug) => {
      const r = rule(kb, 'doshas.' + slug),
        formed = evaluate(r.conditions, facts);
      const resolved = formed
        ? (r.exceptions.map((x: { effect: string; when: Predicate }) => ({
            effect: x.effect,
            match: evaluate(x.when, facts),
          })) as { effect: string; match: boolean | null }[])
        : [];
      const effects = resolved.filter((x) => x.match).map((x) => x.effect);
      const cancelled = effects.includes('cancel'),
        uncertain = resolved.some(
          (x) => x.effect === 'cancel' && x.match === null,
        );
      return {
        id: r.id,
        formed,
        effects,
        survives: cancelled ? false : uncertain ? null : formed,
      };
    },
  );
}
