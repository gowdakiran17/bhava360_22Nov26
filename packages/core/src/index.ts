export type Result<T> = { ok: true; value: T } | { ok: false; reason: string };

export interface ZonedClock {
  readonly instantUtc: string;
  readonly timeZone: string;
}

export function calendarDate(clock: ZonedClock): string {
  if (!clock.instantUtc.endsWith('Z')) throw new Error('Expected a UTC instant');
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: clock.timeZone, year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(new Date(clock.instantUtc));
}

export interface EngineModule<Input, Facts> {
  id: string;
  inputs: readonly (keyof Input)[];
  factsSchema: Readonly<Record<keyof Facts, string>>;
  screens: readonly string[];
  namespace: string;
  featureFlag: string;
  computeFacts(input: Input, clock: ZonedClock): Facts;
}

// Only this explicit allowlist crosses the consumer response boundary.
export function toPublicProjection(reading: { text: string; evidence: readonly string[] }) {
  return { text: reading.text };
}
export { resolveBirth } from './birth';
export * from './ephemeris';
