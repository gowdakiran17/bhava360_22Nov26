import { readFileSync } from 'node:fs';

export interface Nakshatra {
  id: string;
  name: string;
  number: number;
  lord: string;
}
export function loadNakshatras(): Nakshatra[] {
  const source = new URL(
    '../../../kb/dist-json/admin/vedic.json',
    import.meta.url,
  );
  const data = JSON.parse(readFileSync(source, 'utf8'));
  const entries: { id: string; number: number; vimshottari_lord: string }[] =
    data.resources['vedic/nakshatras/catalog.yaml'].nakshatras;
  if (entries.length !== 27) throw new Error('Expected 27 nakshatras');
  return [...entries]
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
}
