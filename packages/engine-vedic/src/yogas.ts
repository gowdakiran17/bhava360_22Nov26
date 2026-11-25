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
  type Chart,
  type Profile,
} from './strength-chart';
import {
  angles,
  anglesTrines,
  evaluate,
  reliefs,
  type Bala,
  type Facts,
  type Grades,
} from './strength-profiles';

interface Formation {
  method: string;
  index: number;
  patterns: number[][];
  count: number;
  nature: string;
  reference: string;
  group: string;
}
export function yogas(
  kb: Catalogue,
  c: Chart,
  o: Profile,
  b: Bala,
  grades: Grades,
  period: string[],
  branch?: 'male-day' | 'female-night',
) {
  const config = resource(kb, 'yogas/activation');
  const members: string[] = config.members;
  const h = (p: string) => distance(c.sign[p], c.rising!);
  const lord = (i: number) => c.signs[mod(c.rising! + i - 1, 12)].lord;
  const host = (p: string) => c.signs[c.sign[p]].lord;
  const dist = (a: string, ref: string) => distance(c.sign[a], c.sign[ref]);
  const at = (i: number) => planets.filter((p) => h(p) === i);
  const mutual = (a: string, b: string) => c.aspect(a, b) && c.aspect(b, a);
  const exalt = (g: string) =>
    resource(kb, 'dignity/sign-dignities').grahas[g].exaltation ===
    c.signs[c.sign[g]].id;
  const strong = (p: string) =>
    ['Strong', 'Moderate'].includes(grades[p]?.grade ?? '');
  const five = planets.filter((p) => p !== 'sun' && p !== 'moon'),
    benefics = planets.filter((p) => c.benefic[p]);
  const occupied = new Set(planets.map(h));
  const facts: Facts = {};
  for (const g of planets) {
    for (const ref of ['lagna', 'sun', 'moon', 'jupiter'])
      facts['d1.' + g + '.distance_from_' + ref] =
        ref === 'lagna' ? (c.rising === null ? null : h(g)) : dist(g, ref);
    facts['d1.' + g + '.own_or_exalted'] = exalt(g) || host(g) === g;
    facts['d1.' + g + '.debilitated'] = c.labels[g] === 'debilitation-sign';
  }
  for (let i = 1; i <= 12; i++)
    facts['d1.lord_' + i + '.distance_from_lagna'] =
      c.rising === null ? null : h(lord(i));
  facts['d1.lord_9.dignified_in_angle_or_trine'] =
    c.rising === null
      ? null
      : anglesTrines.includes(h(lord(9))) &&
        facts['d1.' + lord(9) + '.own_or_exalted'];
  facts['d1.moon.eligible_flank'] = five.some((p) =>
    [2, 12].includes(dist(p, 'moon')),
  );
  const jupiter = b.shadbala.jupiter.rupas;
  facts['d1.jupiter.saraswati_strength'] =
    jupiter === null
      ? null
      : jupiter >=
          rule(kb, 'strength-shadbala.totals').calculation.minimum_rupas
            .jupiter &&
        (facts['d1.jupiter.own_or_exalted'] ||
          rule(
            kb,
            'planets.jupiter',
          ).graha.natural_friendships.friends.includes(host('jupiter')));
  const match = (condition: unknown, group: string[]) =>
    condition ? [group] : [];
  function formation(slug: string, f: Formation): string[][] | null {
    const all = planets;
    switch (f.method) {
      case 'modality':
        return match(
          all.every((p) => c.sign[p] % 3 === f.index),
          all,
        );
      case 'distinct-count':
        return match(new Set(all.map((p) => c.sign[p])).size === f.count, all);
      case 'occupied-pattern':
        return match(
          f.patterns.some(
            (pattern) =>
              pattern.length === occupied.size &&
              pattern.every((i) => occupied.has(i)),
          ),
          all,
        );
      case 'quadrant-nature': {
        const groups = angles
          .map(at)
          .filter(
            (ps) =>
              ps.length &&
              ps.every((g) => c.benefic[g] === (f.nature === 'benefic')),
          );
        return match(groups.length >= 3, groups.flat());
      }
      case 'paired-nature':
        return match(
          occupied.size === 4 &&
            angles.every(
              (i) =>
                at(i).length &&
                at(i).every(
                  (g) =>
                    c.benefic[g] ===
                    ([1, 7].includes(i) === slug.endsWith('vajra')),
                ),
            ),
          all,
        );
      case 'flanks': {
        const ref = f.reference === 'moon' ? c.sign.moon : c.rising!;
        const groups = [2, 12].map((i) =>
          all.filter((g) => distance(c.sign[g], ref) === i),
        );
        return match(
          groups.every(
            (gs) =>
              gs.length &&
              gs.every((g) => c.benefic[g] === (f.nature === 'benefic')),
          ),
          groups.flat(),
        );
      }
    }
    const a = lord(1),
      d = lord(9),
      t = lord(10);
    if ((slug === 'kahala' || slug === 'shankha') && !grades[a]) return null;
    if (slug === 'bheri' && !grades[d]) return null;
    switch (slug) {
      case 'guru-mangala':
        return match([1, 7].includes(dist('mars', 'jupiter')), [
          'mars',
          'jupiter',
        ]);
      case 'dharma-karmadhipati':
        return match(
          d !== t &&
            (dist(d, t) === 1 || (h(d) === 10 && h(t) === 9) || mutual(d, t)),
          [d, t],
        );
      case 'parvata': {
        const angular = all.filter((g) => angles.includes(h(g)));
        return match(
          angular.length &&
            angular.every((g) => c.benefic[g]) &&
            [...at(7), ...at(8)].every((g) => c.benefic[g]),
          angular,
        );
      }
      case 'kahala':
        return match(angles.includes(dist(lord(4), 'jupiter')) && strong(a), [
          a,
          lord(4),
          'jupiter',
        ]);
      case 'chamara':
        return [
          ...match(
            exalt(a) && angles.includes(h(a)) && c.aspect('jupiter', a),
            [a, 'jupiter'],
          ),
          ...[7, 9, 10]
            .map(at)
            .map((gs) => gs.filter((g) => c.benefic[g]))
            .filter((gs) => gs.length >= 2),
        ];
      case 'shankha':
        return match(strong(a) && angles.includes(dist(lord(5), lord(6))), [
          a,
          lord(5),
          lord(6),
        ]);
      case 'bheri': {
        const group = ['jupiter', 'venus', a];
        return strong(d)
          ? [
              ...match(
                [1, 2, 7, 12].every((i) => occupied.has(i)),
                [d, ...[1, 2, 7, 12].flatMap(at)],
              ),
              ...match(
                group.every((g) =>
                  group.every((p) => angles.includes(dist(g, p))),
                ),
                [d, ...group],
              ),
            ]
          : [];
      }
      case 'lagnadhi':
        return match(
          ['mercury', 'jupiter', 'venus'].every((g) =>
            [6, 7, 8].includes(h(g)),
          ) && at(4).every((g) => c.benefic[g]),
          ['mercury', 'jupiter', 'venus'],
        );
      case 'kalanidhi':
        return match(
          [2, 5].includes(h('jupiter')) &&
            ['mercury', 'venus'].every(
              (g) => dist(g, 'jupiter') === 1 || c.aspect(g, 'jupiter'),
            ),
          ['mercury', 'jupiter', 'venus'],
        );
      case 'sreenatha':
        return match(h(lord(7)) === 10 && exalt(lord(7)) && dist(d, t) === 1, [
          lord(7),
          d,
          t,
        ]);
      case 'mahabhagya':
        return branch && b.dayBirth !== null
          ? match(
              (branch === 'male-day') === b.dayBirth &&
                [c.rising!, c.sign.sun, c.sign.moon].every(
                  (s) => (s % 2 === 0) === b.dayBirth,
                ),
              ['sun', 'moon'],
            )
          : null;
      case 'kusuma': {
        const peers = benefics.filter(
          (g) => g !== 'moon' && dist(g, 'moon') === 1,
        );
        return match(
          c.rising! % 3 === 1 &&
            angles.includes(h('venus')) &&
            [1, 5, 9].includes(h('moon')) &&
            peers.length &&
            h('saturn') === 10,
          ['venus', 'moon', 'saturn', ...peers],
        );
      }
      case 'parijata': {
        const group = [
          a,
          host(a),
          host(host(a)),
          c.signs[c.division(host(a), 9)].lord,
        ];
        return match(
          group.every((g) => anglesTrines.includes(h(g)) || exalt(g)),
          group,
        );
      }
      case 'pravrajya':
        return [...occupied].map(at).filter((gs) => gs.length >= 4);
      default:
        throw new Error('Unknown formation ' + slug);
    }
  }
  function witnesses(id: string): string[][] | null {
    const row = kb.rules[id].rule,
      slug = id.split('.').at(-1)!;
    if (
      c.rising === null &&
      !(
        row.formation?.method === 'modality' ||
        row.formation?.method === 'distinct-count' ||
        row.formation?.reference === 'moon' ||
        [
          'guru-mangala',
          'pravrajya',
          'budhaditya',
          'chandra-mangala',
          'adhi',
          'sunapha',
          'anapha',
          'durudhara',
          'vesi',
          'vosi',
          'ubhayachari',
          'kemadruma',
          'gaja-kesari',
          'sakata',
        ].includes(slug)
      )
    )
      return null;
    if (row.formation) return formation(slug, row.formation);
    if (slug.startsWith('neecha-bhanga'))
      return planets.flatMap((g) =>
        slug.endsWith('-raja') && !angles.includes(h(g))
          ? []
          : reliefs(kb, c, g).map((group) => group.slice(0, -1)),
      );
    if (slug === 'amala' || slug === 'vasumati')
      return [c.rising!, c.sign.moon].flatMap((ref) => {
        const group = benefics.filter((g) =>
          (slug === 'amala' ? [10] : [3, 6, 10, 11]).includes(
            distance(c.sign[g], ref),
          ),
        );
        return match(
          group.length &&
            (slug === 'amala' || group.length === benefics.length),
          group,
        );
      });
    if (slug.startsWith('parivartana') || slug === 'dhana' || slug === 'raja') {
      const groups: string[][] = [];
      for (let a = 1; a <= 12; a++)
        for (let d = a + 1; d <= 12; d++) {
          const p = lord(a),
            q = lord(d),
            exchange = p !== q && h(p) === d && h(q) === a;
          if (slug.startsWith('parivartana')) {
            const kind = [a, d].some((i) => [6, 8, 12].includes(i))
              ? 'dainya'
              : [a, d].includes(3)
                ? 'khala'
                : 'maha';
            if (
              exchange &&
              (slug === 'parivartana' || slug.endsWith('-' + kind))
            )
              groups.push([p, q]);
          } else {
            const offices =
              slug === 'dhana'
                ? [a, d].every((i) => [1, 2, 5, 9, 11].includes(i))
                : [a, d].some((i) => angles.includes(i)) &&
                  [a, d].some((i) => [5, 9].includes(i));
            const alternate =
              o.yoga === 'mutual-full-aspect' &&
              mutual(p, q) &&
              (slug === 'raja' ||
                ([a, d].some((i) => [2, 11].includes(i)) &&
                  [a, d].some((i) => [5, 9].includes(i))));
            if (
              offices &&
              (p === q
                ? slug === 'raja' && a !== 1
                : exchange || dist(p, q) === 1 || alternate)
            )
              groups.push([p, q]);
          }
        }
      return groups;
    }
    let formed = evaluate(row.conditions, facts);
    if (
      slug === 'chandra-mangala' &&
      o.yoga === 'mutual-full-aspect' &&
      mutual('mars', 'moon')
    )
      formed = true;
    if (formed === null) return null;
    const group: string[] = [];
    for (const p of row.participants) {
      if (p.startsWith('lord:')) group.push(lord(Number(p.slice(5))));
      else if (p === 'flanking-grahas') {
        const origin = row.participants.includes('sun') ? 'sun' : 'moon';
        const sides = ['sunapha', 'vesi'].includes(slug)
          ? [2]
          : ['anapha', 'vosi'].includes(slug)
            ? [12]
            : [2, 12];
        group.push(...five.filter((g) => sides.includes(dist(g, origin))));
      } else group.push(p);
    }
    return match(formed, group);
  }
  const groups = mapValues(members, witnesses);
  const specific = members.some(
    (id) =>
      ['akriti', 'dala', 'ashraya'].includes(
        kb.rules[id].rule.formation?.group,
      ) && groups[id]?.length,
  );
  return mapValues(members, (id) => {
    const r = kb.rules[id].rule,
      raw = groups[id];
    if (!raw) return { formed: null, witnesses: null };
    const unique = new Map(
      raw.map((group) => {
        const ps = [...new Set(group)].sort();
        return [ps.join('/'), ps];
      }),
    );
    const resolved = [...unique.values()].map((ps) => {
      const anchor = ps[0],
        sep = arc(c.lon.sun, c.lon.mercury);
      const afflicted = (g: string) =>
        c.combust[g] || b.shadbala[g]?.warLoser === true;
      const bound = { ...facts };
      const ownFacts: Facts = {
        foundation_cancelled: false,
        participant_afflicted: ps.some(afflicted),
        anchor_combust: c.combust[anchor],
        anchor_war_loser: b.shadbala[anchor]?.warLoser,
        anchor_d9_debilitated:
          c.signs[c.division(anchor, 9)].id ===
          resource(kb, 'dignity/sign-dignities').grahas[anchor]?.debilitation,
        forming_lord_owns_eighth:
          c.rising === null ? null : ps.includes(lord(8)),
        mixed_nature_witness:
          ps.some((g) => c.benefic[g]) && ps.some((g) => !c.benefic[g]),
        mercury_combust:
          o.yoga === 'budhaditya-close-orb' ? sep <= 3 : c.combust.mercury,
        mercury_deep_combust: sep <= 3,
        mercury_gate_miss:
          c.rising === null
            ? null
            : grades.mercury?.grade === 'Weak' &&
              !anglesTrines.includes(h('mercury')),
        moon_benefic_aspect: benefics.some((g) => c.aspect(g, 'moon')),
        kemadruma_angular:
          c.rising === null
            ? null
            : planets.some((g) => g !== 'moon' && angles.includes(h(g))),
        luminary_conjunction: ['sun', 'moon'].some(
          (g) => g !== anchor && dist(g, anchor) === 1,
        ),
        specific_shape_precedes: specific,
        jupiter_afflicted:
          afflicted('jupiter') ||
          ['shatru', 'adhi-shatru'].includes(c.labels.jupiter!) ||
          (bodies.some((p) => !c.benefic[p] && c.aspect(p, 'jupiter')) &&
            !benefics.some((p) => c.aspect(p, 'jupiter'))),
        other_lord_association: planets.some(
          (g) =>
            !ps.includes(g) && (dist(g, anchor) === 1 || mutual(g, anchor)),
        ),
      };
      for (const [k, v] of Object.entries(ownFacts)) bound['d1.yoga.' + k] = v;
      const exceptions = (
        r.exceptions as {
          when: Parameters<typeof evaluate>[0];
          effect: string;
        }[]
      ).map((ex) => ({ effect: ex.effect, hit: evaluate(ex.when, bound) }));
      const effects = exceptions.filter((x) => x.hit).map((x) => x.effect);
      const cancelled = effects.includes('cancel'),
        withheld =
          exceptions.some((x) => x.effect === 'cancel' && x.hit === null) ||
          ps.some((g) => !grades[g]);
      const gate =
        cancelled || withheld
          ? null
          : ps.every((g) => grades[g]!.grade === 'Weak')
            ? 'hidden'
            : ps.some((g) => grades[g]!.grade === 'Weak')
              ? 'mild'
              : 'full';
      const active = cancelled
        ? false
        : withheld
          ? null
          : period.some((g) => ps.includes(g))
            ? true
            : period.length === 2
              ? false
              : null;
      const display = cancelled
        ? 'omitted'
        : withheld
          ? 'withheld'
          : gate === 'hidden' || r.visibility === 'admin-only'
            ? 'staff-only'
            : !active
              ? 'yoga-background'
              : gate === 'mild' ||
                  effects.includes('soften') ||
                  exceptions.some(
                    (e) => e.effect === 'soften' && e.hit === null,
                  )
                ? 'yoga-mild'
                : 'normal';
      return { participants: ps, effects, gate, active, display };
    });
    return { formed: !!raw.length, witnesses: resolved };
  });
}
