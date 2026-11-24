"""Reference evaluation of pre-partitioned election intervals; all bounds are local aware instants."""
from datetime import datetime


def slots(begin, end, count, offsets, length=1):
    if begin is None or end is None or end <= begin:
        return None
    unit = (end - begin) / count
    return [(begin + unit * i, begin + unit * (i + length)) for i in offsets]


def intersect(window, spans):
    return any(max(window[0], a) < min(window[1], b) for a, b in spans)


def star_slots(begin, end, star, table):
    row = table['stars'][star]
    return {kind: slots(begin, end, 60, offsets, table['duration_ghatis'])
            for kind, offsets in [('varjyam', row['varjyam']), ('amrit', [row['amrit']])]}


def star_blocked(star, malefic_stars, vedha, table):
    if vedha is True:
        return True
    if star is None or malefic_stars is None:
        return None
    uncertain = vedha is None
    for graha, origin in malefic_stars.items():
        if origin is None:
            uncertain=True
            continue
        count=table['election_latta']['counts'][graha]
        if (origin + (abs(count)-1)*(1 if count>0 else -1))%27==star:
            return True
    return None if uncertain else False


def combinations(table, weekday, star, sun_star, tithi, names):
    active = set()
    if star in table['sarvartha'][weekday]:
        active.add('sarvartha')
    if star == table['amrita_siddhi'][weekday]:
        active.add('amrita-siddhi')
    pushkar = table['pushkar']
    if weekday in pushkar['weekdays'] and (tithi-1)%15+1 in pushkar['paksha_tithis']:
        active.update(kind+'-pushkar' for kind in ('dwi','tri') if star in pushkar[kind])
    if sun_star is not None and 1+(names.index(star)-names.index(sun_star))%27 in table['ravi']['inclusive_star_distances_from_sun']:
        active.add('ravi-yoga')
    for kind in ('guru','ravi'):
        if star==table['pushya']['star'] and weekday==table['pushya'][kind]:
            active.add(kind+'-pushya')
    return active


def classify_extra(c, profile, policy, election, evidence, bounds, days, stars):
    """Return blocking reasons, unknown dependencies, and soft evidence separately."""
    rise, setting, start, end = bounds
    star, tithi, weekday = election['nakshatra'], election['tithi'], election['vara']
    table = policy['interval_table']
    day = slots(rise, setting, 15, [i-1 for i in table['durmuhurta'][weekday]['day']])
    gates = {'durmuhurta': intersect((start,end),day)}
    soft = {}
    ep = c.get('star_interval')
    if ep:
        first,last=map(datetime.fromisoformat,ep)
        if first<=start<end<=last:
            spans=star_slots(first,last,star,table)
            gates['varjyam']=intersect((start,end),spans['varjyam'])
            if any(a<=start<end<=b for a,b in spans['amrit']):
                soft['amrit-kalam']='support'
    for n,key in [(7,'seventh_occupied'),(8,'eighth_occupied'),(12,'twelfth_occupied')]:
        if c.get('occupied_houses') is not None:
            gates[key]=n in c['occupied_houses']
    if gates.get('twelfth_occupied'):
        soft['twelfth']='avoid'
    for label, houses in [('benefic_houses',{1,4,5,7,9,10}),('malefic_houses',{3,6,11})]:
        if houses.intersection(c.get(label,[])):
            soft[label]='support'
    obstruction=star_blocked(stars.index(star),c.get('malefic_star_indices'),c.get('star_vedha'),policy['day_yoga_table'])
    gates.update(star_obstructed=obstruction,rikta_or_new=tithi in (4,9,14,19,24,29,30),
                 partner_tara_or_chandra_unsupportive=any(v!='support' for k,v in evidence.items() if k.startswith(('tara/','chandra/'))))
    active={p['fact'].split('.')[-1] for p in profile['lagna_and_calendar']['hard']}
    band = policy['gandanta']
    gates['gandanta'] = any(abs((c[point]-joint+180)%360-180) < band['halfwidth_deg']
                            for point in ('moon','asc') for joint in band['joints_deg'])
    active.add('gandanta')
    regional = policy['regions']
    for name in profile['lagna_and_calendar']['calendar_switches']:
        if not c.get('region_switches',{}).get(name,regional[name]['default']):
            continue
        if name=='asta':
            if c.get('asta_method')!='visibility-days':
                continue  # angular branch evaluated before classification
            gates[name]=c.get('invisible_luminary')
        elif name=='kharmas':
            gates[name]=int(c['sun']%360//30) in (8,11)
        elif name=='panchaka':
            gates[name]=c['moon']%360>=300
            if gates[name] and profile['activity']=='travel':
                gates[name]=None if c.get('direction') is None else c['direction']=='south'
        else:
            gates[name]=c.get(name)
        active.add(name)
    yogas=policy['day_yoga_table']
    for label in combinations(yogas,weekday,star,stars[int(c['sun']%360*3//40)],tithi,stars):
        soft[label]='support'
    if profile['activity']=='travel' and c.get('direction')==yogas['disha_shoola'][weekday]:
        soft['disha-shoola']='avoid'
    return sorted(k for k in active if gates.get(k)), sorted(k for k in active if gates.get(k) is None), soft
