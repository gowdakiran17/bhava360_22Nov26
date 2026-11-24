"""House strength, qualitative projection and dignity boundaries."""
from math import isclose
from shadbala import GRAHAS, aspect


def benefic(g, positions, table, variant=None, mercury_method="predominance"):
    if g in table['always_benefic']:
        return True
    if g in table['always_malefic']:
        return False
    if g == 'moon':
        if any(positions.get(p) is None for p in ('moon','sun')):
            return None
        bounds = table['moon']['variants'][variant or table['moon']['default']]
        angle = (positions['moon']-positions['sun'])%360
        lower = bounds['lower_deg']
        return (angle > lower or angle == lower and bounds['lower_inclusive']) and (angle < bounds['upper_deg'] or angle == bounds['upper_deg'] and bounds['upper_inclusive'])
    if g != 'mercury' or positions.get(g) is None:
        return None
    # Range of possible net votes (benefics minus malefics) for incomplete inputs.
    low = high = 0
    for body in table['mercury']['associates']:
        nature = benefic(body,positions,table,variant)
        pos = positions.get(body)
        if pos is not None and pos//30 != positions[g]//30:
            continue
        votes = [1] if nature is True else [-1] if nature is False else [-1,1]
        if mercury_method == 'mercury-strict':
            votes = [min(0, vote) for vote in votes]
        if pos is None:
            votes.append(0)
        low += min(votes)
        high += max(votes)
    return True if low >= 0 else False if high < 0 else None


def relationship(table, natural, distance):
    temporary = 'friend' if distance in table['temporary_friends'] else 'enemy'
    return table['matrix'][natural][temporary]


def dignity_label(table, g, sign, degree, own, relation):
    if g not in table['grahas'] or degree is None or not 0 <= degree < 30:
        return None
    row = table['grahas'][g]
    peak = row['peak_degree_within_sign']
    if sign == row['exaltation'] and degree == peak:
        return 'exaltation-peak'
    lo,hi = table['label_policy']['mt_degrees'][g]
    if sign == row['moolatrikona_sign'] and lo <= degree < hi:
        return 'moolatrikona'
    if g=='mercury' and sign=='virgo' and degree < peak:
        return 'exaltation-sign'
    if own:
        return 'own-sign'
    if sign == row['exaltation']:
        return 'exaltation-sign'
    if sign == row['debilitation']:
        return 'debilitation-sign'
    return relation


def direction(table, house, midpoint):
    for group, ranges in table['class_intervals_deg'].items():
        if any(lo <= midpoint % 360 < hi for lo,hi in ranges):
            steps = (house-table['strongest_house'][group])%12
            return group, 60-10*min(steps,12-steps)
    raise ValueError('Incomplete house class table')


