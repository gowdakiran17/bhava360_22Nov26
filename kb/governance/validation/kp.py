"""Independent KP table reconstruction and synthetic chart testimony checks."""
from bisect import bisect_right
from fractions import Fraction
from datetime import datetime, timedelta
import re

ORDER = 'ketu venus sun moon mars rahu jupiter saturn mercury'.split()
YEARS = (7, 20, 6, 10, 7, 18, 16, 19, 17)
RULERS = 'mars venus mercury moon sun mercury venus mars jupiter saturn saturn jupiter'.split()
STAR, SIGN, TURN = 48000, 108000, 1296000


def intervals():
    result = []
    for star in range(27):
        start = star * STAR
        for offset in range(9):
            i = (star + offset) % 9
            end = start + STAR * YEARS[i] // 120
            while start < end:
                sign = start // SIGN
                stop = min(end, (sign + 1) * SIGN)
                result.append(dict(number=len(result)+1, start_arcsec=start, end_arcsec=stop,
                                   sign=sign+1, nakshatra=star+1, star_lord=ORDER[star%9], sub_lord=ORDER[i]))
                start = stop
    return result


def numbered(rows, number):
    if type(number) is int and 1 <= number <= len(rows):
        return rows[number-1]


def occupied(cusps, point):
    house, = [i+1 for i, start in enumerate(cusps)
              if (point-start)%TURN < (cusps[(i+1)%12]-start)%TURN]
    return house


