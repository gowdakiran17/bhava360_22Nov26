import { describe, expect, it } from 'vitest';
import { catalogues, catalogue } from '../packages/i18n/src';

const keys = Object.keys(catalogues.en);
function missing(strings: Record<string, string>) {
  return keys.filter(key => !strings[key]?.trim());
}

describe.each(['kn', 'hi'] as const)('%s catalogue', locale => {
  it('contains every required English key', () => {
    expect(missing(catalogues[locale])).toEqual([]);
  });
  it('detects an omitted translation', () => {
    const { footer, ...incomplete } = catalogues[locale];
    expect(missing(incomplete)).toContain('footer');
  });
});
it('resolves disabled locales to English', () => {
  expect(catalogue('te')).toBe(catalogues.en);
});
