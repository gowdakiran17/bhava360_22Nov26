import { Temporal } from '@js-temporal/polyfill';

export function resolveBirth(
  date: string,
  time: string,
  zone: string,
  choice?: 'earlier' | 'later',
) {
  const local = Temporal.PlainDateTime.from(date + 'T' + time);
  const earlier = local.toZonedDateTime(zone, { disambiguation: 'earlier' });
  const later = local.toZonedDateTime(zone, { disambiguation: 'later' });
  if (!earlier.toPlainDateTime().equals(local)) throw new RangeError('invalid');
  if (!choice && earlier.epochMilliseconds !== later.epochMilliseconds)
    throw new RangeError('chooseTime');
  return (choice === 'later' ? later : earlier).toInstant().toString();
}
