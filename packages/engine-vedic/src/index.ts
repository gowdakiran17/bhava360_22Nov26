import {
  birthEpoch,
  type EngineModule,
  type EphemerisPort,
  type EphemerisFlag,
  type Precision,
  type ZonedClock,
} from '@bhava360/core';
import { loadCatalogue, type Nakshatra } from './catalogue';
import { computeVargas, type Longitudes } from './vargas';

const planets = [
  'sun',
  'moon',
  'mercury',
  'venus',
  'mars',
  'jupiter',
  'saturn',
] as const;
type Graha = (typeof planets)[number] | 'rahu' | 'ketu';
export interface VedicInput {
  birthInstantUtc: string;
  latitude: number;
  longitude: number;
  timeZone: string;
  timePrecision: Precision;
  nodeType?: 'mean' | 'true';
}
interface Position {
  longitude: number;
  sign: number;
  house: number | null;
  nakshatra: Nakshatra;
  pada: number;
}
interface Motion extends Position {
  speed: number;
  retrograde: boolean;
}
export interface VedicFacts {
  vargas: ReturnType<typeof computeVargas>;
  workingInstantUtc: string;
  julianDayUt: number;
  ayanamsa: number;
  lagna: Position | null;
  grahas: Record<Graha, Motion>;
  convention: {
    ayanamsaId: 'lahiri';
    siderealMode: 1;
    nodeType: 'mean' | 'true';
    houseSystem: 'whole-sign';
    ephemerisFlag: EphemerisFlag;
    calendar: 'proleptic-gregorian';
    timePrecision: Precision;
  };
}

