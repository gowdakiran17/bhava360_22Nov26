import type { EphemerisPort } from '@bhava360/core';
import type { Catalogue } from './catalogue';
import {
  arc,
  aspectStrength,
  calc,
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

function solarInterval(
  port: EphemerisPort,
  jd: number,
  lat: number,
  lon: number,
  elev: number,
) {
  // Start before the preceding local sunrise, including births before dawn.
  const event = (after: number, kind: 'rise' | 'set') =>
    port.riseSet(after, 'sun', kind, lat, lon, elev);
  let rise = event(jd - 1.5, 'rise');
  if (rise === null || rise > jd) return null;
  let next = event(rise + 1e-6, 'rise');
  while (next !== null && next <= jd) {
    if (next <= rise) throw new Error('Non-increasing sunrise');
    rise = next;
    next = event(rise + 1e-6, 'rise');
  }
  const set = event(rise, 'set');
  if (
    set === null ||
    next === null ||
    !(rise < set && set < next) ||
    next - rise > 1.5
  )
    return null;
  const day = jd < set,
    elapsed = day ? (jd - rise) / (set - rise) : (jd - set) / (next - set);
  return { rise, day, elapsed };
}

export function computeBala(
  kb: Catalogue,
  port: EphemerisPort,
  c: Chart,
  o: Profile,
  jd: number,
  lat: number,
  lon: number,
  elev: number,
) {
  const geom = port.solarGeometry(jd, lat, lon, elev);
  const orbit = Object.fromEntries(
    planets.map((g) => [g, port.strengthPosition(jd, g)]),
  );
  const solar = c.asc === null ? null : solarInterval(port, jd, lat, lon, elev);
  const angles: Record<string, number | null> = {
    asc: c.asc,
    dsc: c.asc === null ? null : c.asc + 180,
    mc: c.asc === null ? null : geom.mc,
    ic: c.asc === null ? null : geom.mc + 180,
  };
  const dignity = resource(kb, 'dignity/sign-dignities').grahas;
  const sap = calc(kb, 'saptavargaja'),
    rel = resource(kb, 'dignity/relationships');
  const war = rule(kb, 'states.graha-yuddha').state;
  const rivals = mapValues(planets, (g) =>
    (war.eligible as string[]).filter(
      (p) =>
        war.eligible.includes(g) &&
        p !== g &&
        arc(c.lon[p], c.lon[g]) < war.maximum_exclusive_degrees,
    ),
  );
  const loser = mapValues(planets, (g) => {
    const others = rivals[g];
    if (!others.length) return false;
    if (
      others.length !== 1 ||
      rivals[others[0]].length !== 1 ||
      orbit[g].latitude === orbit[others[0]].latitude
    )
      return null;
    return orbit[g].latitude < orbit[others[0]].latitude;
  });
  const rows = mapValues(planets, (g) => {
    const longitude = c.lon[g],
      s = c.sign[g],
      deg = longitude % 30;
    const peak =
      c.signs.findIndex((row) => row.id === dignity[g].debilitation) * 30 +
      dignity[g].peak_degree_within_sign;
    const uchcha = arc(longitude, peak) / 3;
    const sapta = sum(
      sap.divisions.map((n: number) => {
        const target = c.division(g, n),
          owner = c.signs[target].lord;
        if (n === 1 && c.mt(g, target, deg)) return sap.moolatrikona;
        if (owner === g) return sap.own;
        return sap.relationship_awards[
          rel.award_order.indexOf(c.friendships[g][owner])
        ];
      }),
    );
    const oj = calc(kb, 'ojayugma'),
      dr = calc(kb, 'drekkana');
    const parity = Number(oj.even.includes(g));
    const ojayugma =
      oj.award * [s, c.division(g, 9)].filter((i) => i % 2 === parity).length;
    const kendradi =
      c.rising === null
        ? null
        : (calc(kb, 'kendradi').awards[mod(s - c.rising, 12) % 3] as number);
    const drekkana = dr.groups[Math.floor(deg / 10)].includes(g) ? dr.award : 0;
    const sthana =
      kendradi === null
        ? null
        : uchcha + sapta + ojayugma + kendradi + drekkana;
    const weak = angles[calc(kb, 'dig').weak_angle[g]],
      dig = weak === null ? null : arc(longitude, weak) / 3;
    const noon = 5 * Math.min(geom.apparentHour, 24 - geom.apparentHour);
    const nat = calc(kb, 'nathonnata');
    const nathonnata = nat.day.includes(g)
      ? noon
      : nat.night.includes(g)
        ? 60 - noon
        : 60;
    const phase = arc(c.lon.sun, c.lon.moon) / 3;
    const paksha = calc(kb, 'paksha').bright.includes(g) ? phase : 60 - phase;
    const dec = orbit[g].declination;
    const signed =
      g === 'mercury'
        ? Math.abs(dec)
        : calc(kb, 'ayana').south.includes(g)
          ? -dec
          : dec;
    const ayana = 1.25 * (24 + Math.max(-24, Math.min(24, signed)));
    let kalaBase: number | null = null;
    if (solar) {
      const days = Math.floor(solar.rise + 0.5 + lon / 360) - 2451545;
      const daylord = planets[mod(6 + days, 7)],
        hora = calc(kb, 'hora'),
        trib = calc(kb, 'tribhaga');
      const tri =
        trib[solar.day ? 'day' : 'night'][Math.floor(3 * solar.elapsed)];
      const hour =
        hora.order[
          (hora.order.indexOf(daylord) +
            Math.floor(12 * solar.elapsed) +
            (solar.day ? 0 : 12)) %
            7
        ];
      kalaBase =
        nathonnata +
        paksha +
        ayana +
        (g === tri || g === trib.always ? 60 : 0) +
        (g === hour ? hora.award : 0);
      for (const key of ['abda', 'masa', 'vara']) {
        const { span, award } = calc(kb, key);
        if (planets[mod(6 + span * Math.floor(days / span), 7)] === g)
          kalaBase! += award;
      }
    }
    const inner = calc(kb, 'cheshta').inner.includes(g);
    const slow = orbit[inner ? 'sun' : g].meanLongitude,
      fast = orbit[inner ? g : 'sun'].meanLongitude;
    const cheshta =
      g === 'sun'
        ? ayana
        : g === 'moon'
          ? paksha
          : slow === null || fast === null
            ? null
            : arc(slow + (mod(longitude - slow + 180) - 180) / 2, fast) / 3;
    const naisargika =
      ((1 + calc(kb, 'naisargika').ascending.indexOf(g)) * 60) / 7;
    const drik = sum(
      planets
        .filter((p) => p !== g)
        .map((p) => {
          const special =
            o.drik === 'fixed-segment' && (p === 'mercury' || p === 'jupiter');
          return (
            aspectStrength(kb, p, longitude - c.lon[p], o.drik) *
            (special ? 1 : c.benefic[p] ? 0.25 : -0.25)
          );
        }),
    );
    return {
      sthana,
      dig,
      kalaBase,
      cheshta,
      naisargika,
      drik,
      uchcha,
      saptavargaja: sapta,
      ojayugma,
      kendradi,
      drekkana,
    };
  });
  const shadbala = mapValues(planets, (g) => {
    const r = rows[g],
      p = rivals[g][0];
    let yuddha: number | null = 0;
    if (p) {
      const other = rows[p],
        classical = o.yuddha === 'classical-disc-difference';
      const a = orbit[g].discArcminutes,
        b = orbit[p].discArcminutes;
      const divisor = classical ? (a && b ? Math.abs(a - b) : null) : 1;
      const subtotal = (x: typeof r) =>
        x.kalaBase === null
          ? null
          : !classical
            ? x.kalaBase
            : x.sthana === null || x.dig === null
              ? null
              : x.kalaBase + x.sthana + x.dig;
      const pre = subtotal(r),
        opp = subtotal(other);
      yuddha =
        loser[g] === null || !divisor || pre === null || opp === null
          ? null
          : ((loser[g] ? -1 : 1) * Math.abs(pre - opp)) / divisor;
    }
    const kala =
      r.kalaBase === null || yuddha === null ? null : r.kalaBase + yuddha;
    const total =
      r.sthana === null || r.dig === null || r.cheshta === null || kala === null
        ? null
        : r.sthana + r.dig + kala + r.cheshta + r.naisargika + r.drik;
    return {
      ...r,
      kala,
      yuddha,
      warLoser: loser[g],
      total,
      rupas: total === null ? null : total / 60,
      ishta: r.cheshta === null ? null : Math.sqrt(r.uchcha * r.cheshta),
      kashta:
        r.cheshta === null
          ? null
          : Math.sqrt((60 - r.uchcha) * (60 - r.cheshta)),
    };
  });
  const bhava = resource(kb, 'strength/bhava-bala/components');
  const corners = [
    c.asc ?? 0,
    mod(geom.mc + 180),
    mod((c.asc ?? 0) + 180),
    geom.mc,
  ];
  const spans = corners.map((x, i) => mod(corners[(i + 1) % 4] - x));
  const sripati = o.bhava === 'sripati';
  const bhavaBala =
    c.rising === null ||
    !solar ||
    (sripati && (Math.abs(sum(spans) - 360) > 1e-7 || Math.min(...spans) <= 0))
      ? null
      : Array.from({ length: 12 }, (_, i) => {
          const q = Math.floor(i / 3),
            j = i % 3;
          const mid = sripati
            ? mod(corners[q] + (j * spans[q]) / 3)
            : 30 * mod(c.rising! + i, 12) + 15;
          const group = Object.keys(bhava.class_intervals_deg).find((key) =>
            bhava.class_intervals_deg[key].some(
              ([lo, hi]: number[]) => lo <= mid && mid < hi,
            ),
          )!;
          const h = bhava.strongest_house[group] - 1,
            steps = mod(i - h, 12);
          const dig = sripati
            ? arc(mid, corners[h / 3] + 180) / 3
            : 60 - 10 * Math.min(steps, 12 - steps);
          const drik = sum(
            planets.map(
              (g) =>
                aspectStrength(kb, g, mid - c.lon[g], 'interpolated-peak') *
                (bhava.drik.weights[g] ?? (c.benefic[g] ? 0.25 : -0.25)),
            ),
          );
          const before = j === 0 ? spans[mod(q - 1, 4)] : spans[q];
          const left = sripati ? mid - before / 6 : mid - 15,
            width = sripati ? (before + spans[q]) / 6 : 30;
          const occupants = sum(
            Object.keys(bhava.occupants.weights)
              .filter((g) => mod(c.lon[g] - left) < width)
              .map((g) => bhava.occupants.weights[g]),
          );
          const sign = c.signs[Math.floor(mid / 30)],
            lord = shadbala[sign.lord].total;
          const period = solar.day
            ? 'day'
            : geom.altitude >= -6
              ? 'twilight'
              : 'night';
          const birthTime = bhava.birth_time[period].includes(sign.id)
            ? bhava.birth_time.award
            : 0;
          return {
            house: i + 1,
            madhya: mid,
            lord: sign.lord,
            bhavadhipati: lord,
            dig,
            drik,
            occupants,
            birthTime,
            total:
              lord === null ? null : lord + dig + drik + occupants + birthTime,
          };
        });
  return { shadbala, bhavaBala, dayBirth: solar?.day ?? null };
}