def houses(c, totals, read, method="whole-sign-middle"):
    table = read('vedic/strength/bhava-bala/components.yaml')
    signs = read('vedic/signs/catalog.yaml')['signs']
    natural = read(table['drik']['sign_source'])
    drik = read(table['drik']['base'])['calculation']
    lon = c['longitude']
    altitude = c.get('solar_altitude_deg')
    if altitude is None or c.get('asc') is None:
        return None
    period = 'day' if c.get('sun_above_apparent_horizon', altitude >= -0.83) else 'twilight' if altitude >= -6 else 'night'
    if method == 'sripati':
        if c.get('mc') is None:
            return None
        corners = [c['asc'],(c['mc']+180)%360,(c['asc']+180)%360,c['mc']]
        spans = [(corners[(i+1)%4]-x)%360 for i,x in enumerate(corners)]
        if not isclose(sum(spans),360) or min(spans)<=0:
            return None
    elif method != 'whole-sign-middle':
        raise ValueError('Unknown midpoint convention')
    rows = []
    for h in range(1,13):
        if c.get('asc') is None:
            return None
        idx = (int(c['asc']//30)+h-1)%12
        mid = 30*idx+15
        group, dig = direction(table,h,mid)
        if method == 'sripati':
            quadrant, third = divmod(h-1,3)
            mid = (corners[quadrant]+third*spans[quadrant]/3)%360
            group,_ = direction(table,h,mid)
            strongest = corners[(table['strongest_house'][group]-1)//3]
            dig = abs((mid-strongest)%360-180)/3
        lord = signs[int(mid // 30)]['lord']
        terms = {}
        for p in table['drik']['casters']:
            good = benefic(p,lon,natural)
            if (good is None and p not in ('jupiter','mercury')) or lon.get(p) is None or totals.get(lord) is None:
                return None
            weight = table['drik']['weights'].get(p,table['drik']['weights']['other'])
            terms[p] = aspect(drik,p,(mid-lon[p])%360)*weight*(1 if good or p in ('mercury','jupiter') else -1)
        if method == 'sripati':
            previous_span = spans[(quadrant-1)%4] if third == 0 else spans[quadrant]
            left = (mid-previous_span/6)%360
            width = (previous_span+spans[quadrant])/6
        else:
            left,width = 30*idx,30
        occupancy = sum(weight for body,weight in table['occupants']['weights'].items() if (lon[body]-left)%360 < width)
        time_term = table['birth_time']['award'] if signs[int(mid//30)]['id'] in table['birth_time'][period] else 0
        net = sum(terms.values())
        rows.append(dict(house=h, madhya=mid, lord=lord, sign_class=group,
                         lord_total=totals[lord], dig=dig, signed_aspects=terms, drik=net,
                         occupants=occupancy, birth_time=time_term, total=totals[lord]+dig+net+occupancy+time_term))
    return rows


def bhava_word(totals,h,policy):
    if len(totals)!=12 or None in totals:
        return None
    if len(set(totals))==1:
        return policy['all_equal']
    rank = 1+sum(v>totals[h-1] for v in totals)
    return 'supported' if rank<=policy['supported_through'] else 'steady' if rank<=policy['steady_through'] else 'modest'


def validate_bhava(read, require):
    table = read('vedic/strength/bhava-bala/components.yaml')
    intervals = sorted((lo,hi,g) for g,ranges in table['class_intervals_deg'].items() for lo,hi in ranges)
    edge = 0
    for lo,hi,g in intervals:
        require(lo==edge and hi>lo,'complete sign class coverage')
        best = table['strongest_house'][g]
        require(direction(table,best,lo)==direction(table,best,hi-1e-6)==(g,60) and
                direction(table,(best+5)%12+1,lo)==(g,0),'house distance extrema')
        edge=hi
    require(edge==360 and direction(table,1,255)[0]=='chatushpada' and
            direction(table,4,285)[0]=='jalachara','half-sign ownership')
    w = read('vedic/strength/user-words.yaml')
    require([bhava_word(list(range(12)),h,w['bhava']) for h in (1,4,5,8,9,12)] ==
            ['modest','modest','steady','steady','supported','supported'] and
            bhava_word([8]*12,2,w['bhava'])=='steady' and bhava_word([],1,w['bhava']) is None,'rank boundaries')
    b = read('vedic/planets/benefic-profile.yaml')
    for variant,angles,expected in [('shukla',[0,.01,180,181],[False,True,True,False]),
                                   ('bright-72',[71.99,72,288,288.01],[False,True,True,False]),
                                   ('raman-ashtami',[83.99,84,263.99,264],[False,True,True,False])]:
        require([benefic('moon',{'sun':0,'moon':x},b,variant) for x in angles]==expected,'Moon boundary')
    lon = dict(sun=0,moon=40,mars=80,saturn=120,rahu=150,ketu=330,mercury=200,jupiter=60,venus=270)
    require(benefic('mercury',lon,b) and benefic('mercury',dict(lon,mercury=155),b) is False
            and benefic('mercury',dict(lon,rahu=None),b) is None,'Mercury conjunction or unknown')
    mixed=dict(lon,mercury=1,jupiter=2)
    require(benefic('mercury',mixed,b) and not benefic('mercury',mixed,b,mercury_method='mercury-strict')
            and not benefic('mercury',dict(lon,mercury=1),b),'Mercury tie versus Sun alone')
    rel = read('vedic/dignity/relationships.yaml')
    for nat, yes, no in [('friend','adhi-mitra','sama'),('neutral','mitra','shatru'),('enemy','sama','adhi-shatru')]:
        for d in range(1,13):
            require(relationship(rel,nat,d)==(yes if d in (2,3,4,10,11,12) else no),'directed friendship')
    dignity = read('vedic/dignity/sign-dignities.yaml')
    for g,(lo,hi) in dignity['label_policy']['mt_degrees'].items():
        row=dignity['grahas'][g]
        sign=row['moolatrikona_sign']
        limits=read('vedic/planets/'+g+'.yaml')['graha']['dignity']['moolatrikona_degree_limits']
        require(limits[sign]==[lo,hi],g+' shared MT bounds')
        own=g!='moon'
        def label(deg):
            return dignity_label(dignity,g,sign,deg,own,None)
        require(label(lo+1e-5)==label(hi-1e-5)=='moolatrikona' and label(hi)!='moolatrikona',g+' MT limits')
        if g in ('moon','mercury'):
            require(label(lo)=='exaltation-peak' and label(lo-1e-5)=='exaltation-sign',g+' shared peak')
        else:
            require(label(lo)=='moolatrikona' and label(hi)=='own-sign',g+' own boundary')
    s=read('examples/bhava-bala-s1.yaml')
    reference = read('vedic/strength/shadbala/worked-reference.yaml')['scenario']
    require(s['inputs']=={key:reference['inputs'][key] for key in ('asc','mc','longitude','solar_altitude_deg')} and
            s['lord_totals']=={g:sum(row.values()) for g,row in reference['expected'].items()},'same S1 chart')
    rows=houses(s['inputs'],s['lord_totals'],read)
    expected=s['house_ten']
    actual=rows[9]
    require(all(isclose(a['total'],b,abs_tol=1e-8) for a,b in zip(rows,s['twelve_totals'],strict=True))
            and all(isclose(actual[k],expected[k],abs_tol=1e-8) for k in ('madhya','dig','drik','lord_total','total'))
            and actual['signed_aspects']==expected['signed_aspects']
            and bhava_word(s['twelve_totals'],10,w['bhava'])==s['label']
            and w['labels'][s['label']]==s['public_words'],'S1 house ten worksheet')
    require(houses(dict(s['inputs'],asc=None),s['lord_totals'],read) is None,'missing Lagna')
    for degree,label in read('examples/fixtures/boundaries.yaml')['venus_libra'].items():
        require(dignity_label(dignity,'venus','libra',degree,True,None)==label,'Venus Libra boundary')
    for altitude,period in [(-.83,'day'),(-.831,'twilight'),(-6,'twilight'),(-6.001,'night')]:
        rows=houses(dict(s['inputs'],solar_altitude_deg=altitude),s['lord_totals'],read)
        require(sum(x['birth_time'] for x in rows)==15*len(table['birth_time'][period]),'rising classes')
    require(table['birth_time']['window_tag']=='MODERN','civil twilight provenance')
    sides=[houses(dict(s['inputs'],solar_altitude_deg=a),s['lord_totals'],read) for a in (-.831,-.83)]
    require(any(abs(left['birth_time']-right['birth_time'])==15 for left,right in zip(*sides)),
            'sunrise or sunset can flip the internal time term')
    occupied=next(x for x in rows if x['occupants']!=0)
    require(occupied['occupants']==sum(value for body,value in table['occupants']['weights'].items()
            if s['inputs']['longitude'][body]//30==occupied['madhya']//30),'whole-sign occupants')
    sripati=houses(s['inputs'],s['lord_totals'],read,'sripati')
    require([round(sripati[i-1]['total'],2) for i in (4,9,10)]==[446.44,669.15,545.59], 'Sripati sandhis and rising sign')
    for house, lord in s['sripati_lords'].items():
        row = sripati[house - 1]
        require(row['lord'] == lord and row['lord_total'] == s['lord_totals'][lord],
                f'S1 Sripati lord for house {house}')
    require(isclose(sripati[0]['madhya'],s['inputs']['asc']) and isclose(sripati[9]['madhya'],s['inputs']['mc'])
            and houses(dict(s['inputs'],mc=None),s['lord_totals'],read,'sripati') is None,'Sripati kardinal anchors')
    print('Bhava Bala passed: 12 houses, signed S1 worksheet, dignity boundaries, friendship and qualitative bands.')
