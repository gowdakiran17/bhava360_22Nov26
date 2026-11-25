"""Generate offline reference instants using pyswisseph and the five synthetic charts."""
import json
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from importlib.metadata import version
from zoneinfo import ZoneInfo

import swisseph as swe
from generate_vedic import FIXTURES, FLAGS

UTC = timezone.utc
ORDER = ["ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury"]
YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]


def jd(instant):
    return 2440587.5 + instant.timestamp() / 86400


def reference(label, local, zone, lat, lon, traditional=False):
    instant = local.astimezone(UTC)
    at = jd(instant)
    midnight = datetime.combine(local.date(), time(), ZoneInfo(zone))

    def event(start, bits):
        code, values = swe.rise_trans(jd(start), swe.SUN, bits, (lon, lat, 0), 1013.25, 15, swe.FLG_MOSEPH)
        return values[0] if code == 0 and values[0] < jd(start + timedelta(days=1)) else None

    rise_bits = swe.CALC_RISE | (swe.BIT_DISC_CENTER | swe.BIT_NO_REFRACTION if traditional else 0)
    rise = event(midnight, rise_bits)
    vara = None
    if rise is not None:
        last = midnight if rise <= at else midnight - timedelta(days=1)
        if event(last, rise_bits) is not None:
            vara = last.isoweekday() % 7

    def angles(t):
        sun, moon = [swe.calc_ut(t, body, FLAGS)[0][0] for body in (swe.SUN, swe.MOON)]
        return [(moon-sun) % 360, moon, (moon+sun) % 360, (moon-sun) % 360]

    limbs = {}
    for i, (name, count) in enumerate(zip(('tithi', 'nakshatra', 'yoga', 'karana'), (30, 27, 27, 60))):
        def index(t):
            return int(angles(t)[i] * count / 360)
        current = index(at)
        crossings = []
        for direction in (-1, 1):
            inside = at
            outside = at + direction / 8
            while index(outside) == current:
                inside, outside = outside, outside + direction / 8
            for _ in range(38):
                mid = (inside + outside) / 2
                if index(mid) == current:
                    inside = mid
                else:
                    outside = mid
            crossings.append((inside + outside) / 2)
        limbs[name] = [current, *crossings]
    phase = angles(at)[1] * 27 / 360
    first = int(phase) % 9
    days = YEARS[first] * 365.25
    origin = at - (phase % 1) * days
    active = []
    start, duration, lord = origin, days, first
    for depth in range(4):
        active.append([ORDER[lord], start, start + duration])
        for offset in range(9):
            child = (lord + offset) % 9
            length = duration * YEARS[child] / 120
            if at < start + length:
                lord, duration = child, length
                break
            start += length
    return dict(label=label, instantUtc=instant.isoformat().replace('+00:00','Z'), timeZone=zone,
                latitude=lat, longitude=lon, traditional=traditional, sunrise=rise, sunset=event(midnight,swe.CALC_SET),
                vara=vara, limbs=limbs, balanceYears=(1-phase%1)*YEARS[first], active=active)


if __name__ == '__main__':
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    zone = 'Asia/Kolkata'
    rows = []
    for name, day, clock, _, lat, lon in FIXTURES:
        local = datetime.fromisoformat(day+'T'+clock).replace(tzinfo=ZoneInfo(zone))
        rows.append(reference(name, local, zone, lat, lon))
        if name == 'Asha':
            rows.append(reference('traditional', local, zone, lat, lon, True))
    for label, instant, zone, lat, lon in [
        ('polar','2001-06-21T12:00:00Z','Etc/UTC',70,0),
        ('spring','2001-04-01T10:01:00Z','America/Los_Angeles',34,-118),
        ('fall-first','2001-10-28T08:30:00Z','America/Los_Angeles',34,-118),
        ('fall-second','2001-10-28T09:30:00Z','America/Los_Angeles',34,-118),
    ]:
        rows.append(reference(label, datetime.fromisoformat(instant.replace('Z','+00:00')).astimezone(ZoneInfo(zone)),zone,lat,lon))
    Path(__file__).with_name('panchang_dasha.json').write_text(json.dumps(
        dict(source='pyswisseph '+version('pyswisseph')+' / Moshier / Lahiri', rows=rows),indent=2)+'\n')
