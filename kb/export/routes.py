"""Build candidate sets. Eligibility, consent and fact matching happen downstream."""
from collections import defaultdict


def routing(rules, docs, aliases):
    routes = defaultdict(set)

    def add(route, ids):
        for key in ids:
            if key not in rules:
                raise ValueError(f'{route}: unknown rule {key}')
            routes[route].add(aliases.get(key, key))

    areas = docs['life-areas/catalog.yaml']['areas']
    for area in areas:
        route = 'area/' + area
        routes[route]
        summary = docs.get(f'life-areas/{area}/summary.yaml', {})
        for feed in summary.get('feeds', {}).values():
            add(route, feed)

    vedic = {
        'chart': 'signs planets houses planets-in-signs planets-in-houses house-lords lordships states nakshatras padas',
        'divisional-charts': 'vargas', 'strength': 'strength', 'yogas-doshas': 'yogas doshas',
        'timeline': 'dashas transits annual-chart', 'today': 'panchang festivals transits dashas',
        'panchang': 'panchang festivals', 'matching': 'matching', 'planning': 'muhurta panchang',
        'prashna': 'prashna', 'relocation': 'relocation',
    }
    for key, rule in rules.items():
        system, topic = rule['system'], rule['topic'].split('/')[0]
        if system == 'vedic':
            for screen, topics in vedic.items():
                if topic in topics.split():
                    add('screen/' + screen, [key])
            subtopic = rule['topic']
            if topic in ('dashas','transits','vargas','annual-chart','yogas','doshas'):
                add('screen/'+topic,[key])
            if topic=='strength':
                add('screen/'+subtopic.split('/')[-1],[key])
        else:
            add('screen/' + system, [key])
            if system=='western':
                add('screen/western-'+topic,[key])
        if system in {'vedic', 'jaimini', 'western', 'kp', 'lal-kitab', 'numerology'}:
            for area in rule['life_areas']:
                add('area/' + area, [key])

    for tool in docs['life-areas/catalog.yaml']['checker_ids']:
        route = 'tool/' + tool
        recipe = docs[f'checkers/{tool}/recipe.yaml']
        add(route, [reason['rule_id'] for reason in recipe['explain_rules']])
        profile = docs.get(f'checks/{tool}/profile.yaml', {})
        add(route, profile.get('numerology_ids', []))
        for key, rule in rules.items():
            if rule['system'] == 'numerology':
                school, slug = rule['topic'], key.split('.')[-1]
                if profile.get('adapter') == 'letters' and school in {'chaldean','pythagorean'}:
                    if slug.startswith(('root-', 'compound-', 'master-')):
                        add(route, [key])
                if profile.get('adapter') not in (None,'letters') and school == 'ank-jyotish' and slug.startswith('root-'):
                    add(route, [key])
            if tool == 'big-decision-muhurta' and rule['topic'] in ('muhurta','panchang'):
                add(route, [key])
        if tool == 'house-relocation':
            routes[route].update(routes['screen/vastu'], routes['screen/relocation'])
            add(route, ['vedic.houses.house-4','vedic.planets.moon','vedic.planets-in-houses.moon-house-4'])

    def combine(name, children):
        routes['screen/' + name].update(*(routes[child] for child in children))

    combine('life-areas', ['area/' + area for area in areas])
    combine('check-tools', [r for r in routes if r.startswith('tool/')])
    combine('home', ['screen/today','screen/life-areas'])
    combine('first-look', ['screen/chart','screen/life-areas'])
    combine('ask', ['screen/life-areas','screen/prashna'])
    combine('family-together', ['screen/planning','screen/timeline'])
    combine('notifications', ['screen/today','screen/planning','screen/tarot'])
    add('screen/matching', [key for key in rules if key.startswith('western.synastry.') or
                            key in {'vedic.doshas.mars-partnership','vedic.doshas.nadi','vedic.doshas.bhakoot',
                                    'vedic.houses.house-7','vedic.planets.venus','vedic.vargas.d9-placement'}])
    combine('reports', ['screen/life-areas','screen/chart','screen/divisional-charts','screen/matching','screen/timeline'])
    # Administrative and non-reading screens never provide the only path to a rule.
    private={k for k,r in rules.items() if r.get("visibility")=="admin-only"}
    for ids in routes.values():
        ids.difference_update(private)
    routed = set().union(*routes.values())
    canonical = set(rules) - aliases.keys()
    if routed != canonical-private:
        raise ValueError(f'Unrouted or noncanonical candidates: {sorted(routed ^ canonical)}')
    routes['screen/admin-tester'] = canonical
    for name in ('accounts','onboarding','profiles','language','settings','consent','payments','plus','purchase','glossary'):
        routes['screen/' + name] = set()
    return {name: sorted(ids) for name, ids in sorted(routes.items())}
