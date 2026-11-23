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


def validate_western(rules,read,evaluate,require):
    profile = read('western/profile.yaml')
    fixture = read('examples/western-reference.yaml')
    require(fixture['synthetic'] and profile['zodiac']=='tropical' and profile['houses']['default']=='placidus'
            and profile['houses']['option']=='whole-sign','Western frame')
    bodies = 'sun moon mercury venus mars jupiter saturn uranus neptune pluto'.split()
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
    orbs = read('western/aspects/orbs.yaml')['draft_natal_orbs']
    for name,(angle,orb) in zip(('conjunction','sextile','square','trine','opposition','quincunx'),
                               [(0,8),(60,4),(90,6),(120,6),(180,8),(150,2)]):
        require(name in profile['natal_aspects'] and orbs[name]==dict(angle=angle,orb=orb),name+' orb')
        for delta,expected in [(0,True),(orb,True),(orb+0.001,False)]:
            longitude = angle-delta if angle==180 else angle+delta
            hit = abs(separation(0,longitude)-angle)<=orb
            require(fires('aspects.'+name,{'western.natal.aspect':name if hit else None})==expected,name+' boundary')
    for chart in fixture['charts'].values():
        p = chart['positions']
        delta = separation(p['sun'],p['saturn'])
        square = abs(delta-orbs['square']['angle'])<=orbs['square']['orb']
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
