import { readFileSync } from 'node:fs';
import { globSync } from 'node:fs';
import { expect, it } from 'vitest';
import { calendarDate, toPublicProjection } from '../packages/core/src';
import { GET } from '../apps/api/app/health/route';

it('checks engine sources for implicit or local time', () => {
  const sources = [...globSync('packages/engine-*/src/**/*.ts'), ...globSync('packages/ephemeris-swiss/src/**/*.ts'), 'packages/core/src/ephemeris.ts'];
  expect(sources.length).toBeGreaterThanOrEqual(5);
  for (const path of sources) {
    expect(readFileSync(path, 'utf8'), path).not.toMatch(/\bDate\b|process\.env\.TZ|\.get(?:Date|Day|FullYear|Hours|Milliseconds|Minutes|Month|Seconds|TimezoneOffset|Year)\s*\(|\.toLocale(?:Date|Time)String\(/);
  }
});
it('uses the injected zone across midnight', () => {
  expect(calendarDate({ instantUtc: '2000-01-01T20:00:00Z', timeZone: 'Asia/Kolkata' })).toBe('2000-01-02');
});
it('allows only consumer fields', () => {
  expect(toPublicProjection({ text: 'example', evidence: ['test'] })).toEqual({ text: 'example' });
});
it('exposes only health status', async () => {
  expect(await GET().json()).toEqual({ status: 'ok' });
});
