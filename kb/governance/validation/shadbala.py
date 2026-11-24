"""Recompute the KB profile from synthetic astronomical inputs, before display rounding."""
from bisect import bisect_right
from itertools import combinations
from math import isclose, sqrt
import re

GRAHAS = 'sun moon mars mercury jupiter venus saturn'.split()
ROOT = 'vedic/strength/shadbala/'
PREFIX = 'vedic.strength-shadbala.'


def arc(a, b):
    return abs((a-b+180) % 360-180)


def aspect(table, planet, angle, method="interpolated-peak"):
    if angle is None:
        return None
    angle %= 360
    knots = table['knots_degrees']
    weights = [60 if method=='interpolated-peak' and k in table['special'].get(planet, []) else v for k,v in zip(knots,table['common'])]
    i = bisect_right(knots,angle)-1
    bonus = 0
    if method=='fixed-segment':
        if any(k<=angle<k+table['segment_width_degrees'] for k in table['special'].get(planet,[])):
            bonus=table['fixed_segment_bonus'][planet]
    elif method!='interpolated-peak':
        raise ValueError('Unknown special aspect convention')
    return bonus + weights[i] + (weights[i+1]-weights[i])*(angle-knots[i])/(knots[i+1]-knots[i])


def recompute(chart, tables, rules, signs, war_method="modern-kala-transfer", drik_method="interpolated-peak"):
    from varga_charts import calculate
    lon = chart['longitude']
    sign = {g:int(lon[g]//30) for g in GRAHAS}
    angles = {'asc':chart['asc'], 'dsc':(chart['asc']+180)%360, 'mc':chart['mc'], 'ic':(chart['mc']+180)%360}
    rulers = {r['id']:r['lord'] for r in signs}
    sign_names = list(rulers)
    epoch,days = chart['epoch_weekday'],chart['completed_days']
    daylord = GRAHAS[(epoch+days)%7]
    # Bind the current sunrise day, including the following night.
    rise, setting, following = chart['sunrise_sunset_next']
    moment = chart['instant']
    if not rise <= moment < following or not rise < setting < following:
        raise ValueError('Incomplete solar interval')
    day = moment < setting
    start,end = (rise,setting) if day else (setting,following)
    elapsed = (moment-start)/(end-start)
    tri = tables['tribhaga']['day' if day else 'night'][int(3*elapsed)]
    cycle = tables['hora']['order']
    hourlord = cycle[(cycle.index(daylord)+int(12*elapsed)+(0 if day else 12))%7]
    from bhava_bala import benefic, relationship
    nature = {g:benefic(g,lon,tables['natural']) for g in GRAHAS}
    out = {g:{} for g in GRAHAS}
    for g,r in out.items():
        graha = rules['vedic.planets.'+g]['graha']
        dignity = graha['dignity']
        dsign,degree = next(iter(dignity['debilitation_peak_degrees'].items()))
        r['uchcha'] = arc(lon[g],sign_names.index(dsign)*30+degree)/3
        sap = tables['saptavargaja']
        r['saptavargaja'] = 0
        vargas = {}
        for n in sap['divisions']:
            calc = rules[f'vedic.vargas.d{n}-placement']['varga']['calculation']
            vargas[n] = dest = calculate(calc,lon[g],sign_names)
            owner = rulers[dest]
            lo,hi = dignity['moolatrikona_degree_limits'].get(dest,(0,0))
            if n==1 and lo <= lon[g]%30 < hi:
                award = sap['moolatrikona']
            elif owner==g:
                award = sap['own']
            else:
                relations = graha['natural_friendships']
                natural = 'friend' if owner in relations['friends'] else 'enemy' if owner in relations['enemies'] else 'neutral'
                distance = (sign[owner]-sign[g])%12+1
                rel = tables['relationships']
                label = relationship(rel,natural,distance)
                award = sap['relationship_awards'][rel['award_order'].index(label)]
            r['saptavargaja'] += award
        parity = int(g in tables['ojayugma']['even'])
        r['ojayugma'] = tables['ojayugma']['award']*sum(sign_names.index(vargas[n])%2==parity for n in (1,9))
        house_index = (sign[g]-int(chart['asc']//30))%12
        r['kendradi'] = tables['kendradi']['awards'][house_index%3]
        r['drekkana'] = tables['drekkana']['award'] if g in tables['drekkana']['groups'][int(lon[g]%30//10)] else 0
        r['sthana'] = sum(r[k] for k in tables['sthana']['terms'])
        r['dig'] = arc(lon[g],angles[tables['dig']['weak_angle'][g]])/3
        t = chart['solar_hour']%24
        strength = 5*min(t,24-t)
        r['nathonnata'] = strength if g in tables['nathonnata']['day'] else 60-strength if g in tables['nathonnata']['night'] else 60
        phase = arc(lon['moon'],lon['sun'])/3
        r['paksha'] = phase if g in tables['paksha']['bright'] else 60-phase
        r['tribhaga'] = 60 if g in (tri,tables['tribhaga']['always']) else 0
        for k in ('abda','masa','vara'):
            span = tables[k]['span']
            lord = GRAHAS[(epoch+span*(days//span))%7]
            r[k] = tables[k]['award'] if g==lord else 0
        r['hora'] = tables['hora']['award'] if g==hourlord else 0
        dec = chart['declination'][g]
        adjusted = abs(dec) if g=='mercury' else -dec if g in tables['ayana']['south'] else dec
        r['ayana'] = (24+max(-24,min(24,adjusted)))*1.25
        r['yuddha'] = 0
        if g in ('sun','moon'):
            r['cheshta'] = r['ayana' if g=='sun' else 'paksha']
        else:
            fast,slow = chart['mean']['sun'],chart['mean'][g]
            if g in tables['cheshta']['inner']:
                fast,slow = slow,fast
            midpoint = slow+((lon[g]-slow+180)%360-180)/2
            r['cheshta'] = arc(midpoint,fast)/3
        r['naisargika'] = (1+tables['naisargika']['ascending'].index(g))*60/7
        r['drik'] = sum(aspect(tables['drik'],p,(lon[g]-lon[p])%360,drik_method)*(1 if nature[p] else -1)
                        for p in GRAHAS if p!=g)/4 if all(nature[p] is not None for p in GRAHAS if p!=g) else None
    war = rules[tables['yuddha']['winner_rule']]['state']
    pairs = [(a,b) for a,b in combinations(war['eligible'],2) if arc(lon[a],lon[b])<war['maximum_exclusive_degrees']]
    for a,b in pairs:
        lat_a, lat_b = (chart['latitude'].get(g) for g in (a,b))
        overlapping = any(sum(g in pair for pair in pairs)>1 for g in (a,b))
        if overlapping or lat_a is None or lat_b is None or lat_a==lat_b:
            out[a]['yuddha']=out[b]['yuddha']=None
            continue
        pre = [sum(out[g][k] for k in tables['kala']['terms'] if k!='yuddha') for g in (a,b)]
        divisor = 1
        if war_method=='classical-disc-difference':
            diameters = chart.get('disc_arcminutes',{})
            if any(diameters.get(g,0)<=0 for g in (a,b)) or diameters[a]==diameters[b]:
                out[a]['yuddha']=out[b]['yuddha']=None
                continue
            divisor=abs(diameters[a]-diameters[b])
            pre=[v+out[g]['sthana']+out[g]['dig'] for g,v in zip((a,b),pre)]
        elif war_method!='modern-kala-transfer':
            raise ValueError('Unknown war method')
        transfer = abs(pre[0]-pre[1])/divisor*(1 if chart['latitude'][a]>chart['latitude'][b] else -1)
        out[a]['yuddha'],out[b]['yuddha'] = transfer,-transfer
    for g,r in out.items():
        r['kala'] = None if r['yuddha'] is None else sum(r[k] for k in tables['kala']['terms'])
        total = tables['totals']
        r['totals'] = None if any(r[k] is None for k in total['terms']) else sum(r[k] for k in total['terms'])
        r['rupas'] = None if r['totals'] is None else r['totals']/total['virupas_per_rupa']
        r['meets_minimum'] = None if r['rupas'] is None else r['rupas']>=total['minimum_rupas'][g]
        r['ishta'] = sqrt(r['uchcha']*r['cheshta'])
        r['kashta'] = sqrt((60-r['uchcha'])*(60-r['cheshta']))
    return out


def validate_shadbala(rules,read,require):
    cases = read('examples/shadbala-reference.yaml')
    tables = {rid[len(PREFIX):]:r['calculation'] for rid,r in rules.items() if rid.startswith(PREFIX) and 'calculation' in r}
    must = set('sthana uchcha saptavargaja ojayugma kendradi drekkana dig kala nathonnata paksha tribhaga abda masa vara hora ayana yuddha cheshta naisargika drik totals'.split())
    require(tables.keys()==must,'Shadbala component inventory')
    require(tables['totals']['minimum_rupas']==read(ROOT+'components.yaml')['minimum_rupas'],'Shadbala minima')
    require(cases['synthetic'] is True and cases['graha_order']==GRAHAS,'synthetic strength references')
    require(set(cases['fixtures'])=={'Scenario 1','Scenario 2'},'strength fixture identities')
    safe = read(ROOT+'components.yaml')['approved_public_phrases']
    require(all(not re.search(r'\d|[%٪]|\b(?:scores?|points|rupas?|virupas?)\b|अंक|स्कोर|ವಿರೂಪ|ಅಂಕ', text, re.I)
                for phrase in safe for text in phrase.values()), 'qualitative Shadbala phrases only')
    for rid,r in rules.items():
        if not rid.startswith(PREFIX):
            continue
        require(r['user_text'] in safe,rid+' public strength wording')
        if 'calculation' in r:
            require(r['calculation']['access']==['admin','tester'],rid+' numeric visibility')
            require(r['conditions']=={'all':[dict(fact='strength.shadbala.selected_component',op='eq',value=rid[len(PREFIX):])]},rid+' selection')
    tables['natural'] = read('vedic/planets/benefic-profile.yaml')
    tables['relationships'] = read(tables['saptavargaja']['relationship_table'])
    reference = read(ROOT+'worked-reference.yaml')
    scenario = reference['scenario']
    require(scenario['verification']=='unverified-pending-source' and scenario['synthetic']
            and reference['published_raman']['expected_7_by_6'] is None,'benchmark provenance')
    got = recompute(scenario['inputs'],tables,rules,read('vedic/signs/catalog.yaml')['signs'])
    components = set(tables['totals']['terms'])
    tolerance = scenario['absolute_tolerance_virupas']
    require(set(scenario['expected'])==set(GRAHAS) and set(tolerance)==components
            and all(0 < t <= 1e-6 for t in tolerance.values()),'benchmark shape')
    for g,row in scenario['expected'].items():
        require(set(row)==components,g+' six components')
        for component,expected in row.items():
            require(isclose(got[g][component],expected,rel_tol=0,abs_tol=tolerance[component]),
                    f'S1 {g} {component}: {got[g][component]} vs {expected}')
    print('S1 independent worksheet passed: 42 component values; published Raman comparison pending.')
    count = 0
    for name,f in cases['fixtures'].items():
        result = recompute(f['inputs'],tables,rules,read('vedic/signs/catalog.yaml')['signs'])
        require(set(f['expected'])==must|{'rupas','meets_minimum','ishta','kashta'},name+' reference coverage')
        for k,row in f['expected'].items():
            require(len(row)==len(GRAHAS),name+' '+k)
            for g,expected in zip(GRAHAS,row):
                actual = result[g][k]
                ok = actual is expected if expected is None or isinstance(expected,bool) else actual is not None and isclose(actual,expected,rel_tol=0,abs_tol=0.000001)
                require(ok,f'{name} {g} {k}: got {actual}, expected {expected}')
                count += 1
    # The KB-05 cutoff is exclusive. A latitude tie propagates only to dependent totals.
    inputs = cases['fixtures']['Scenario 2']['inputs']
    signs = read('vedic/signs/catalog.yaml')['signs']
    tie = dict(inputs,latitude={**inputs['latitude'],'mercury':inputs['latitude']['mars']})
    boundary = dict(inputs,longitude={**inputs['longitude'],'mercury':inputs['longitude']['mars']+1})
    tied = recompute(tie,tables,rules,signs)
    outside = recompute(boundary,tables,rules,signs)
    for g in ('mars','mercury'):
        require(tied[g]['kala'] is None and tied[g]['totals'] is None and tied[g]['ishta'] is not None,
                g+' unresolved planetary war')
        require(outside[g]['yuddha']==0,g+' exclusive war threshold')
    # Hold the D1 and divisional longitudes fixed. Altering only the MT endpoint
    # isolates the Virgo/Libra-style 45 versus 30 D1 award from other varga awards.
    from copy import deepcopy
    former = deepcopy(rules)
    former['vedic.planets.venus']['graha']['dignity']['moolatrikona_degree_limits']['libra']=[0,5]
    for deg,expected in [(4.99,0),(5,15),(14.99,15),(15,0)]:
        probe=dict(inputs,longitude=dict(inputs['longitude'],venus=180+deg))
        now=recompute(probe,tables,rules,signs)['venus']['saptavargaja']
        prior=recompute(probe,tables,former,signs)['venus']['saptavargaja']
        require(now-prior==expected,'Venus D1 award boundary')
    for g,start,bonus in [('mars',90,15),('jupiter',120,30),('saturn',60,45)]:
        table=tables['drik']
        for deg,extra in [(start-.01,0),(start,bonus),(start+15,bonus),(start+30,0)]:
            base=aspect(table,'sun',deg)
            require(isclose(aspect(table,g,deg,'fixed-segment'),base+extra),'BPHS aspect segment')
    for diameters,known in [({},False),({'mars':1,'mercury':1},False),({'mars':1,'mercury':3},True)]:
        res=recompute(dict(inputs,disc_arcminutes=diameters),tables,rules,signs,'classical-disc-difference')
        require((res['mars']['yuddha'] is not None)==known,'war diameter availability')
        if known:
            a,b=(res[g] for g in ('mars','mercury'))
            pre=lambda r:r['sthana']+r['dig']+r['kala']-r['yuddha']
            require(isclose(abs(a['yuddha']),abs(pre(a)-pre(b))/2) and a['yuddha']==-b['yuddha'],'war transfer')
    print(f'{count} synthetic Shadbala reference values passed across both fixtures.')
