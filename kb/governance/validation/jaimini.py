"""Synthetic Jaimini reference charts and independent boundary checks."""
from other_dashas import SignChart
from collections import Counter
from fractions import Fraction
import re

PREFIX = 'jaimini/'
CLASSICAL = 'sun moon mars mercury jupiter venus saturn'.split()
RULERS = 'mars venus mercury moon sun mercury venus mars jupiter saturn saturn jupiter'.split()


def ranked(positions, method, scheme=None):
    scheme = method['default_scheme'] if scheme is None else scheme
    roles = method['schemes'][scheme]
    bodies = list(method['classical_candidates'])
    if scheme == 'eight':
        bodies.append(method['eight_addition'])
    scores = {}
    for body in bodies:
        if body not in positions:
            return dict.fromkeys(roles)
        progress = positions[body][1]
        scores[body] = method['sign_width_arcsec']-progress if body=='rahu' else progress
    ordered = sorted(bodies, key=scores.get, reverse=True)
    counts = Counter(scores.values())
    return {role:body if counts[scores[body]]==1 else None for role,body in zip(roles,ordered,strict=True)}


def arudha(source, lord_sign, profile):
    distance = (lord_sign-source)%12 + 1
    raw = (lord_sign+distance-1)%12
    if (raw-source)%12+1 in profile['exception_when_raw_distance']:
        return (raw+profile['advance_from_raw'])%12
    return raw


def aspects(source,target):
    if source%3==2:
        return target%3==2 and target!=source
    return {source%3,target%3}=={0,1} and (target-source)%12 not in (1,11)


