import type { Catalogue } from './catalogue';
import {
  mapValues,
  mod,
  planets,
  resource,
  rule,
  sum,
  type Chart,
  type Profile,
} from './strength-chart';

export function ashtakavarga(kb: Catalogue, c: Chart, o: Profile) {
  if (c.rising === null) return null;
  const table = resource(kb, 'strength/ashtakavarga/bindu');
  const reduction = rule(kb, 'strength-ashtakavarga.shodhana').calculation;
  const policy = rule(kb, 'strength-ashtakavarga.shodhya-pinda').calculation;
  const weights = kb.resources[policy.weights];
  const natal: Record<string, number> = { ...c.sign, lagna: c.rising };
  const occupied = new Set(planets.map((g) => natal[g]));
  const rows = mapValues(planets, (g) => {
    const offsets =
      g === 'moon' && o.bav === 'pvr-table-20'
        ? table.variants[o.bav].moon
        : table.offsets[g];
    const raw = Array<number>(12).fill(0);
    for (const p of table.contributors)
      for (const house of offsets[p]) raw[mod(natal[p] + house - 1, 12)]++;
    const trinal = [...raw];
    for (const group of reduction.trines as number[][]) {
      const min = Math.min(...group.map((i) => raw[i]));
      for (const i of group) trinal[i] -= min;
    }
    const reduced = [...trinal];
    for (const pair of weights.same_owner_pairs as string[]) {
      const [a, b] = pair
        .toLowerCase()
        .split('/')
        .map((id) => c.signs.findIndex((s) => s.id === id));
      const x = trinal[a],
        y = trinal[b];
      if (!x || !y || (occupied.has(a) && occupied.has(b))) continue;
      if (occupied.has(a)) reduced[b] = y > x ? x : 0;
      else if (occupied.has(b)) reduced[a] = x > y ? y : 0;
      else reduced[a] = reduced[b] = x === y ? 0 : Math.min(x, y);
    }
    const rashi = sum(
      reduced.map(
        (n, i) => n * weights.rashi_weights[policy.rashi_weight_profile][i],
      ),
    );
    const graha = sum(
      planets.map(
        (p, i) =>
          reduced[natal[p]] * weights.graha_weights_sun_through_saturn[i],
      ),
    );
    return {
      raw,
      trinal,
      reduced,
      rashiPinda: rashi,
      grahaPinda: graha,
      shodhyaPinda: rashi + graha,
    };
  });
  const sav = Array.from({ length: 12 }, (_, i) =>
    sum(planets.map((g) => rows[g].raw[i])),
  );
  return { bav: rows, sav, total: sum(sav) };
}
