"""Exercise the draft dosha predicates with invented sidereal positions in degrees."""

BODIES = 'sun moon mars mercury jupiter venus saturn'.split()
NAMES = {'Scenario 1', 'Scenario 2', 'Scenario 3', 'Scenario 4', 'Scenario 5'}


def sign(longitude):
    return int(longitude // 30)


def distance(origin, target):
    return (sign(target) - sign(origin)) % 12 + 1


def mars_facts(chart, config, profile, signs, aspects):
    reference, house_list, relief = (config[k] for k in ('reference', 'house_list', 'relief'))
    bindings = {'regional-lagna': [('lagna', 'lagna_five'), ('lagna', 'four')],
                'raman': [(r, 'family_five') for r in profile['references']],
                'rath': [('lagna', 'family_five'), ('moon', 'lagna_five')],
                'sgs': [('lagna', 'family_five')]}
    if (reference not in profile['references'] or house_list not in profile['house_lists']
            or relief not in profile['relief_profiles']
            or relief in bindings and (reference, house_list) not in bindings[relief]):
        raise ValueError('Unrecognised Manglik binding')
    mars = chart['mars']
    house = distance(chart[reference], mars)
    mars_sign = signs[sign(mars)]['id']
    benefics = ['venus', 'jupiter']
    malefics = ['sun', 'mars', 'saturn', 'rahu', 'ketu']
    if 0 < (chart['moon'] - chart['sun']) % 360 <= 180:
        benefics.append('moon')
    else:
        malefics.append('moon')
    if all(sign(chart['mercury']) != sign(chart[b]) for b in malefics):
        benefics.append('mercury')
    facts = dict(house_list=house_list, reference_distance=house, relief_profile=relief,
                 benefic_contact=any(distance(chart[b], mars) in [1, *aspects[b]] for b in benefics),
                 dignity_exception=mars_sign in ('aries', 'scorpio', 'capricorn'),
                 raman_house_sign=mars_sign in profile['raman_house_sign_pairs'].get(house, []),
                 raman_sign=mars_sign in profile['raman_exempt_signs'],
                 raman_companion=any(sign(mars) == sign(chart[b]) for b in ('moon','jupiter')),
                 raman_ascendant=any(sign(chart['lagna']) == sign(chart[b]) for b in ('jupiter','venus')),
                 sgs_lagna_exempt=signs[sign(chart['lagna'])]['id'] in profile['sgs_exempt_lagnas'],
                 sgs_aspects_candidate=any((house+h-2)%12+1 in profile['house_lists']['family_five']
                                           for h in aspects['mars']))
    return {'dosha.mars.'+key: value for key, value in facts.items()}


def natal_survives(rule, facts, evaluate):
    return evaluate(rule['conditions'], facts) and not any(
        e['effect'] == 'cancel' and evaluate(e['when'], facts) is True for e in rule['exceptions'])


def node_facts(chart, slug):
    arc = [(chart[b]-chart['rahu']) % 360 for b in BODIES]
    facts = {'dosha.axis.confined': all(a <= 180 for a in arc),
             'dosha.axis.strict_interior': all(0 < a < 180 for a in arc)}
    pairs = []
    for body in ('sun','moon','jupiter','saturn'):
        nodes = ['rahu'] if body == 'saturn' else ['rahu','ketu']
        contacts = [(body,n) for n in nodes if sign(chart[body]) == sign(chart[n])]
        key = 'dosha.rahu.shares_saturn' if body == 'saturn' else 'dosha.node.shares_'+body
        facts[key] = bool(contacts)
        pairs.extend(contacts)
    ninth = [(b,n) for b,n in pairs if b in ('sun','moon') and distance(chart['lagna'],chart[b]) == 9]
    facts['dosha.pitru.ninth_node_luminary'] = bool(ninth)
    eligible = {'shrapit': ['saturn'], 'guru-chandal': ['jupiter'], 'grahan': ['sun','moon']}
    bound = ninth if slug == 'pitru' else [(b,n) for b,n in pairs if b in eligible.get(slug, [])]
    facts['dosha.node.contact_within_one_degree'] = any(
        abs((chart[b]-chart[n]+180)%360-180) <= 1 for b,n in bound)
    return facts


def pair_facts(a, b, parihara, signs, rules, raman=False):
    star_a, star_b = (int(m*60//800) for m in (a,b))
    pattern = (0,1,2,2,1,0)
    l1, l2 = [signs[sign(m)]['lord'] for m in (a,b)]
    def friends(lord):
        return rules['vedic.planets.'+lord]['graha']['natural_friendships']['friends']
    quarter_a, quarter_b = (int(m*60//200) for m in (a,b))
    lord_relief = l1 == l2 or l1 in friends(l2) and l2 in friends(l1)
    return {'match.nadi.quarter_relief': raman and pattern[quarter_a%6] != pattern[quarter_b%6],
            'match.bhakoot.raman_relief': raman and lord_relief,
            'match.nadi.same': pattern[star_a%6] == pattern[star_b%6],
            'match.nadi.pada_parihara': parihara and ((star_a == star_b and quarter_a != quarter_b) or (sign(a)==sign(b) and star_a!=star_b)),
            'match.bhakoot.zero': distance(a,b) in (2,12,5,9,6,8),
            'match.bhakoot.lord_parihara': parihara and lord_relief}


def validate_doshas(rules, read, evaluate, require):
    fixture = read('examples/dosha-charts.yaml')
    records = {r['id'].split('.')[-1]:r for r in rules.values() if r['system']=='vedic' and r['topic']=='doshas'}
    required = set('mars-partnership nodal-axis pitru guru-chandal grahan shrapit nadi bhakoot sade-sati ashtama-shani'.split())
    require(set(records) == required, 'dosha inventory')
    require(fixture['synthetic'] is True and set(fixture['charts']) <= NAMES, 'synthetic dosha charts')
    profile = read('vedic/doshas/profiles.yaml')['manglik']
    aspects = read('vedic/aspects/full-graha.yaml')['inclusive_distances']
    signs = read('vedic/signs/catalog.yaml')['signs']
    def chart(name, overrides):
        values = {**fixture['charts'][name], **overrides}
        require(set(values) == set(BODIES+['lagna','rahu']) and all(0<=v<360 for v in values.values()), name)
        return {**values, 'ketu':(values['rahu']+180)%360}
    tested = {slug:set() for slug in records}
    checked_exceptions = {slug:set() for slug in records}
    for case in fixture['cases']:
        slug = case['entry']
        rule = records[slug]
        natal = chart(case['chart'], case.get('positions', {}))
        facts = node_facts(natal, slug)
        config = {**profile['defaults'], **case.get('config', {})}
        mars = mars_facts(natal, config, profile, signs, aspects)
        facts.update(mars)
        if case.get('consent') and 'partner' in case:
            other = chart(case['partner'], case.get('partner_positions', {}))
            facts.update(pair_facts(natal['moon'],other['moon'],case.get('parihara',False),signs,rules,case.get('raman',False)))
            companion = mars_facts(other,config,profile,signs,aspects)
            facts['dosha.mars.pair_balanced'] = all(natal_survives(records['mars-partnership'], f, evaluate)
                                                    for f in (mars,companion))
        if 'transit' in case:
            t = case['transit']
            if t['start'] <= t['at'] < t['end']:
                facts['transit.saturn.distance_from_natal_moon'] = distance(natal['moon'],t['saturn'])
                facts['transit.ingress.reentry'] = t.get('reentry',False)
        formed = evaluate(rule['conditions'],facts)
        require(formed is case['formed'], str(case)+' formation: '+str(formed))
        tested[slug].add(formed)
        if formed:
            active = [i for i,e in enumerate(rule['exceptions']) if evaluate(e['when'],facts) is True]
            require(active == case.get('exceptions',[]), str(case)+' actual exceptions: '+str(active))
            checked_exceptions[slug].update(active)
            if 'strength' in case:
                active_notes = [n['effect'] for n in rule['strength_notes'] if evaluate(n['when'],facts) is True]
                require(active_notes == case['strength'], str(case)+' strength: '+str(active_notes))
    for slug,rule in records.items():
        require({True,False} <= tested[slug], slug+' requires both formation and miss')
        require(checked_exceptions[slug] == set(range(len(rule['exceptions']))), slug+' untested relief')
    print(f"{len(fixture['cases'])} synthetic dosha cases passed across {len(records)} entries.")
