import {
  birthEpoch,
  type EngineModule,
  type EphemerisPort,
  type EphemerisFlag,
  type Precision,
  type ZonedClock,
} from '@bhava360/core';
import { loadNakshatras, type Nakshatra } from './catalogue';

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

export function createVedicEngine(port: EphemerisPort) {
  const catalogue = loadNakshatras();
  return {
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
      const asc =
        timePrecision === 'unknown'
          ? null
          : port.ascendant(jdUt, latitude, longitude, 'lahiri');
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
          nakshatra: { ...catalogue[Math.floor(quarter / 4)] },
          pada: (quarter % 4) + 1,
        };
      }
      const node = port.longitude(
        jdUt,
        nodeType === 'mean' ? 'meanNode' : 'trueNode',
        'lahiri',
      );
      function motion(degrees: number, speed: number): Motion {
        return { ...position(degrees), speed, retrograde: speed < 0 };
      }
      const grahas = {} as Record<Graha, Motion>;
      for (const planet of planets) {
        const measured = port.longitude(jdUt, planet, 'lahiri');
        if (measured.flag !== node.flag)
          throw new Error('Mixed ephemerides in one chart');
        grahas[planet] = motion(measured.longitude, measured.speed);
      }
      grahas.rahu = motion(node.longitude, node.speed);
      grahas.ketu = motion((node.longitude + 180) % 360, node.speed);
      return {
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
          ephemerisFlag: node.flag,
          timePrecision,
        },
      };
    },
  } satisfies EngineModule<VedicInput, VedicFacts>;
}
