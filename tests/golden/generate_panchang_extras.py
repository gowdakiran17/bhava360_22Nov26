"""Offline reference using pyswisseph/Moshier, angular root refinement and elapsed seconds."""
import json
from datetime import datetime, time, timedelta, timezone
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

import swisseph as swe

from generate_vedic import FIXTURES, FLAGS

HERE = Path(__file__).resolve().parent
KB = json.loads((HERE.parents[1] / "kb/dist-json/admin/vedic.json").read_text())["resources"]
DAY = KB["vedic/panchang/day-night.yaml"]
EIGHTHS = KB["vedic/panchang/limbs.yaml"]["day_eighths_sunday_first"]
MONTHS = KB["vedic/panchang/calendar-profiles.yaml"]["amanta_months_by_entered_sign"]
SUN, MOON = swe.SUN, swe.MOON
SYNODIC = 29.53059


def jd(dt):
    return 2440587.5 + dt.timestamp() / 86400


def seconds(t):
    return None if t is None else round((t - 2440587.5) * 86400, 3)


@lru_cache(maxsize=16384)
def position(at, body):
    return swe.calc_ut(at, body, FLAGS)[0]


def phase(at):
    return (position(at, MOON)[0] - position(at, SUN)[0]) % 360


def conjunction_or_tithi(guess, angle):
    """Newton iteration using measured relative speed, independent of engine bisection."""
    for _ in range(10):
        error = (phase(guess) - angle + 180) % 360 - 180
        change = error / (position(guess, MOON)[3] - position(guess, SUN)[3])
        guess -= change
        if abs(change) < 1e-9:
            break
    return guess


