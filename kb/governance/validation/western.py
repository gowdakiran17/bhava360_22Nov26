"""Exercise Western KB predicates with independent synthetic tropical positions."""
from collections import Counter
from itertools import permutations


def separation(a, b):
    return abs((a-b+180) % 360-180)


def pattern(positions, geometry, aspects):
    if 'minimum_bodies' in geometry:
        counts = Counter(int(p%360//30) for p in positions)
        return max(counts.values(), default=0) >= geometry['minimum_bodies']
    for a,b,c in permutations(positions,3):
        distances = [separation(a,b),separation(a,c),separation(b,c)]
        if all(abs(d-aspects[k]['angle']) <= aspects[k]['orb'] for d,k in zip(distances,geometry['edges'])):
            return True
    return False


def fortune(asc, sun, moon, altitude):
    if None in (asc,sun,moon,altitude):
        return None
    return (asc+(moon-sun if altitude>=0 else sun-moon))%360


def western_houses(method, asc, calculate, policy):
    """calculate returns twelve cusps or raises on Swiss failure (including substituted systems)."""
    if method not in policy['systems'] or asc is None:
        return None
    effective = method
    if method in ('placidus','koch'):
        try:
            cusps = calculate(policy['systems'][method]['code'])
            widths = [(cusps[(i+1)%12]-c)%360 for i,c in enumerate(cusps)] if len(cusps)==12 else []
            if not widths or min(widths)<=0 or abs(sum(widths)-360)>1e-7:
                raise ValueError('Invalid quadrant cusps')
        except ValueError:
            effective = 'whole-sign'
    if effective in ('whole-sign','equal'):
        start = int(asc%360//30)*30 if effective=='whole-sign' else asc
        cusps = [(start+30*i)%360 for i in range(12)]
    label = policy['systems'][method]['admin_label'] if method==effective else policy['fallback_labels'][method]
    return dict(requested=method,effective=effective,label=label,code=policy['systems'][effective]['code'],cusps=cusps)


def validate_western(rules,read,evaluate,require):
    profile = read('western/profile.yaml')
    fixture = read('examples/western-reference.yaml')
    require(fixture['synthetic'] and profile['zodiac']=='tropical' and profile['houses']['default']=='placidus'
            and set(profile['houses']['systems'])=={'placidus','whole-sign','koch','equal'},'Western frame')
    hp = profile['houses']
    require([s['code'] for s in hp['systems'].values()]==list('PWKE'),'Swiss house codes')
    for name in hp['systems']:
        normal = western_houses(name,359,lambda code:[(359+30*i)%360 for i in range(12)],hp)
        require(normal['effective']==name and normal['cusps'][0]==(330 if name=='whole-sign' else 359),'house origin')
        failed = western_houses(name,359,lambda code:[0]*12,hp)
        require(failed['effective']==('whole-sign' if name in ('koch','placidus') else name)
                and western_houses(name,None,None,hp) is None,'Western labelled fallback')
    require(read('shared/conventions/profiles.yaml')['calculation_profiles']['kp-placidus-v1']['polar_fallback']=='unknown','KP keeps separate policy')
    require(fortune(350,10,30,0)==10 and fortune(350,10,30,-.01)==330
            and fortune(None,10,30,20) is None,'Fortune sect and wrap')
    # A quadrant adapter may signal a polar substitution as an error.
    def failed_call(code):
        raise ValueError('Polar cusp failure')
    require(all(western_houses(m,351,failed_call,hp)['code']=='W' for m in ('koch','placidus')),
            'explicit Western recomputation')
    orb_tables = read('western/aspects/orbs.yaml')
    for technique in ('natal','transit','progression','solar-arc','synastry','composite'):
        table = orb_tables[technique]
        for i,name in enumerate(profile['natal_aspects']):
            width = table[name]['orb']
            expected = [8,4,6,6,8,2][i] if technique=='natal' else [6,3,5,5,6,2][i] if technique in ('synastry','composite') else 1
            require(width==expected and table[name]['angle']==orb_tables['natal'][name]['angle'],technique+' width')
            for delta,want in [(width-.001,True),(width,True),(width+.001,False)]:
                exact = table[name]['angle']
                require((abs(separation(exact-delta if exact==180 else exact+delta,0)-exact)<=width)==want,'orb boundary')
    bodies = 'sun moon mercury venus mars jupiter saturn uranus neptune pluto'.split()
    validate_depth(rules,read,evaluate,require)
    signs = 'aries taurus gemini cancer leo virgo libra scorpio sagittarius capricorn aquarius pisces'.split()
    require(set(profile['planets'])=={'western.planets.'+b for b in bodies},'ten Western planet anchors')
    def fires(rid,facts):
        return evaluate(rules['western.'+rid]['conditions'],facts) is True
    for b in bodies:
        outer = b in ('uranus','neptune','pluto')
        require(fires('planets.'+b,{'western.natal.selected_outer' if outer else 'western.natal.body':b}),b)
        for i,s in enumerate(signs):
            facts = {'western.natal.body':b,'western.natal.bound-sign':s,'western.natal.'+b+'.sign':s}
            require(fires('signs.'+s,facts) and fires('natal.'+b+'-'+s,facts),b+'/'+s)
            require(fires(f'natal.{b}-house-{i+1}',{'western.natal.body':b,'western.natal.bound-house':i+1}),
                    b+' house inventory')
    orbs = read('western/aspects/orbs.yaml')['natal']
    for name,(angle,orb) in zip(('conjunction','sextile','square','trine','opposition','quincunx'),
                               [(0,8),(60,4),(90,6),(120,6),(180,8),(150,2)]):
        require((name in profile['natal_aspects'])==(name!='quincunx') and orbs[name]==dict(angle=angle,orb=orb),name+' orb')
        for delta,expected in [(0,True),(orb,True),(orb+0.001,False)]:
            longitude = angle-delta if angle==180 else angle+delta
            hit = abs(separation(0,longitude)-angle)<=orb
            require(fires('aspects.'+name,{'western.natal.aspect':name if hit else None})==expected,name+' boundary')
    for chart in fixture['charts'].values():
        p = chart['positions']
        delta = separation(p['sun'],p['saturn'])
        square = inside_orb(orb_tables,'natal','square','sun','saturn',delta)
        facts = {'western.natal.sun-saturn-pair':True,'western.natal.aspect':'square' if square else None}
        require(fires('aspects.saturn-square-sun',facts)==chart['sun_saturn_square'],'natal square')
        cusps = chart['placidus']
        h, = [i+1 for i,c in enumerate(cusps) if (p['venus']-c)%360 < (cusps[(i+1)%12]-c)%360]
        whole = 1+(int(p['venus']//30)-int(chart['ascendant']//30))%12
        require(dict(placidus=h,**{'whole-sign':whole})==chart['venus_house'],'Venus house frames')
        for house in (h,whole):
            require(fires('natal.venus-house-7',{'western.natal.body':'venus','western.natal.bound-house':house})
                    == (house==7),'Venus house selection')
    for case in fixture['patterns']:
        kind = case['kind']
        found = pattern(case['points'],profile['pattern_geometry'][kind],orbs)
        require(fires('patterns.'+kind,{'western.patterns.'+kind:found})==case['found'],kind+' geometry')
    timing = fixture['timing']
    jd = timing['birth_jd']+timing['elapsed_days']/profile['secondary_days_per_year']
    require(jd==timing['progressed_jd'],'day per year')
    for topic,slug,orb in [('transits','natal-contact','transit_orb_degrees'),
                           ('progressions','secondary-contact','secondary_orb_degrees')]:
        for kind in profile['natal_aspects']:
            for offset,expected in [(0.5,True),(1.1,False)]:
                angle = orbs[kind]['angle']
                moving = angle-offset if angle==180 else angle+offset
                hit = abs(separation(moving,0)-angle)<=profile[orb]
                facts = {'western.'+topic+'.'+slug:hit,'western.'+topic+'.bound-aspect':kind}
                require(fires(topic+'.'+slug+'-'+kind,facts)==expected,'timing contact orb')
    case = timing['solar_return']
    a,b = case['solar_longitudes']
    start,end = case['bracket_jd']
    root = start+(case['natal_sun']-a)%360/((b-a)%360)*(end-start)
    require(root==case['expected_jd'] and fires('returns.solar-return',{'western.returns.solar-return':True}),
            'annual solar crossing')
    require(profile['public']['tones']==['Supportive','Steady','Take care'] and
            profile['public']['fields']==['localized_tone','user_text'],'Western public projection')
    print('Western passed: 120 sign placements, 120 house placements, six aspect boundaries, four patterns and three timing methods.')


def inside_orb(tables, technique, aspect, first, second, distance, *, minors=False):
    if distance is None:
        return None
    row=tables[technique].get(aspect)
    major=aspect in ('conjunction','sextile','square','trine','opposition')
    if row is None or not major and not minors:
        return False
    extra=0
    if major and technique in ('natal','synastry','composite'):
        extra=max(tables['widening_degrees'][first],tables['widening_degrees'][second])
    return abs(distance-row['angle'])<=row['orb']+extra


def compose_calendar(events, scale, start, end, policy):
    """Query bounds and solved pass instants share the requested local zone."""
    calendar={}
    for e in events:
        if e['mover'] not in policy['periods'][scale] or not start<=e['at']<end or not e['stable']:
            continue
        key=e['mover'],e['target'],e['aspect']
        entry=calendar.setdefault(key,{'dates':set(),'direction':e['direction']})
        entry['dates'].add(e['at'])
    votes={x['direction'] for x in calendar.values()}-{'context','neutral'}
    tone='Supportive' if votes=={'support'} else 'Take care' if votes=={'caution'} else 'Steady'
    return (tone if calendar else None, sorted((at,key) for key,x in calendar.items() for at in x['dates']))


def validate_depth(rules,read,evaluate,require):
    from itertools import combinations
    policy=read('western/personal-horoscopes/compose.yaml')
    tables=read('western/aspects/orbs.yaml')
    bodies='sun moon mercury venus mars jupiter saturn uranus neptune pluto asc mc'.split()
    pairs={'natal':list(combinations(bodies,2)),
           'transit':[(a,b) for a in bodies[5:10] for b in bodies[:5]+bodies[-2:]],
           'synastry':[('sun','moon'),('moon','moon'),('venus','mars')]+[('saturn',b) for b in bodies[:5]]+[('asc',b) for b in bodies[:5]+['asc']]}
    for mode,items in pairs.items():
        for a,b in items:
            for kind,angles in policy['groups'].items():
                rid=f'western.{mode}-pairs.{a}-{b}-{kind}'
                row=rules[rid]
                facts={f'western.{mode}.reading_pair':a+'-'+b,f'western.{mode}.family':kind,
                       'western.angle.reliable':True,'western.transit.perfection_dated':True}
                require(evaluate(row['conditions'],facts) and evaluate(row['conditions'],{}) is None,rid)
                if {a,b}&{'asc','mc'}:
                    require(not evaluate(row['conditions'],dict(facts,**{'western.angle.reliable':False})),rid)
                if mode=='natal' and {a,b}<=set(bodies[7:10]):
                    require(row['evidence']['weight_class']=='context',rid)
                for angle in angles:
                    require(inside_orb(tables,mode,angle,a,b,tables[mode][angle]['angle']),rid)
    require(inside_orb(tables,'natal','square','sun','moon',98) and
            not inside_orb(tables,'natal','square','sun','moon',98.001) and
            not inside_orb(tables,'natal','quincunx','sun','moon',150) and
            inside_orb(tables,'natal','quincunx','sun','moon',152,minors=True),'orb caps and override')
    for sign in 'aries taurus gemini cancer leo virgo libra scorpio sagittarius capricorn aquarius pisces'.split():
        cond=rules['western.angles.mc-'+sign]['conditions']
        require(evaluate(cond,{'western.angle.mc_sign':sign,'western.angle.reliable':True}) and
                evaluate(cond,{'western.angle.mc_sign':sign}) is None,sign+' MC gate')
    for scale,mover in [('day','moon'),('week','mercury')]:
        event=dict(at=4,mover=mover,target='venus',aspect='sextile',stable=True,direction='support')
        require(compose_calendar([event,event,dict(event,at=6)],scale,4,6,policy)==
                ('Supportive',[(4,(mover,'venus','sextile'))]),scale+' local bounds and repeated contact')
    scenario=read('examples/western-calendar.yaml')
    events=scenario['passes']
    tone,dated=compose_calendar(events,'month',1,31,policy)
    require(tone==scenario['monthly_tone'] and len(dated)==2,'opposed monthly testimonies')
    require(compose_calendar(events,'week',1,31,policy)==(None,[]),'weekly mover filter')
    require(compose_calendar(events,'month',1,events[1]['at'],policy)[0]=='Take care','half-open time horizon')
    require(compose_calendar([dict(events[0],stable=False)],'month',1,31,policy)==(None,[]),'uncertain target')
