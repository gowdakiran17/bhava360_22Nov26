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
    {1:8, 2:7, 3:1, 4:10, 5:9, 8:5, 9:11, 11:6, 12:3},
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


def validate_gochara(rules, read, evaluate, require):
    fixture = read('examples/gochara-reference.yaml')
    require(fixture['synthetic'] is True, 'synthetic transit fixtures')
    vedha = read('vedic/transits/vedha.yaml')
    require(vedha['support_to_obstruction'] == dict(zip(PLANETS, TABLE_63)), 'Table 63')
    require(vedha['eligible_blockers'] == PLANETS and vedha['mutual_exemptions'] ==
            [['sun','saturn'],['moon','mercury']], 'vedha exemptions')

    def fires(slug, values):
        return evaluate(rules[PREFIX + slug]['conditions'], values)

    s = fixture['sweep']
    start = instant(s['start_utc'])
    step = timedelta(days=s['window_days'])
    require(step.days > 0 and s['expected_moon_houses'] == list(range(1,13)), 'dated house sweep')
    phase = {12:'sade-sati-rising', 1:'sade-sati-middle', 2:'sade-sati-closing',
             4:'kantaka-shani', 8:'ashtama-shani'}
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
        check('double-transit','double.common_target',hit,target in (1,3))
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