def ingress_after(t):
    index = (int(position(t, SUN)[0] // 30) + 1) % 12
    return swe.solcross_ut(index * 30, t, FLAGS), index


def month(at):
    start = conjunction_or_tithi(at - phase(at) / 360 * SYNODIC, 0)
    end = conjunction_or_tithi(start + SYNODIC, 0)
    first, index = ingress_after(start)
    following, second = ingress_after(first + 0.01)
    names = [MONTHS[index]]
    if first >= end:
        kind = "adhika"
    elif following < end:
        kind = "kshaya"
        names.append(MONTHS[second])
    else:
        kind = "ordinary"
    return kind, names, start, end


def reference(label, day, clock, zone, lat, lon):
    local = datetime.fromisoformat(day + "T" + clock).replace(tzinfo=ZoneInfo(zone))
    at = jd(local)
    midnight = datetime.combine(local.date(), time(), local.tzinfo)
    weekday = local.isoweekday() % 7

    def event(body, bits, offset=0):
        start = jd(midnight + timedelta(days=offset))
        end = jd(midnight + timedelta(days=offset + 1))
        status, values = swe.rise_trans(start, body, bits, (lon, lat, 0), 1013.25, 15, swe.FLG_MOSEPH)
        return values[0] if status == 0 and start <= values[0] < end else None

    rise, sunset = event(SUN, swe.CALC_RISE), event(SUN, swe.CALC_SET)
    prev_set, next_rise = event(SUN, swe.CALC_SET, -1), event(SUN, swe.CALC_RISE, 1)
    windows = None
    if None not in (prev_set, rise, sunset, next_rise) and prev_set < rise < sunset < next_rise:
        def partitions(start, end, n):
            return [seconds(start + (end-start)*i/n) for i in range(n+1)]

        def window(start, end, n, slot):
            return partitions(start, end, n)[slot-1:slot+1]

        def sequence(cycle, first, count, step=1):
            return [cycle[(cycle.index(first) + i*step) % len(cycle)] for i in range(count)]

        windows = {key: window(rise, sunset, 8, EIGHTHS[table][weekday])
                   for key, table in [('rahuKaal','rahu'), ('yamaganda','yamaganda'), ('gulika','gulika')]}
        windows.update(abhijit=window(rise, sunset, 15, 8), brahma=window(prev_set, rise, 15, 14),
                       hours=partitions(rise,sunset,12)[:-1]+partitions(sunset,next_rise,12),
                       lords=sequence(DAY["hora_cycle"], ["sun","moon","mars","mercury","jupiter","venus","saturn"][weekday],24),
                       day=partitions(rise,sunset,8), night=partitions(sunset,next_rise,8))
        for side, cycle in [('day','choghadiya_order'), ('night','night_cycle')]:
            windows[side+'Labels'] = sequence(DAY[cycle], DAY[side+'_first_sun_through_sat'][weekday],8,DAY[side+'_step'])

    kind, names, start, end = month(at)
    dark_names = month(end+1)[1] if phase(at) >= 180 else names
    anomaly = None
    if rise is not None and next_rise is not None:
        first, last = (int(phase(t)//12)+1 for t in (rise,next_rise))
        jump = (last-first)%30
        anomaly = dict(first=first, next=last, kind=['adhika','ordinary','kshaya'][min(2,jump)],
                       skipped=[(first+i-1)%30+1 for i in range(1,jump)])

    findings = {}
    for profile in ('amanta','purnimanta'):
        festivals = []
        def resolved(t):
            k, _, _, finish = month(t)
            return k != 'kshaya' and (profile == 'amanta' or phase(t)<180 or month(finish+1)[0]!='kshaya')
        if rise is not None and resolved(rise):
            number = int(phase(rise)//12)+1
            for name, indices in [('ekadashi',[11,26]),('purnima',[15]),('amavasya',[30])]:
                if number in indices:
                    festivals.append(name)
        if rise is not None and next_rise is not None:
            ingress, _ = ingress_after(rise)
            if ingress < next_rise and resolved(ingress):
                festivals.append('sankranti')
            # Select the eligible sunrise(s) for the Pratipada of the first Chaitra.
            for nm in (start,end):
                if month(nm+0.1)[1]==['chaitra'] and month(nm-0.1)[1]!=['chaitra']:
                    finish = conjunction_or_tithi(nm+1,12)
                    candidates = [event(SUN,swe.CALC_RISE,i) for i in (-1,0,1)]
                    matching = [v for v in candidates if v is not None and nm<=v<finish]
                    if (matching and min(matching)==rise) or (not matching and rise<nm<finish<=next_rise):
                        festivals.append('ugadi')
            if sunset is not None and rise < sunset < next_rise:
                evening_end = sunset+(next_rise-sunset)/5
                for number in (13,28,30):
                    target = (number-1)*12
                    delta = (target-phase(sunset)+180)%360-180
                    begin = conjunction_or_tithi(sunset+delta*SYNODIC/360,target)
                    finish = conjunction_or_tithi(begin+1,(target+12)%360)
                    if max(begin,sunset)>=min(finish,evening_end) or not resolved(max(begin,sunset)+1e-9):
                        continue
                    if number!=30:
                        festivals.append('pradosh')
                    elif month(begin+0.1)[:2]==('ordinary',['ashvina']):
                        later = event(SUN,swe.CALC_SET,1)
                        if later is not None and finish<=later:
                            festivals.append('deepavali')
        findings[profile] = sorted(festivals)

    return dict(label=label,instantUtc=local.astimezone(timezone.utc).isoformat().replace('+00:00','Z'),timeZone=zone,latitude=lat,longitude=lon,
                date=day,moonrise=seconds(event(MOON,swe.CALC_RISE)),moonset=seconds(event(MOON,swe.CALC_SET)),
                windows=windows,anomaly=anomaly,kind=kind,names=names,
                purnimanta=dark_names[0] if len(dark_names)==len(names)==1 else None,
                start=seconds(start),end=seconds(end),festivals=findings)


if __name__ == '__main__':
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    india='Asia/Kolkata'
    rows=[reference(name,day,clock,india,lat,lon) for name,day,clock,_,lat,lon in FIXTURES]
    rows.append(dict(rows[-1],label='Dev unknown-time (working noon)'))
    rows.extend([reference('polar','2001-06-21','12:00','UTC',70,0),
                 reference('DST transition','2024-03-10','12:00','America/Los_Angeles',34,-118)])
    for day in ['1988-03-18','1994-04-11','1994-04-12','2024-04-07','2024-04-24','2024-04-30','2024-04-05','2024-04-06','2024-04-08','2024-04-09','2024-04-13','2024-04-14',
                '2024-04-19','2024-04-21','2024-04-23','2024-10-31','2024-11-01','2023-08-01','1983-01-20']:
        rows.append(reference('calendar '+day,day,'12:00',india,12.97,77.59))
    # Keep each measurement series together so changes can be reviewed row by row.
    payload = {"source": "pyswisseph " + version("pyswisseph") + " Moshier/Lahiri", "rows": rows}
    (HERE / "panchang_extras.json").write_text(json.dumps(payload, indent=2) + "\n")