def d9(position):
    # Nine harmonics of absolute longitude, independent of sign-modality lookup.
    sign, progress = position
    return ((sign*108000 + progress)//12000)%12


def validate_jaimini(rules,read,evaluate,require):
    fixture = read('examples/jaimini-reference.yaml')
    require(fixture['synthetic'] and set(fixture['cases'])=={'Asha','Ravi'},'Jaimini fixtures')
    method = read(PREFIX+'chara-karakas/methods.yaml')
    period = read('jaimini/chara-dasha/periods.yaml')
    require(method['default_scheme']=='seven' and method['optional_scheme']=='eight'
            and period['modifier_grade_bounds']==[-1,1] and period['default_variant']==
            read('vedic/dashas/chara/periods.yaml')['profile'],'Jaimini owner defaults')
    require(method['classical_candidates']==CLASSICAL and method['eight_addition']=='rahu'
            and method['sign_width_arcsec']==108000, 'karaka inputs')
    require(method['schemes']=={'seven':'AK AmK BK MK PK GK DK'.split(),
                                'eight':'AK AmK BK MK PiK PK GK DK'.split()},'karaka roles')
    policy = read(PREFIX+'arudha-padas/methods.yaml')
    config = policy['calculation']
    labels = {f'A{n}':n for n in range(1,13)}
    require(policy['labels']==dict(labels,AL=1,UL=12) and policy['rulers']==RULERS,'pada inputs')
    require(config['exception_when_raw_distance']==[1,7] and config['advance_from_raw']==9,'exception pair')
    # Expected offsets by relative sign of lord, obtained by inclusive sign counting.
    offsets = [9,2,4,3,8,10,9,2,4,3,8,10]
    for source in range(12):
        for i,want in enumerate(offsets):
            require(arudha(source,(source+i)%12,config)==(source+want)%12,'pada lord sweep')
    matrix = read(PREFIX+'rashi-drishti/signs.yaml')['targets']
    require(len(matrix)==12, 'aspect rows')
    for s in range(12):
        require(matrix[s]==[t for t in range(12) if aspects(s,t)], f'sign aspect row {s}')

    def fire(slug,key,value):
        cond = rules['jaimini.'+slug]['conditions']
        require(evaluate(cond,{key:value}) is value and evaluate(cond,{}) is None,slug)

    role_names = 'atmakaraka amatyakaraka bhratrikaraka matrikaraka pitrikaraka putrakaraka gnatikaraka darakaraka'.split()
    entries = dict(zip(method['schemes']['eight'],role_names,strict=True))
    for name,case in fixture['cases'].items():
        positions = case['positions']
        lagna = case['lagna'][0]
        require(d9(case['lagna'])==case['lagna_d9'],name+' lagnamsa')
        for scheme in method['schemes']:
            roles = ranked(positions,method,scheme)
            require(list(roles.values())==case['ranked_'+scheme],name+' '+scheme)
            require(d9(positions[roles['AK']])==case['ak_d9'][scheme],name+' karakamsa')
            for role,g in roles.items():
                for selected in positions:
                    fire('chara-karakas.'+entries[role],'jaimini.'+role.lower()+'.confirmed',selected==g)
        chart = SignChart({'positions':{g:p[0] for g,p in positions.items()},
                           'degree_in_sign':{g:Fraction(p[1],3600) for g,p in positions.items()}},
                          read('vedic/dashas/chara/periods.yaml')['even_footed'])
        for sign,expected in zip((7,10),case['dual_lords'],strict=True):
            require(chart.owner(sign)==chart.owner(sign,for_period=False)==expected,(name,sign,'co-lord'))
            anchor = chart.pos[chart.owner(sign,for_period=False)]
            direction = -1 if anchor==chart.pos['ketu'] else 1
            pair = [(anchor+direction*(h-1))%12 for h in (2,12)]
            require(pair==case['lord_argala'][sign],(name,sign,'lord-based argala'))
        for n,want in enumerate(case['padas'],1):
            source = (lagna+n-1)%12
            require(arudha(source,positions[chart.owner(source,for_period=False)][0],config)==want,(name,n))
            entry = {1:'arudha-lagna',12:'upapada'}.get(n,'a'+str(n))
            key = {1:'jaimini.al.stable',12:'jaimini.ul.stable'}.get(n,f'jaimini.a{n}.stable')
            fire('arudha-padas.'+entry,key,True)
        for src in positions.values():
            for dst in positions.values():
                hit = dst[0] in matrix[src[0]]
                require(hit==aspects(src[0],dst[0]),name+' graha sign contact')
                fire('rashi-drishti.sign-contact','jaimini.sign_aspect',hit)
    p = fixture['cases']['Asha']['positions'].copy()
    p['moon'] = [3,p['sun'][1]]
    require(ranked(p,method)==ranked(p,method,'seven'),'seven default roles')
    ties = ranked(p,method,'seven')
    require(ties['AK'] is ties['AmK'] is None and ties['BK']=='mars','exact tie affects only tied slots')
    p['moon'] = [3,p['sun'][1]+Fraction(1,100)]
    require(ranked(p,method,'seven')['AK']=='moon','unrounded progress')
    del p['rahu']
    require(not any(ranked(p,method,'eight').values()) and ranked(p,method,'seven')['AK']=='moon','missing candidate')
    argala = read(PREFIX+'argala/pairs.yaml')
    require(argala['primary']=={2:12,4:10,11:3} and argala['secondary']=={5:9},'paired obstructions')
    visibility = read('SCHEMA.yaml')['jaimini_entries']
    require(visibility['public_fields']==['user_text','remedy.user_text'] and
            visibility['technical_fields_access']==['admin'], 'Jaimini field access')
    technical = re.compile(r'\b(?:AK|AmK|BK|MK|PiK|PK|GK|DK|AL|UL|A(?:[1-9]|1[0-2])|argala|arudha|atmakaraka|karakamsa|swamsa)\b|ಕಾರಕಾಂಶ|ಆತ್ಮಕಾರಕ|आत्मकारक|कारकांश|→|->')
    for rid,r in rules.items():
        if r['system']=='jaimini':
            copies=[r['user_text']]
            if r['remedy']:
                copies.append(r['remedy']['user_text'])
            require(all(not technical.search(t) for c in copies for t in c.values()),rid+' technical public text')
    print('Jaimini passed: both karaka schemes on two charts, exact-tie and fractional probes, 24 chart padas, 144 lord placements and all 144 ordered sign pairs.')