import { computePanchang, type PanchangInput } from './panchang';
import { computeVimshottari, type VimshottariInput } from './vimshottari';
import { computeStrength, type StrengthInput } from './strength';
import { computeChara, type CharaInput } from './chara';
import { computeYogini, type YoginiInput } from './yogini';
export type {
  CharaInput,
  YoginiInput,
  PanchangInput,
  VimshottariInput,
  StrengthInput,
};
export function createVedicEngine(port: EphemerisPort) {
  const catalogue = loadCatalogue();
  const { nakshatras, methods } = catalogue;
  const engine = {
    computeStrength(input: StrengthInput): ReturnType<typeof computeStrength> {
      return computeStrength(
        port,
        catalogue,
        engine.computeFacts(input),
        input,
      );
    },
    computeYogini: (input: YoginiInput) =>
      computeYogini(port, catalogue, input),
    computeChara: (input: CharaInput) => computeChara(port, catalogue, input),
    computePanchang: (input: PanchangInput) =>
      computePanchang(port, catalogue, input),
    computeVimshottari: (input: VimshottariInput) =>
      computeVimshottari(port, catalogue, input),
    id: 'vedic',
    inputs: [
      'birthInstantUtc',
      'latitude',
      'longitude',
      'timeZone',
      'timePrecision',
      'nodeType',
    ],
    factsSchema: {
      workingInstantUtc: 'ISO UTC',
      julianDayUt: 'days',
      ayanamsa: 'degrees',
      lagna: 'Position | null',
      grahas: 'Record<Graha, Motion>',
      vargas: 'Divisional charts by D-number with access and stability',
      convention: 'VedicFacts.convention',
    },
    screens: ['home', 'panchang'],
    namespace: 'vedic',
    featureFlag: 'engine.vedic',
    computeFacts(input: VedicInput, _clock?: ZonedClock): VedicFacts {
      const { latitude, longitude, timePrecision, nodeType = 'mean' } = input;
      if (
        !Number.isFinite(latitude) ||
        Math.abs(latitude) >= 90 ||
        !Number.isFinite(longitude) ||
        Math.abs(longitude) > 180 ||
        !['known', 'approximate', 'unknown'].includes(timePrecision) ||
        !['mean', 'true'].includes(nodeType)
      )
        throw new RangeError('Invalid birthplace or convention');
      const { utc, jdUt } = birthEpoch(
        input.birthInstantUtc,
        input.timeZone,
        timePrecision,
      );
      const nodeOrbit = nodeType === 'mean' ? 'meanNode' : 'trueNode';
      function measure(at: number) {
        const node = port.longitude(at, nodeOrbit, 'lahiri');
        const measurements = {} as Record<Graha, typeof node>;
        for (const planet of planets) {
          const body = port.longitude(at, planet, 'lahiri');
          if (body.flag !== node.flag)
            throw new Error('Mixed ephemerides in one chart');
          measurements[planet] = body;
        }
        measurements.rahu = node;
        measurements.ketu = {
          ...node,
          longitude: (node.longitude + 180) % 360,
        };
        const asc =
          timePrecision === 'unknown'
            ? null
            : port.ascendant(at, latitude, longitude, 'lahiri');
        const longitudes = { lagna: asc } as Longitudes;
        for (const g of Object.keys(measurements) as Graha[])
          longitudes[g] = measurements[g].longitude;
        return { measurements, longitudes, flag: node.flag };
      }
      const central = measure(jdUt);
      const asc = central.longitudes.lagna;
      const risingSign = asc === null ? null : Math.floor(asc / 30);
      function position(degrees: number): Position {
        if (!(degrees >= 0 && degrees < 360))
          throw new RangeError('Expected longitude in [0, 360)');
        const sign = Math.floor(degrees / 30);
        const quarter = Math.floor((degrees * 3) / 10);
        return {
          longitude: degrees,
          sign: sign + 1,
          house:
            risingSign === null ? null : ((sign - risingSign + 12) % 12) + 1,
          nakshatra: { ...nakshatras[Math.floor(quarter / 4)] },
          pada: (quarter % 4) + 1,
        };
      }
      const grahas = {} as Record<Graha, Motion>;
      for (const g of Object.keys(central.measurements) as Graha[]) {
        const { longitude, speed } = central.measurements[g];
        grahas[g] = { ...position(longitude), speed, retrograde: speed < 0 };
      }
      const observations = new Map<number, ReturnType<typeof measure>>([
        [jdUt, central],
      ]);
      function observe(at: number) {
        const cached = observations.get(at);
        if (cached) return cached;
        const sample = measure(at);
        if (sample.flag !== central.flag)
          throw new Error('Ephemeris changed inside the sensitivity window');
        observations.set(at, sample);
        return sample;
      }
      // A station can cross a boundary twice between adjacent observations.
      // Locate the turning point by the sign of the longitude speed.
      let start = jdUt - 300 / 86400;
      for (let seconds = -270; seconds <= 300; seconds += 30) {
        const end = jdUt + seconds / 86400;
        const left = observe(start).measurements;
        const right = observe(end).measurements;
        for (const g of [...planets, 'rahu'] as const) {
          if (left[g].speed * right[g].speed >= 0) continue;
          let lo = start,
            hi = end;
          while ((hi - lo) * 86400 > 0.001) {
            const mid = (lo + hi) / 2;
            if (mid === lo || mid === hi) break;
            if (observe(mid).measurements[g].speed < 0 === left[g].speed < 0)
              lo = mid;
            else hi = mid;
          }
        }
        start = end;
      }
      const samples = [...observations]
        .sort(([a], [b]) => a - b)
        .map(([, sample]) => sample.longitudes);
      return {
        vargas: computeVargas(
          methods,
          central.longitudes,
          samples,
          central.flag,
          timePrecision,
        ),
        workingInstantUtc: utc,
        julianDayUt: jdUt,
        ayanamsa: port.lahiriAyanamsa(jdUt),
        lagna: asc === null ? null : position(asc),
        grahas,
        convention: {
          ayanamsaId: 'lahiri',
          siderealMode: 1,
          nodeType,
          houseSystem: 'whole-sign',
          calendar: 'proleptic-gregorian',
          ephemerisFlag: central.flag,
          timePrecision,
        },
      };
    },
  } satisfies EngineModule<VedicInput, VedicFacts> & {
    computeStrength(input: StrengthInput): ReturnType<typeof computeStrength>;
    computeYogini(input: YoginiInput): ReturnType<typeof computeYogini>;
    computeChara(input: CharaInput): ReturnType<typeof computeChara>;
    computePanchang(input: PanchangInput): ReturnType<typeof computePanchang>;
    computeVimshottari(
      input: VimshottariInput,
    ): ReturnType<typeof computeVimshottari>;
  };
  return engine;
}
