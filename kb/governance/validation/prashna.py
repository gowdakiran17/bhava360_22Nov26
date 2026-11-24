"""Fire Prashna predicates on synthetic question charts with known linear motion."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from kp import numbered


def testimony(chart, case, profile, querent, topic, category):
    positions = {**chart['positions'], **case.get('positions', {})}
    actors = {querent, topic, 'moon'}
    if any(name not in positions or None in positions[name] for name in actors):
        return None, None, set()
    evidence = set()
    contacts = []
    reasons = set()
    for name in {querent, 'moon'} - {topic}:
        a, speed_a = positions[name]
        b, speed_b = positions[topic]
        distance = (int(b // 30) - int(a // 30)) % 12
        signal = profile['sign_steps'].get(distance)
        error = b % 30 - a % 30
        relative = speed_b - speed_a
        limit = min(profile['orb_degrees'][name], profile['orb_degrees'][topic])
        if signal not in ('support', 'friction') or abs(error) > limit:
            continue
        if error and error * relative >= 0:
            continue
        evidence.add(signal)
        reasons.add(("querent" if name == querent else "moon") + "-" + signal)
        if not error:
            continue
        days = -error / relative
        stations = case.get('station_days', {})
        if days > chart['horizon_days'] or any(
            body in stations and stations[body] <= days for body in (name, topic)
        ):
            continue
        if all(0 < pos % 30 + speed * days < 30 for pos, speed in ((a, speed_a), (b, speed_b))):
            contacts.append(days)
    if category == 'lost-item' and int(positions[topic][0] // 30) == chart['asc'] // 30:
        evidence.add('support')
        reasons.add('recovery-context')
    kinds = {frozenset(): 'neither', frozenset(['support']): 'support_only',
             frozenset(['friction']): 'friction_only', frozenset(['support', 'friction']): 'both'}
    delay = min(contacts) if contacts and len(evidence) == 1 else None
    return profile['leaning'][kinds[frozenset(evidence)]], delay, reasons


def validate_prashna(rules, read, evaluate, require):
    routing = read('vedic/prashna/questions.yaml')
    profile = read('vedic/prashna/judgment.yaml')
    ref = read('examples/prashna-reference.yaml')
    boundaries = read('shared/boundaries/responses.yaml')['messages']
    arcs = read('kp/number-horary/249-divisions.yaml')['intervals']
    entries = {r['id'].split('.')[-1]: r for r in rules.values() if r['id'].startswith('vedic.prashna.')}
    require(ref['synthetic'] is True, 'Prashna synthetic fixtures')
    require('kp.number-horary.arc' in rules, 'KP-17 delegation target')
    for category, message in routing['public_referrals'].items():
        require(entries[category]['user_text'] == boundaries[message], category + ' referral')

    covered = set()
    for case in ref['cases']:
        require(case['person'] in ('Scenario 1', 'Scenario 2', 'Scenario 3', 'Scenario 4', 'Scenario 5'), 'synthetic identity')
        chart = ref['charts'][case['chart']]
        site = ref['sites'][chart['site']]
        instant = datetime.fromisoformat(chart['instant'])
        zone = ZoneInfo(site['zone'])
        require(instant.tzinfo and instant.astimezone(zone).strftime('%Y-%m-%d %A') == chart['local'],
                'question civil date at ' + chart['site'])
        intent = case.get('intent')
        category = routing['aliases'].get(case['category'], case['category'])
        category = routing['intent_overrides'].get(intent, category)
        route = routing['route'][category]
        mode = case.get('mode', 'standard')
        admin = case.get('admin', False)
        access = 'public-reflection'
        if category in routing['public_referrals']:
            access = routing['public_referrals'][category] + '-referral'
        if admin and not intent and (category == 'litigation' or mode == 'kerala' and category != 'health'):
            access = 'admin-study'
        primary = route['primary'] if category != 'travel' else routing['travel_primary'].get(case.get('trip'))
        ready = primary is not None and case.get('frame', 'question') == 'question'
        facts = {'category': category, 'access': access, 'mode': mode, 'current_chart_ready': ready}
        day = None
        reasons = set()
        if intent in routing['unsupported_intents']:
            facts = {}
        else:
            require(primary == case['primary'], 'wrong question house: ' + category)
            if mode == 'standard' and ready and access == 'public-reflection':
                asc = int(chart['asc'] // 30)
                rulers = routing['rulers_from_aries']
                lean, delay, reasons = testimony(chart, case, profile, rulers[asc], rulers[(asc+primary-1)%12], category)
                moon = {**chart['positions'], **case.get('positions', {})}.get('moon')
                facts.update({'moon.bound': bool(moon and None not in moon), 'leaning': lean,
                              'timing.verified': delay is not None})
                if delay is not None:
                    day = (instant + timedelta(days=delay)).astimezone(zone).date().isoformat()
            if mode == 'kp-number':
                facts['kp.bound'] = ready and numbered(arcs, case.get('number')) is not None
            if mode == 'kerala':
                sign = case.get('observed_sign')
                facts['arudha.observed'] = type(sign) is int and 1 <= sign <= 12
                heaps = case.get('heaps', [])
                facts['ashtamangala.observed'] = len(heaps) == 3 and all(type(n) is int and n > 0 for n in heaps)
                if 'digits' in case:
                    require([1+(n-1)%8 for n in heaps] == case['digits'], 'observed remainders')
        bound = {'prashna.' + key: value for key, value in facts.items()}
        fired = {key for key, rule in entries.items() if evaluate(rule['conditions'], bound) is True}
        require(fired == set(case['expected']) and day == case.get('day'), f'{case}: fired {fired}, day {day}')
        for reason in reasons:
            require(all(profile['reason_copy'][reason].get(lang) for lang in ('en', 'kn', 'hi')), reason)
        if 'reasons' in case:
            require(reasons == set(case['reasons']), 'Prashna reason selection')
        covered.update(fired)
    require(covered == set(entries), 'missing Prashna predicate coverage')
    print(f"Prashna passed: {len(ref['cases'])} dated cases covering {len(covered)} rules.")
