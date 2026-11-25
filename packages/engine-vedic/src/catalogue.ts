import { prepareMethods } from './vargas';
import { readFileSync } from 'node:fs';

export interface Nakshatra {
  id: string;
  name: string;
  number: number;
  lord: string;
}
export type YearClock = 'julian-365.25' | 'savana' | 'mean-gregorian';
export type TithiIndex0 =
  | 0
  | 1
  | 2
  | 3
  | 4
  | 5
  | 6
  | 7
  | 8
  | 9
  | 10
  | 11
  | 12
  | 13
  | 14
  | 15
  | 16
  | 17
  | 18
  | 19
  | 20
  | 21
  | 22
  | 23
  | 24
  | 25
  | 26
  | 27
  | 28
  | 29;
interface LimbTables {
  tithi: {
    index0: TithiIndex0;
    number: number;
    paksha: 'shukla' | 'krishna';
    name: string;
  }[];
  yoga: string[];
  karana: { fixed: Record<string, string>; movable: string[] };
}
interface PeriodTable {
  default_year: YearClock;
  year_days: Record<YearClock, string>;
  lord_order: string[];
  sequence: Record<string, number>;
  cycle_years: number;
  star_width_arcseconds: number;
}
export type Catalogue = ReturnType<typeof loadCatalogue>;
export function loadCatalogue() {
  const source = new URL(
    '../../../kb/dist-json/admin/vedic.json',
    import.meta.url,
  );
  const data = JSON.parse(readFileSync(source, 'utf8'));
  const entries: { id: string; number: number; vimshottari_lord: string }[] =
    data.resources['vedic/nakshatras/catalog.yaml'].nakshatras;
  if (entries.length !== 27) throw new Error('Expected 27 nakshatras');
  const nakshatras: Nakshatra[] = [...entries]
    .sort((a, b) => a.number - b.number)
    .map((entry, i) => {
      const id = 'vedic.nakshatras.' + entry.id;
      const rule = data.rules[id]?.rule;
      if (
        !rule?.title ||
        entry.number !== i + 1 ||
        rule.nakshatra.number !== entry.number ||
        !entry.vimshottari_lord ||
        rule.nakshatra.vimshottari_lord !== entry.vimshottari_lord
      )
        throw new Error('Inconsistent nakshatra metadata for ' + id);
      return {
        id,
        name: rule.title,
        number: entry.number,
        lord: entry.vimshottari_lord,
      };
    });
  const limbs = data.resources['vedic/panchang/limbs.yaml'];
  return {
    tables: data.resources[limbs.tables] as LimbTables,
    widths: limbs.width_arcseconds as Record<
      'tithi' | 'karana' | 'yoga' | 'nakshatra',
      number
    >,
    observer: data.resources['vedic/panchang/rise-set.yaml'].observer as {
      elevation_default_m: number;
      pressure_hpa: number;
      temperature_c: number;
    },
    periods: data.resources[
      'vedic/dashas/vimshottari/periods.yaml'
    ] as PeriodTable,
    nakshatras,
    methods: prepareMethods(
      data.resources['vedic/vargas/methods.yaml'].methods,
    ),
  };
}
