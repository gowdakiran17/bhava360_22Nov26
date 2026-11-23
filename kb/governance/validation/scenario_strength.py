"""Regenerate the unpublished S1 worksheet with the KB dev environment and no network.

Run this file from any directory. Print YAML for the scenario section of worked-reference.yaml.
The reference uses static varga lookup rows and its own arithmetic, independent of shadbala.recompute.
"""
from bisect import bisect_right
from pathlib import Path
import yaml
import swisseph as swe

KB = Path(__file__).resolve().parents[2]
ORDER = 'sun moon mars mercury jupiter venus saturn'.split()
SIX = 'sthana dig kala cheshta naisargika drik'.split()


def read(path):
    return yaml.safe_load((KB / path).read_text())


def inputs():
    # Artificial test epoch at J2000 and an invented observing point. No birth record.
    jd, place = 2451545.0, (15., 12., 0.)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    backend = swe.FLG_MOSEPH
    ayan = swe.get_ayanamsa_ex_ut(jd, backend)[1]
    asc, mc = swe.houses_ex(jd, place[1], place[0], b'W', swe.FLG_SIDEREAL)[1][:2]
    chart = dict(instant=jd, asc=asc, mc=mc, longitude={}, latitude={}, declination={}, mean={})
    for name in ORDER + ['rahu']:
        planet = swe.MEAN_NODE if name == 'rahu' else getattr(swe, name.upper())
        pos, flags = swe.calc_ut(jd, planet, backend | swe.FLG_SIDEREAL)
        assert flags & backend
        chart['longitude'][name], chart['latitude'][name] = pos[:2]
        if name == 'rahu':
            chart['longitude']['ketu'] = (pos[0]+180) % 360
            continue
        chart['declination'][name] = swe.calc_ut(jd, planet, backend | swe.FLG_EQUATORIAL)[0][1]
        if name != 'moon':
            # Use heliocentric mean longitude of date. Mean Sun opposes mean Earth.
            obj = swe.EARTH if name == 'sun' else planet
            mean = swe.get_orbital_elements(jd+swe.deltat(jd), obj, backend)[9]
            chart['mean'][name] = (mean-ayan+(180 if name=='sun' else 0)) % 360
    def event(after, kind):
        status, times = swe.rise_trans(after, swe.SUN, kind, place, 1013.25, 15, backend)
        assert status == 0
        return times[0]
    rise = event(jd-.5, swe.CALC_RISE)
    chart['sunrise_sunset_next'] = [rise, event(rise,swe.CALC_SET), event(rise+.01,swe.CALC_RISE)]
    chart['solar_hour'] = ((jd+.5+place[0]/360+swe.time_equ(jd))%1)*24
    chart.update(epoch_weekday=6, completed_days=0)  # scenario cycle begins at this Saturday sunrise
    return chart