def validate_kp(rules, read, evaluate, require):
    judgement_checks(rules,read,evaluate,require)
    rows = read('kp/number-horary/249-divisions.yaml')['intervals']
    require(rows == intervals() and len(rows)==249, 'exact KP boundaries, signs, stars, subs and numbers')
    starts = [r['start_arcsec'] for r in rows]

    def lookup(position):
        return rows[bisect_right(starts, position%TURN)-1]

    require(lookup(TURN)==rows[0] and lookup(-1)==rows[-1], 'KP circular endpoints')
    for row in rows:
        require(numbered(rows,row['number'])==lookup(row['start_arcsec'])==row, row)
        require(lookup(row['end_arcsec']-Fraction(1,100))==row, row)
    require(all(numbered(rows,n) is None for n in (True,False,0,250,1.2,'1')), 'horary integer domain')
    policy = read('kp/significators/bhava360.yaml')
    require(policy['ranked_levels']==['star_occupied','planet_occupied','star_owned','planet_owned']
            and policy['four_step']['actors']==['planet','star_of_planet','sub_of_planet','star_of_sub'],
            'distinct KP significator profiles')
    groups = read('kp/cusps/event-groups.yaml')['events']
    require(set(groups)==set(range(1,13)) and groups[7]['houses']==[2,7,11]
            and groups[10]['houses']==groups[6]['houses']==[2,6,10,11], 'KP event groups')
    failure = read('shared/conventions/profiles.yaml')['calculation_profiles']['kp-placidus-v1']['on_cusp_failure']
    require('planet-sub-lords' in failure['retain'] and lookup(0)['sub_lord']=='ketu'
            and set(failure['withhold'])=={'cuspal-sub-lords','house-significators','kp-prashna'}
            and set(failure['note'])=={'en','kn','hi'},'polar failure preserves independent planetary rows')
    fixture = read('examples/kp-reference.yaml')
    require(fixture['synthetic'] and set(fixture['cases'])=={'Asha','Ravi'}, 'synthetic KP charts')
    division = read('kp/star-sub-lords/divisions.yaml')
    require(list(division['lord_years_in_order'].items())==list(zip(ORDER,YEARS)) and
            (division['star_width_arcseconds'],division['sign_width_arcseconds'],division['cycle_years'])==
            (STAR,SIGN,120), 'KP calculation parameters')
    split_points = [b['start_arcsec']//3600 for a,b in zip(rows,rows[1:])
                    if a['sign']!=b['sign'] and (a['nakshatra'],a['sub_lord'])==(b['nakshatra'],b['sub_lord'])]
    require(split_points==division['split_at_degrees'], 'six splits within stellar subs')
    require(read('SCHEMA.yaml')['kp_entries']['public_fields']==['user_text','remedy.user_text'], 'KP public projection')
    chain_terms = re.compile(r'sub[ -]?lord|star[ -]?lord|placidus|ayanam[śs]a|significator|ಉಪಾಧಿಪತಿ|ಉಪಸ್ವಾಮಿ|नक्षत्र स्वामी|उपस्वामी|कस्प|→|->',re.I)
    for rid,r in rules.items():
        if r['system']=='kp':
            for copy in [r['user_text'],*([r['remedy']['user_text']] if r['remedy'] else [])]:
                require(all(not chain_terms.search(t) for t in copy.values()),rid+' technical chain in public copy')
    judgment = fixture['judgment']
    moon = lookup(judgment['moon_deg']*3600)
    asc = lookup(judgment['actual_asc_deg']*3600)
    require(asc!=numbered(rows,judgment['horary_number']), 'separate actual and numbered rising signs')
    for probe in judgment['cases']:
        local = datetime.fromisoformat(probe['local'])
        sunrise = datetime.fromisoformat(judgment['local_sunrise'])
        day = local.date()-timedelta(days=int(local<sunrise))
        roles = [policy['weekday_lords'][(day.weekday()+1)%7],RULERS[moon['sign']-1],moon['star_lord'],
                 RULERS[asc['sign']-1],asc['star_lord']]
        repeated = len(set(roles))<len(roles)
        require(roles==probe['expected_roles'] and evaluate(rules['kp.ruling-planets.repeated-lord']['conditions'],
                {'kp.ruling.repeated_lord':repeated}) is probe['repeat'],'actual judgment role or sunrise')
    for name, case in fixture['cases'].items():
        def rotate(deg):
            return (deg+case['rotation_deg'])%360 * 3600
        cusps = [rotate(v) for v in fixture['cusps_deg']]
        pos = {g:rotate(v) for g,v in fixture['longitude_deg'].items()}
        owner = [RULERS[c//SIGN] for c in cusps]
        require(owner==case['expected_cusp_owners'], name+' cusp owners')
        residence = {g:occupied(cusps,p) for g,p in pos.items()}
        star = {g:lookup(p)['star_lord'] for g,p in pos.items()}
        sub = {g:lookup(p)['sub_lord'] for g,p in pos.items()}
        require((residence,star,sub)==tuple(fixture[k] for k in
                ('expected_residence','expected_star','expected_sub')), name+' planetary primitives')
        require(all(occupied(cusps,c)==i+1 and occupied(cusps,c-1)==(i-1)%12+1
                    for i,c in enumerate(cusps)), name+' cusp edges')
        owned = {g:[i+1 for i,r in enumerate(owner) if r==g] for g in pos}
        # Build the independent expected significators in the reverse (house-to-planets) direction.
        expected = {g:[[],[],[],[]] for g in pos}
        for h,ruler in enumerate(case['expected_cusp_owners'],1):
            occupants = {g for g,h0 in fixture['expected_residence'].items() if h0==h}
            for g,star_lord in fixture['expected_star'].items():
                for level,match in enumerate((star_lord in occupants,g in occupants,star_lord==ruler,g==ruler)):
                    if match:
                        expected[g][level].append(h)
        for g in pos:
            levels = [[residence[star[g]]],[residence[g]],owned[star[g]],owned[g]]
            require(levels==expected[g], (name,g,'ranked levels'))
            actors = [g,star[g],sub[g],star[sub[g]]]
            expected_actors = [g,fixture['expected_star'][g],fixture['expected_sub'][g],
                               fixture['expected_star'][fixture['expected_sub'][g]]]
            require(actors==expected_actors,(name,g,'four steps'))
            for step,actor in enumerate(actors):
                principal = step in (1,3) or star[actor]==actor or actor not in star.values()
                primary_expected = step in (1,3) or actor in fixture['expected_primary_direct_actors']
                primary_houses = {residence[actor],*(h for h in owned[actor] if h not in residence.values())} if principal else set()
                expected_primary = {fixture['expected_residence'][actor],*(h for h,o in enumerate(case['expected_cusp_owners'],1)
                                    if o==actor and h not in fixture['expected_residence'].values())} if primary_expected else set()
                require(primary_houses==expected_primary,(name,g,step,'primary house testimony'))
        for n,event in groups.items():
            actor = lookup(cusps[n-1])['sub_lord']
            require(actor==fixture['expected_cusp_sub'][n-1], (name,n,'cusp sub'))
            hit = any(set(level).intersection(event['houses']) for level in expected[actor])
            rule = rules[event['entry']]
            require(evaluate(rule['conditions'],{event['fact']:hit}) is hit and
                    evaluate(rule['conditions'],{}) is None,(name,n,'cusp predicate'))
            if n==7:
                require(hit is case['expected_marriage_link'], name+' partnership screen')
    print('KP passed: all 249 exact rows, 498 interval-edge probes, 18 planetary testimonies and 24 cusp readings.')


def event_outcome(group, houses, cusp_solved):
    if cusp_solved is not True or houses is None:
        return None
    support=bool(set(group['houses']).intersection(houses))
    denial=bool(set(group['negating_houses']).intersection(houses))
    return {(True,False):'promised',(False,True):'denied',(True,True):'mixed',(False,False):'unrelated'}[support,denial]


def event_windows(group, outcome, links, ruling, periods, passages, horizon):
    if outcome not in ('promised','mixed') or ruling is None or len(periods)!=3:
        return []
    candidates=set(ruling).intersection(g for g,houses in links.items() if houses is not None and set(houses).intersection(group['houses']))
    if any(lord not in candidates for lord,_,_ in periods):
        return []
    sensitive={'event-cusp',*(lord for lord,_,_ in periods)}
    hits=set()
    for body,target,entry,exit in passages:
        if body not in ('sun','moon','jupiter') or target not in sensitive:
            continue
        start=max(horizon[0],entry,*(a for _,a,_ in periods))
        end=min(horizon[1],exit,*(b for _,_,b in periods))
        if start<end:
            hits.add((start,end,body,target))
    return sorted(hits)


def judgement_checks(rules, read, evaluate, require):
    groups=read('kp/cusps/event-groups.yaml')['events']
    for row in groups.values():
        require(set(row['negating_houses'])=={(h-2)%12+1 for h in row['houses']},row['event'])
    for links,expected in [([2],'promised'),([6],'denied'),([7,10],'mixed'),([8],'unrelated'),(None,None)]:
        require(event_outcome(groups[7],links,True)==expected,'marriage group')
    k2=read('examples/kp-judgement.yaml')
    predicates=read('kp/judgement/chain.yaml')['predicates']
    for spec in predicates.values():
        node=spec['when']; key=node['fact']
        require(evaluate(node,{key:True}) and not evaluate(node,{key:False}) and evaluate(node,{}) is None,key)
    g=groups[k2['cusp']]
    outcome=event_outcome(g,k2['cusp_links'],True)
    require(outcome=='mixed' and event_outcome(g,k2['cusp_links'],False) is None,'actual Placidus failure')
    def windows(ruling):
        return event_windows(g,outcome,k2['significators'],ruling,k2['periods'],k2['passages'],k2['horizon'])
    require(windows(k2['ruling'])==[tuple(k2['expected_window'])] and not windows(['venus']), 'K2 intersection and ruling filter')
    require(evaluate(rules['kp.judgement.mixed']['conditions'],{'kp.judgement.outcome':outcome}) and
            evaluate(rules['kp.judgement.mixed-signals']['conditions'],{'kp.judgement.conflict':True}),'K2 explanations')
