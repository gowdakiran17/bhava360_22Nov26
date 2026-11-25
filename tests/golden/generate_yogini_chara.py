"""Offline Moshier/Lahiri reference. Offsets are measured in the selected tree's years."""
import json
from datetime import datetime, time, timedelta, timezone
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

import swisseph as swe

from generate_vedic import BODIES, FIXTURES, FLAGS

SIGNS = "aries taurus gemini cancer leo virgo libra scorpio sagittarius capricorn aquarius pisces".split()
LORDS = "mars venus mercury moon sun mercury venus mars jupiter saturn saturn jupiter".split()
YOGINIS = "Mangala Pingala Dhanya Bhramari Bhadrika Ulka Siddha Sankata".split()
EVEN = {3, 4, 5, 9, 10, 11}
EXALTED = dict(sun=0, moon=1, mars=9, mercury=5, jupiter=3, venus=11, saturn=6)
ANTAR_FORWARD = {0, 4, 5, 6, 10, 11}


def jd(t):
    return 2440587.5 + t.timestamp() / 86400


def yogini(moon, stable):
    if not stable:
        return None
    arc = moon * 3600
    mansion, offset = divmod(arc, 48000)
    one_based = (int(mansion) + 1 + 3) % 8 or 8
    elapsed = offset / 48000 * one_based
    majors = []
    cursor = -elapsed
    for i in range(8):
        lord = (one_based - 1 + i) % 8
        years = lord + 1
        majors.append([YOGINIS[lord], cursor, cursor + years])
        cursor += years
    return dict(star=int(mansion)+1, elapsed=elapsed, balance=one_based-elapsed, majors=majors)


def chara(seed, chart):
    def years(s, g):
        direction = -1 if s in EVEN else 1
        distance = next(n for n in range(1, 13) if (s+n*direction) % 12 == chart[g])
        if g in EXALTED:
            distance += (chart[g] == EXALTED[g]) - (chart[g] == (EXALTED[g]+6) % 12)
        return distance

    def support(source, dest):
        if source == dest:
            return True
        # Movable to fixed, fixed to movable (omit adjacent signs); dual to other dual.
        offsets = ((4, 7, 10), (2, 5, 8), (3, 6, 9))[source % 3]
        return (dest-source) % 12 in offsets

    def owner(s):
        first = LORDS[s]
        other = {7: 'ketu', 10: 'rahu'}.get(s)
        if not other:
            return first
        if chart[other] == s:
            return first
        if chart[first] == s:
            return other

        def rank(g):
            place = chart[g]
            helpers = ['mercury', 'jupiter', LORDS[place]]
            return (sum(pos == place for body, pos in chart.items() if body != g),
                    sum(support(chart[helper], place) for helper in helpers),
                    EXALTED.get(g) == place, place % 3, years(s, g))

        if rank(first) == rank(other):
            return None
        return max((first, other), key=rank)

    direction = -1 if (seed+8) % 12 in EVEN else 1
    majors = []
    cursor = 0
    for cycle in (1, 2):
        for i in range(12):
            sign = (seed + direction*i) % 12
            lord = owner(sign)
            if lord is None:
                return None
            first = min(12, years(sign, lord))
            span = first if cycle == 1 else 12-first
            if span:
                step = 1 if sign in ANTAR_FORWARD else -1
                children = [SIGNS[(sign+step*j) % 12] for j in range(1, 13)]
                majors.append(dict(sign=SIGNS[sign], lord=lord, start=cursor, end=cursor+span,
                                   cycle=cycle, children=children))
                cursor += span
    assert cursor == 144
    return majors


def reference(fixture, unknown=False):
    name, date, clock, _, latitude, longitude = fixture
    zone = ZoneInfo('Asia/Kolkata')
    birth = datetime.fromisoformat(date+'T'+clock).replace(tzinfo=zone)
    at = jd(birth)
    bounds = [birth-timedelta(minutes=2), birth+timedelta(minutes=2)]
    if unknown:
        midnight = datetime.combine(birth.date(), time(), zone)
        bounds = [midnight, midnight+timedelta(days=1, microseconds=-1000)]

    def angle(t, g):
        return swe.calc_ut(t, BODIES[g], FLAGS)[0][0]

    def asc(t):
        return int(swe.houses_ex(t, latitude, longitude, b'W', swe.FLG_SIDEREAL)[1][0] // 30)

    moon = angle(at, 'moon')
    stable = all(int(angle(jd(b),'moon')*27/360) == int(moon*27/360) for b in bounds)
    chart = {g:int(angle(at, g)//30) for g in BODIES}
    chart['ketu'] = (chart['rahu']+6) % 12
    seed = asc(at)
    lagna_stable = not unknown and all(asc(jd(bounds[0])+i/86400) == seed for i in range(241))
    return dict(label=name+(' unknown' if unknown else ''),timePrecision='unknown' if unknown else 'known',
                birthInstantUtc=birth.astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
                latitude=latitude, longitude=longitude, timeZone=zone.key, jd=at,
                yogini=yogini(moon, stable), seed=SIGNS[seed] if lagna_stable else None,
                chara=chara(seed,chart) if lagna_stable else None)


if __name__ == '__main__':
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    rows = [reference(f) for f in FIXTURES] + [reference(FIXTURES[-1], True)]
    output = dict(source='pyswisseph '+version('pyswisseph')+' / Moshier / Lahiri / mean node',rows=rows)
    Path(__file__).with_name('yogini_chara.json').write_text(json.dumps(output, indent=2)+'\n')
