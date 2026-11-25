import { birthEpoch, type EphemerisPort } from '@bhava360/core';
import type { Catalogue } from './catalogue';
import type { VedicFacts, VedicInput } from './index';
import { ashtakavarga } from './ashtakavarga';
import { computeBala } from './bala';
import {
  defaults,
  resource,
  strengthChart,
  type StrengthOptions,
} from './strength-chart';
import { doshas, grades } from './strength-profiles';
import { yogas } from './yogas';
import { computeVimshottari } from './vimshottari';

export interface StrengthInput extends VedicInput {
  variants?: StrengthOptions;
  elevationM?: number;
  periodInstantUtc?: string;
  mahabhagyaBranch?: 'male-day' | 'female-night';
}
interface Words {
  en: string;
  kn: string;
  hi: string;
  tone: 'Supportive' | 'Steady' | 'Take care';
}
function publicWords(row: Words | undefined): Words | null {
  return row ? { en: row.en, kn: row.kn, hi: row.hi, tone: row.tone } : null;
}
export function computeStrength(
  port: EphemerisPort,
  kb: Catalogue,
  chart: VedicFacts,
  input: StrengthInput,
) {
  const options: Record<keyof StrengthOptions, readonly string[]> = {
    drik: [defaults.drik, 'fixed-segment'],
    yuddha: [defaults.yuddha, 'classical-disc-difference'],
    bhava: [defaults.bhava, 'sripati'],
    moon: [defaults.moon, 'raman-ashtami', 'bright-72'],
    mercury: [defaults.mercury, 'mercury-strict'],
    venus: [defaults.venus, 'saravali-five-degrees'],
    bav: [defaults.bav, 'pvr-table-20'],
    yoga: [defaults.yoga, 'mutual-full-aspect', 'budhaditya-close-orb'],
    manglik: [defaults.manglik, 'regional-lagna', 'raman', 'rath', 'sgs'],
    marsReference: ['lagna', 'moon', 'venus'],
    regionalList: ['lagna_five', 'four'],
  };
  for (const [key, value] of Object.entries(input.variants ?? {})) {
    if (
      !Object.hasOwn(options, key) ||
      !options[key as keyof StrengthOptions].includes(value)
    )
      throw new RangeError('Unknown strength convention: ' + key);
  }
  if (!Number.isFinite(input.elevationM ?? 0))
    throw new RangeError('Invalid observer elevation');
  const o = { ...defaults, ...input.variants };
  const c = strengthChart(kb, chart, o);
  const b = computeBala(
    kb,
    port,
    c,
    o,
    chart.julianDayUt,
    input.latitude,
    input.longitude,
    input.elevationM ?? 0,
  );
  const planetGrades = grades(kb, c, b);
  const policy = resource(kb, 'strength/user-words');
  const projection = {
    planets: Object.fromEntries(
      Object.entries(planetGrades).map(([g, r]) => [
        g,
        publicWords(
          r ? policy.labels[policy.planet_grade[r.grade]] : undefined,
        ),
      ]),
    ),
    houses:
      b.bhavaBala?.map((row) => {
        const houses = b.bhavaBala!;
        if (row.total === null || houses.some((h) => h.total === null))
          return null;
        const rank = 1 + houses.filter((h) => h.total! > row.total!).length;
        const label = houses.every((h) => h.total === row.total)
          ? policy.bhava.all_equal
          : rank <= policy.bhava.supported_through
            ? 'supported'
            : rank <= policy.bhava.steady_through
              ? 'steady'
              : 'modest';
        return publicWords(policy.labels[label]);
      }) ?? null,
  };
  const timeline = computeVimshottari(port, kb, input).timeline;
  const moment = birthEpoch(
    input.periodInstantUtc ?? chart.workingInstantUtc,
    input.timeZone,
    'known',
  ).jdUt;
  const contains = (p: { startUtc: string; endUtc: string }) =>
    birthEpoch(p.startUtc, 'UTC', 'known').jdUt <= moment &&
    moment < birthEpoch(p.endUtc, 'UTC', 'known').jdUt;
  const maha = timeline?.find(contains),
    antar = maha?.children?.find(contains);
  const period = [maha?.lord, antar?.lord].filter((g): g is string => !!g);
  return {
    admin: {
      convention: {
        ...chart.convention,
        ...o,
        profile: 'parashari-strength-v1',
        ashtakavargaProfile: 'bphs-seven-graha-337',
        published_raman: 'unverified',
        savanaEpoch: 'local sunrise day of 2000-01-01',
        periodClock: 'julian-365.25',
        periodInstantUtc: input.periodInstantUtc ?? chart.workingInstantUtc,
      },
      ...b,
      planetGrades,
      period,
      dignity: c.labels,
      friendships: c.friendships,
      combust: c.combust,
      benefic: c.benefic,
      ashtakavarga: ashtakavarga(kb, c, o),
      yogas: yogas(kb, c, o, b, planetGrades, period, input.mahabhagyaBranch),
      doshas: doshas(kb, c, o),
    },
    public: projection,
  };
}
