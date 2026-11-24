"""Dated, synthetic gochara reference cases. Sign indices start at Aries = 0."""
from datetime import datetime, timedelta
from ashtakavarga import PLANETS, prastara_for, transit_at

PREFIX = 'vedic.transits.'
NODES = ['rahu', 'ketu']
# Independent transcription of Rao 26.3 Table 63; order is Sun through Saturn.
TABLE_63 = (
    {3:9, 6:12, 10:4, 11:5},
    {1:5, 3:9, 6:12, 7:2, 10:4, 11:8},
    {3:12, 6:9, 11:5},
    {2:5, 4:3, 6:9, 8:1, 10:8, 11:12},
    {2:12, 5:4, 7:3, 9:10, 11:8},
    {1:8, 2:7, 3:1, 4:10, 5:9, 8:5, 9:11, 11:3, 12:6},
    {3:12, 6:9, 11:5},
)


def instant(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def house(sign, origin):
    return (sign-origin) % 12 + 1


def blocked(profile, graha, positions):
    """Return eligible blockers, [] for clear, or None for insufficient positions."""
    paired = profile['support_to_obstruction'].get(graha, {}).get(positions.get(graha))
    if paired is None:
        return None
    eligible = set(profile['eligible_blockers']) - {graha}
    for pair in profile['mutual_exemptions']:
        if graha in pair:
            eligible.difference_update(pair)
    hits = sorted(p for p in eligible if positions.get(p) == paired)
    if hits or all(positions.get(p) is not None for p in eligible):
        return hits
    return None


def bound_qualifiers(area, graha, reference, inputs, config, aspects, vedha, limits, evaluate):
    """Resolve the two predicates for one testimony, reference and dated area target."""
    from synthesis import double, transit_pace
    origin=inputs.get(reference)
    if (origin is None or graha not in config['grahas'] or
        (reference=='lagna' and inputs.get('tier')=='C')):
        return dict(challenge=None,support=None)
    moving=inputs['signs'].get(graha)
    if moving is None:
        return dict(challenge=None,support=None)
    targets=[(origin+h-1)%12 for h in config['areas'][area]['houses']]
    lords=[inputs.get('lord_signs',{}).get(t) for t in targets]
    known_targets=targets+[s for s in lords if s is not None]
    contact=any(house(t,moving) in (1,*aspects[graha]) for t in known_targets)
    values={'transit.contact.area_target':contact if contact or None not in lords else None}
    if reference=='moon':
        positions={g:house(sign,origin) for g,sign in inputs['signs'].items() if sign is not None}
        h=positions[graha]
        support=h in vedha['support_to_obstruction'].get(graha,{3,6,11})
        blockers=blocked(vedha,graha,positions) if support and graha not in NODES else []
        values.update({'transit.moon.house_stance':'support' if support else 'caution',
                       'transit.vedha.blocked':bool(blockers) if blockers is not None else None,
                       'transit.saturn.phase_challenge':graha=='saturn' and h in (12,1,2,4,8)})
    if inputs.get('av_available') and inputs.get('tier')!='C' and graha not in NODES:
        band=inputs.get('bav_band')
        values.update({'transit.bav.band':band,'transit.bav.supportive':band=='Supportive' if band else None})
        if graha in ('jupiter','saturn'):
            qualified=double(inputs['signs'],known_targets,aspects)
            if not qualified and None in lords: qualified=None
            pace=transit_pace(inputs.get('av',[]),limits)
            values['transit.double.'+('common_target' if reference=='lagna' else 'moon_target')]=qualified
            values['transit.double.pace_supported']=None if pace=='unknown' else pace=='supported'
    return {kind:evaluate(node,values) for kind,node in config['predicates'].items()}


def validate_gochara(rules, read, evaluate, require):
    fixture = read('examples/gochara-reference.yaml')
    require(fixture['synthetic'] is True, 'synthetic transit fixtures')
    vedha = read('vedic/transits/vedha.yaml')
    require(vedha['support_to_obstruction'] == dict(zip(PLANETS, TABLE_63)), 'Table 63')
    require(vedha['eligible_blockers'] == PLANETS and vedha['mutual_exemptions'] ==
            [['sun','saturn'],['moon','mercury']], 'vedha exemptions')

    for origin, obstruction in [(11,3),(12,6)]:
        positions = dict.fromkeys(PLANETS,origin)
        positions['mars'] = obstruction
        require(blocked(vedha,'venus',positions)==['mars'],'Venus vedha pair')
        positions['mars'] = 6 if obstruction==3 else 3
        require(blocked(vedha,'venus',positions)==[],'Venus swapped blocker')

    def fires(slug, values):
        return evaluate(rules[PREFIX + slug]['conditions'], values)

    s = fixture['sweep']
    start = instant(s['start_utc'])
    step = timedelta(days=s['window_days'])
    require(step.days > 0 and s['expected_moon_houses'] == list(range(1,13)), 'dated house sweep')
    phase = {12:'sade-sati-rising', 1:'sade-sati-middle', 2:'sade-sati-closing',
             4:'ardhashtama-shani', 8:'ashtama-shani'}
    for g in PLANETS + NODES:
        slugs = ['saturn-moon' if (g,h)==('saturn',1) else f'{g}-moon-house-{h}' for h in range(1,13)]
        key = f'transit.{g}.distance_from_natal_moon'
        windows = [(start+i*step, start+(i+1)*step, sign) for i,sign in enumerate(s['transit_signs'])]
        require(len(windows)==12, g+' window coverage')
        for i, (begin, end, sign) in enumerate(windows):
            for at in (begin, end-timedelta(seconds=1)):
                active, = [slot for slot in windows if slot[0]<=at<slot[1]]
                value = house(active[2], s['natal_moon_sign'])
                require(value == s['expected_moon_houses'][i] and value != house(sign,s['natal_lagna_sign']), g)
                values = {key:value, 'transit.saturn.over_moon_sign':value==1}
                require([slug for slug in slugs if fires(slug,values)] == [slugs[i]], (g,at))
                require(rules[PREFIX+slugs[i]]['life_areas']==rules[f'vedic.houses.house-{value}']['life_areas'],slugs[i])
                if g=='saturn':
                    for h, slug in phase.items():
                        require(fires(slug,values) == (value==h), (slug,at))
        require(all(fires(slug,{}) is None for slug in slugs), g+' no active window')

    snap = fixture['snapshot']
    at = instant(snap['instant'])
    require(instant(snap['start']) <= at < instant(snap['antar_end']) < instant(snap['end']), 'dated contact')
    natal, longitudes = snap['natal_signs'], snap['longitude']
    signs = {g:deg//30 for g,deg in longitudes.items()}
    positions = {g:house(sign,natal['moon']) for g,sign in signs.items()}
    require(positions['saturn']==snap['expected_saturn_house'], 'fixture reference')
    require(blocked(vedha,'saturn',positions)==snap['expected_vedha_blockers'], 'two occupants, one exempt')
    for g, pairs in zip(PLANETS,TABLE_63):
        for origin, target in pairs.items():
            for occupant in PLANETS + NODES:
                if g==occupant:
                    continue
                test_positions = dict.fromkeys(PLANETS,origin)
                test_positions.update({g:origin,occupant:target})
                actual = blocked(vedha,g,test_positions)
                exempt = {g,occupant} in ({'sun','saturn'},{'moon','mercury'})
                expected = [] if exempt or occupant in NODES else [occupant]
                require(actual==expected and fires('vedha-obstruction',{'transit.vedha.blocked':bool(actual)})
                        == bool(expected), (g,origin,occupant))
    require(blocked(vedha,'saturn',{'saturn':3,'sun':12}) is None,'unknown possible blocker')

    def check(slug, key, value, expected):
        require(fires(slug,{'transit.'+key:value}) is expected, slug)

    aspects = read('vedic/aspects/full-graha.yaml')['inclusive_distances']
    for target in range(12):
        hit = all(house(target,signs[g]) in [1,*aspects[g]] for g in ('jupiter','saturn'))
        # Capricorn Jupiter reaches Capricorn, Taurus, Cancer, Virgo.
        # Taurus Saturn reaches Taurus, Cancer, Scorpio, Aquarius.
        require(fires('double-transit',{'transit.double.common_target':hit,'transit.double.moon_target':False}) == (target in (1,3)), 'Lagna double transit')
    for ketu,expected in [(longitudes['ketu'],True),(longitudes['ketu']+1,False)]:
        check('nodal-axis','nodes.opposed',(ketu-longitudes['rahu'])%360==180,expected)
    contact = snap['contact']
    for target in [contact['natal'],'venus']:
        hit = signs[contact['moving']]==natal[target]
        check('over-natal-graha','contact.natal',hit,target=='mercury')
        for time in (at,instant(snap['antar_end'])):
            antar = snap['active_antar'] if time<instant(snap['antar_end']) else snap['next_antar']
            check('over-dasha-lord','contact.active_lord',hit and target in (antar,snap['active_maha']),
                  target=='mercury' and time==at)

    raw = read('vedic/strength/ashtakavarga/bindu.yaml')
    kak = rules['vedic.strength-ashtakavarga.kakshya']['calculation']
    marks = prastara_for(raw['offsets']['saturn'],natal)
    lord,bit,band = transit_at(longitudes['saturn']*3600,marks,kak,raw['transit_bands'])
    require((lord,bit,band)==(snap['expected_kakshya'],snap['expected_kakshya_bit'],snap['expected_bav_band']),
            'dated KB-13 cross-check')
    check('raw-bav-kakshya','av.contributor_mark',bool(bit),True)
    for i,(date,speed,expected) in enumerate(fixture['station']['samples']):
        samples = fixture['station']['samples']
        if i:
            require(instant(samples[i-1][0]) < instant(date),'motion chronology')
        turn = speed==0 and 0<i<len(samples)-1 and samples[i-1][1]*samples[i+1][1]<0
        check('station','motion.station',turn,expected=='station')
        check('retrograde','motion.retrograde',speed<0,expected=='retrograde')

    # G1: Cancer Saturn viewed from Capricorn rising and Libra Moon.
    for graha in PLANETS + NODES:
        key=f'transit.{graha}.distance_from_lagna'
        for sign in range(12):
            h=house(sign,9)
            slug=f'{graha}-lagna-house-{h}'
            require(fires(slug,{key:h}) and fires(slug,{}) is None and
                    rules[PREFIX+slug]['evidence']['reference']=='lagna',slug)
    require((house(3,9),house(3,6))==(7,10),'G1 independent reference chips')
    require([house(i,9) for i in [3,4,3]]==[7,8,7],'retrograde exit and re-entry')
    require(len({house(3,int(deg//30)) for deg in [29.8,30.2]})==2,'withhold ambiguous Moon phase')
    qualifiers=read('vedic/transits/qualifiers.yaml')['areas']
    require(len(qualifiers)==11,'area coverage')
    for area,row in qualifiers.items():
        for kind,node in read('vedic/transits/qualifiers.yaml')['predicates'].items():
            require(evaluate(node,{}) is None and evaluate(node,{'transit.contact.area_target':False}) is False,area)
            trigger='transit.vedha.blocked' if kind=='challenge' else 'transit.bav.supportive'
            require(evaluate(node,{'transit.contact.area_target':True,trigger:True}),area)

    config=read('vedic/transits/qualifiers.yaml')
    limits=read('life-areas/pipeline.yaml')['transit']['pace']
    inputs=dict(lagna=9,moon=6,signs={'saturn':3,'jupiter':3},tier='C',
                av_available=True,bav_band='Supportive',av=[(40,6),(40,6)])
    require(bound_qualifiers('love-marriage','saturn','lagna',inputs,config,aspects,vedha,limits,evaluate)
            ==dict(challenge=None,support=None),'Tier C withholds Lagna reference')
    moon=bound_qualifiers('career','saturn','moon',inputs,config,aspects,vedha,limits,evaluate)
    require(moon['challenge'] is True and moon['support'] is not True,'Tier C Moon without AV inheritance')
