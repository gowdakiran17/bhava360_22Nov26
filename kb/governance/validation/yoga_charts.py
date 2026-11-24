"""Fixture-only D1/D9 projections for testing yoga predicates on synthetic chart positions."""

ANGLES = {1, 4, 7, 10}
FIVE = ('mars', 'mercury', 'jupiter', 'venus', 'saturn')
GRAHAS = ('sun', 'moon', *FIVE)


def distance(target, origin):
    return 1 + (target - origin) % 12


def references(read):
    signs = read('vedic/signs/catalog.yaml')['signs']
    planets = {g: read(f'vedic/planets/{g}.yaml')['graha'] for g in GRAHAS}
    return (signs, planets, read('vedic/aspects/full-graha.yaml')['inclusive_distances'],
            read('vedic/strength/shadbala/components.yaml')['minimum_rupas'])


def fixture_facts(chart, tables):
    signs, planets, aspects, minima = tables
    coords = chart['longitude']
    if set(coords) != set(GRAHAS) | {'lagna'} or not all(0 <= x < 360 for x in coords.values()):
        raise ValueError('invalid synthetic D1 coordinates')
    pos = {g: int(x // 30) for g, x in coords.items()}
    lagna, moon = pos['lagna'], pos['moon']
    def lord(h):
        return signs[(lagna + h - 1) % 12]['lord']
    def nav(g):
        return int(coords[g] * 9 // 30) % 12
    def angular(index):
        return any(distance(index, origin) in ANGLES for origin in (lagna, moon))
    def exchange(a, b):
        return a != b and lord(a) != lord(b) and distance(pos[lord(a)], lagna) == b and distance(pos[lord(b)], lagna) == a
    def link(a, b):
        return lord(a) != lord(b) and (pos[lord(a)] == pos[lord(b)] or exchange(a, b))
    values = {}
    for g in GRAHAS:
        dignity = planets[g]['dignity']
        sign = signs[pos[g]]['id']
        values[f'd1.{g}.own_or_exalted'] = sign in dignity['own_sign_degrees'] or sign in dignity['exaltation_peak_degrees']
        values[f'd1.{g}.debilitated'] = sign in dignity['debilitation_peak_degrees']
        for ref in ('sun', 'moon', 'lagna', 'jupiter'):
            values[f'd1.{g}.distance_from_{ref}'] = distance(pos[g], pos[ref])
    for h in range(1, 13):
        values[f'd1.lord_{h}.distance_from_lagna'] = distance(pos[lord(h)], lagna)
    values['d1.moon.eligible_flank'] = any(distance(pos[g], moon) in (2, 12) for g in FIVE)
    benefics = {'jupiter', 'venus'}
    if 0 < (coords['moon'] - coords['sun']) % 360 < 180:
        benefics.add('moon')
    if all(pos['mercury'] != pos[g] for g in ('sun', 'mars', 'saturn')):
        benefics.add('mercury')
    for ref in ('lagna', 'moon'):
        ds = [distance(pos[g], pos[ref]) for g in benefics]
        values[f'd1.{ref}.tenth_has_benefic'] = 10 in ds
        values[f'd1.{ref}.benefics_all_in_upachaya'] = all(d in (3, 6, 10, 11) for d in ds)
    a, b = chart['house_pair']
    ex = exchange(a, b)
    values['d1.lords.reciprocal_exchange'] = ex
    if ex:
        values['d1.lords.exchange_class'] = ('dainya' if {a,b} & {6,8,12} else 'khala' if 3 in (a,b) else 'maha')
    values['d1.lords.kendra_trikona_link'] = any(link(a,b) for a in ANGLES for b in (5,9))
    values['d1.lords.wealth_trine_link'] = any(link(a,b) for a in (2,11) for b in (5,9))
    values['d1.lord_9.dignified_in_angle_or_trine'] = (distance(pos[lord(9)], lagna) in ANGLES | {5,9}
                                                      and values[f'd1.{lord(9)}.own_or_exalted'])
    j = planets['jupiter']
    values['d1.jupiter.saraswati_strength'] = (chart['jupiter_shadbala_rupas'] >= minima['jupiter'] and
        (values['d1.jupiter.own_or_exalted'] or signs[pos['jupiter']]['lord'] in j['natural_friendships']['friends']))
    g = chart['selected_graha']
    deb = values[f'd1.{g}.debilitated']
    exalt = next(iter(planets[g]['dignity']['exaltation_peak_degrees']))
    host = signs[pos[g]]['lord']
    exalt_lord = next(s['lord'] for s in signs if s['id'] == exalt)
    values.update({'d1.dignity.' + key: deb and flag for key, flag in {
        'exchange_with_dispositor': host != g and signs[pos[host]]['lord'] == g,
        'debility_lord_angular': angular(pos[host]),
        'exaltation_lord_angular': angular(pos[exalt_lord]),
        'mutual_kendras': host != exalt_lord and distance(pos[host], pos[exalt_lord]) in ANGLES,
        'dispositor_aspect': distance(pos[g], pos[host]) in aspects[host],
        'exaltee_angular': any(signs[pos[g]]['id'] in planets[h]['dignity']['exaltation_peak_degrees']
                               and angular(pos[h]) for h in GRAHAS),
        'exalted_navamsha': signs[nav(g)]['id'] == exalt,
        'navamsha_lord_support': (distance(pos[signs[nav(g)]['lord']], lagna) in ANGLES | {5,9}
                                  and (lagna % 3 == 0 or nav(lord(1)) % 3 == 0)),
        'recovered_planet_angular': distance(pos[g], lagna) in ANGLES,
    }.items()})
    return values


def validate_yoga_charts(rules, read, evaluate, require):
    yogas = {r['id'].split('.')[-1]: r for r in rules.values() if (r['system'], r['topic']) == ('vedic', 'yogas')}
    tables = references(read)
    observed = {key: set() for key in yogas}
    exceptions = set()
    relief_keys = {leaf['fact'] for leaf in yogas['neecha-bhanga']['conditions']['any']}
    tested_relief = set()
    uncancelled_kemadruma = False
    for case in read('examples/yoga-charts.yaml')['cases']:
        require(case['fixture'] in {'Asha', 'Ravi', 'Meera', 'Kabir', 'Dev'}, 'synthetic fixture name')
        facts = fixture_facts(case, tables)
        if 'multiple_relief_branches' in case:
            require({k for k in relief_keys if facts[k]} == set(case['multiple_relief_branches']), case['id'])
        if 'sole_relief_branch' in case:
            key = case['sole_relief_branch']
            require({k for k in relief_keys if facts[k]} == {key}, case['id'] + ' isolated relief branch')
            require(evaluate(yogas['neecha-bhanga']['conditions'], facts) is True, key)
            tested_relief.add(key)
        for expected, outcome in [('matches', True), ('misses', False)]:
            for key in case.get(expected, []):
                require(evaluate(yogas[key]['conditions'], facts) is outcome, f"{case['id']} {key} {expected}")
                observed[key].add(outcome)
        for key, indices in case.get('exceptions', {}).items():
            require(evaluate(yogas[key]['conditions'], facts) is True, key + ' exception without formation')
            if key == 'kemadruma' and not indices:
                uncancelled_kemadruma = True
            for i, item in enumerate(yogas[key]['exceptions']):
                require(evaluate(item['when'], facts) is (i in indices), key + ' exception case')
                if i in indices:
                    exceptions.add((key,i))
    require(tested_relief == relief_keys, 'missing isolated neecha bhanga branch')
    require(uncancelled_kemadruma, 'missing uncancelled Kemadruma chart')
    require(all(results == {True, False} for results in observed.values()), 'missing positive/negative yoga chart')
    require(exceptions == {(k,i) for k,r in yogas.items() for i in range(len(r['exceptions']))},
            'missing yoga exception chart')
