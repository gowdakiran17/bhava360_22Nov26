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


def aspect(table, planet, angle):
    knots = table['knots_degrees']
    weights = [60 if k in table['special'].get(planet, []) else v for k,v in zip(knots,table['common'])]
    i = bisect_right(knots,angle)-1
    return weights[i] + (weights[i+1]-weights[i])*(angle-knots[i])/(knots[i+1]-knots[i])


def recompute(chart, tables, rules, signs):
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
    elongation = (lon['moon']-lon['sun'])%360
    malefics = {'sun','mars','saturn'}
    if not 0 < elongation <= 180:
        malefics.add('moon')
    if any(sign['mercury']==sign[g] for g in malefics):
        malefics.add('mercury')
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
                nat = int(owner in relations['friends'])-int(owner in relations['enemies'])
                distance = (sign[owner]-sign[g])%12+1
                temp = 1 if distance in sap['temporary_friends'] else -1
                award = sap['relationship_awards'][2+nat+temp]
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
        r['drik'] = sum(aspect(tables['drik'],p,(lon[g]-lon[p])%360)*(-1 if p in malefics else 1)
                        for p in GRAHAS if p!=g)/4
    war = rules[tables['yuddha']['winner_rule']]['state']
    pairs = [(a,b) for a,b in combinations(war['eligible'],2) if arc(lon[a],lon[b])<war['maximum_exclusive_degrees']]
    for a,b in pairs:
        lat_a, lat_b = (chart['latitude'].get(g) for g in (a,b))
        overlapping = any(sum(g in pair for pair in pairs)>1 for g in (a,b))
        if overlapping or lat_a is None or lat_b is None or lat_a==lat_b:
            out[a]['yuddha']=out[b]['yuddha']=None
            continue
        pre = [sum(out[g][k] for k in tables['kala']['terms'] if k!='yuddha') for g in (a,b)]
        transfer = abs(pre[0]-pre[1])*(1 if chart['latitude'][a]>chart['latitude'][b] else -1)
        out[a]['yuddha'],out[b]['yuddha'] = transfer,-transfer
    for g,r in out.items():
        r['kala'] = None if r['yuddha'] is None else sum(r[k] for k in tables['kala']['terms'])
        total = tables['totals']
        r['totals'] = None if r['kala'] is None else sum(r[k] for k in total['terms'])
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
    require(set(cases['fixtures'])=={'Asha','Ravi'},'strength fixture identities')
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
    inputs = cases['fixtures']['Ravi']['inputs']
    signs = read('vedic/signs/catalog.yaml')['signs']
    tie = dict(inputs,latitude={**inputs['latitude'],'mercury':inputs['latitude']['mars']})
    boundary = dict(inputs,longitude={**inputs['longitude'],'mercury':inputs['longitude']['mars']+1})
    tied = recompute(tie,tables,rules,signs)
    outside = recompute(boundary,tables,rules,signs)
    for g in ('mars','mercury'):
        require(tied[g]['kala'] is None and tied[g]['totals'] is None and tied[g]['ishta'] is not None,
                g+' unresolved planetary war')
        require(outside[g]['yuddha']==0,g+' exclusive war threshold')
    print(f'{count} synthetic Shadbala reference values passed across both fixtures.')