def worksheet(c):
    lon, mean = c['longitude'], c['mean']
    signs = read('vedic/signs/catalog.yaml')['signs']
    ids = [s['id'] for s in signs]
    methods = {r['chart']:r for r in read('vedic/vargas/methods.yaml')['methods']}
    def separation(a,b):
        d = (a-b)%360
        return min(d,360-d)
    def division(g,n):
        s, deg = divmod(lon[g],30)
        m = methods['D'+str(n)]
        if n == 30:
            bounds = m['degree_boundaries'][('odd','even')[int(s)%2]]
            part = bisect_right(bounds,deg)-1
        else:
            part = int(deg*n/30)
        return ids.index(m['sign_lookup'][ids[int(s)]][part])
    def cast(g, target):
        angle = (target-lon[g])%360
        weights = [0,0,15,45,30,0,60,45,30,15,0,0]
        knots = [0,30,60,90,120,150,180,210,240,270,300,360]
        for special in {'mars':[90,210], 'jupiter':[120,240], 'saturn':[60,270]}.get(g,[]):
            weights[knots.index(special)] = 60
        i = bisect_right(knots,angle)-1
        return weights[i]+(weights[i+1]-weights[i])*(angle-knots[i])/(knots[i+1]-knots[i])
    negative = {'sun','mars','saturn','rahu','ketu'}
    if not 0 < (lon['moon']-lon['sun'])%360 <= 180:
        negative.add('moon')
    if any(lon[p]//30 == lon['mercury']//30 for p in negative):
        negative.add('mercury')
    rise, setting, _ = c['sunrise_sunset_next']
    daylight = (c['instant']-rise)/(setting-rise)
    assert 0 <= daylight < 1 and c['epoch_weekday'] == 6 and c['completed_days'] == 0
    assert all(separation(lon[a],lon[b])>=1 for i,a in enumerate(ORDER[2:]) for b in ORDER[2:][i+1:])
    phase = separation(lon['moon'],lon['sun'])/3
    rows = {}
    for i,g in enumerate(ORDER):
        sign, deg = divmod(lon[g],30)
        planet = read('vedic/planets/'+g+'.yaml')['graha']
        dignity = planet['dignity']
        low, peak = next(iter(dignity['debilitation_peak_degrees'].items()))
        position = separation(lon[g],ids.index(low)*30+peak)/3
        for n in [1,2,3,7,9,12,30]:
            idx = division(g,n)
            ruler = signs[idx]['lord']
            lo,hi = dignity['moolatrikona_degree_limits'].get(ids[idx],(0,0))
            if n==1 and lo<=deg<hi:
                position += 45
            elif ruler==g:
                position += 30
            else:
                natural = planet['natural_friendships']
                score = int(ruler in natural['friends'])-int(ruler in natural['enemies'])
                friendly = (int(lon[ruler]//30-sign)%12+1) in (2,3,4,10,11,12)
                position += [2,4,10,15,20][2+score+(1 if friendly else -1)]
        position += sum(15 for n in (1,9) if division(g,n)%2 == (g in ['moon','venus']))
        position += [60,30,15][int(sign-c['asc']//30)%3]
        position += 15*(g in [('sun','mars','jupiter'),('mercury','saturn'),('moon','venus')][int(deg//10)])
        weak = [c['mc']+180,c['mc'],c['mc']+180,c['asc']+180,c['asc']+180,c['mc'],c['asc']][i]
        dig = separation(lon[g],weak)/3
        noon = 60-5*abs(c['solar_hour']-12)
        dec = c['declination'][g]
        adj = abs(dec) if g=='mercury' else -dec if g in ('saturn','moon') else dec
        ayana = 1.25*(24+max(-24,min(24,adj)))
        paksha = phase if g in ('moon','mercury','venus','jupiter') else 60-phase
        kala = (60 if g=='mercury' else noon if g in ('sun','venus','jupiter') else 60-noon)+ayana+paksha
        kala += 60*(g in ('jupiter',('mercury','sun','saturn')[int(daylight*3)]))
        kala += (15+30+45)*(g=='saturn')
        kala += 60*(g=='saturn jupiter mars sun venus mercury moon'.split()[int(daylight*12)%7])
        if g in ('sun','moon'):
            cheshta = ayana if g=='sun' else paksha
        else:
            slow,fast = (mean['sun'],mean[g]) if g in ('mercury','venus') else (mean[g],mean['sun'])
            cheshta = separation(slow+((lon[g]-slow+180)%360-180)/2,fast)/3
        natural = [7,6,2,3,4,5,1][i]*60/7
        drik = sum(cast(p,lon[g])*(-1 if p in negative else 1) for p in ORDER if p!=g)/4
        rows[g] = dict(zip(SIX,[position,dig,kala,cheshta,natural,drik]))
    return rows


if __name__=='__main__':
    chart = inputs()
    print(yaml.safe_dump(dict(name='Scenario S1', verification='unverified-pending-source',
          synthetic=True, jd_ut=2451545., observer_east_north_m=[15,12,0], profile='parashari-strength-v1',
          ayanamsa='SE_SIDM_LAHIRI', backend='SEFLG_MOSEPH', swiss_version=swe.version,
          generator='governance/validation/scenario_strength.py', inputs=chart,
          absolute_tolerance_virupas=dict.fromkeys(SIX,0.000001), expected=worksheet(chart)),sort_keys=False))
