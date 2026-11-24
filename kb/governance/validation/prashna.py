"""Fire Prashna predicates on synthetic question charts with known linear motion."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bhava_bala import benefic
from kp import numbered
from tajika import contact, reception, transfer, RULERS, FALL


def chart_context(asc, lord, moon, positions, stable_navamsha):
    """Private capacity witnesses qualify testimony and never create a date."""
    if asc is None or lord not in positions or moon not in positions:
        return {}
    def condition(body, angle):
        sign = int(angle % 360 // 30)
        if RULERS[sign] == body:
            return 'own'
        fall = int(FALL[body] // 30)
        return 'exalted' if sign == (fall+6)%12 else 'debilitated' if sign == fall else 'ordinary'
    result = {'lagna_lord': condition(lord, positions[lord][0]),
              'moon': condition(moon, positions[moon][0]),
              'lagna_navamsha': int(asc * 3 // 10) % 12 if stable_navamsha else None,
              'lord_navamsha': condition(lord, positions[lord][0]*9) if stable_navamsha else None}
    if positions.get('sun') and positions['sun'][0] is not None:
        result['moon_phase'] = (positions[moon][0]-positions['sun'][0])%360
    return result


def testimony(chart, case, profile, querent, topic, category):
    positions = {**chart['positions'], **case.get('positions', {})}
    actors = {querent, topic, 'moon'}
    if any(name not in positions or None in positions[name] for name in actors):
        return None, None, set(), None
    conjunction_tone = None
    evidence = set()
    contacts = []
    reasons = set()
    for name in {querent, 'moon'} - {topic}:
        core=profile['core']
        hit=contact(core,name,topic,positions)
        if not hit or hit['state'] not in ('applying','exact'):
            continue
        signal=core['angles'][hit['angle']]
        if hit['angle']==0 and hit['state']=='applying':
            signal = 'support'
            longitudes = {g:position[0] for g,position in positions.items() if position}
            nature = benefic(topic,longitudes,profile['natural_profile'])
            key = {True:'benefic', False:'malefic', None:'unresolved'}[nature]
            conjunction_tone = profile['conjunction']['tone_by_topic_lord'][key]
        if signal=='context':continue
        evidence.add(signal)
        reasons.add(("querent" if name == querent else "moon") + "-" + signal)
        if hit['state']=='exact':
            continue
        days = hit['days']
        stations = case.get('station_days', {})
        if days > chart['horizon_days'] or any(
            body in stations and stations[body] <= days for body in (name, topic)
        ):
            continue
        contacts.append(days)
    # Indirect application requires a verified uninterrupted motion interval.
    # A question with only instantaneous speeds cannot establish that sequence.
    history = case.get('verified_motion_interval')
    if history and history.get('uninterrupted') and history.get('days',0) > 0:
        for bridge in positions.keys() - {querent,topic}:
            kind = transfer(profile['core'], querent, topic, bridge, positions)
            if kind:
                hits = [contact(profile['core'],bridge,g,positions) for g in (querent,topic)]
                if all(h['state'] != 'applying' or h['days'] <= history['days'] for h in hits):
                    evidence.add('support')
                    reasons.add(kind)
    if evidence and reception(querent,topic,positions):
        reasons.add('reception')
    if category == 'lost-item' and int(positions[topic][0] // 30) == chart['asc'] // 30:
        evidence.add('support')
        reasons.add('recovery-context')
    kinds = {frozenset(): 'neither', frozenset(['support']): 'support_only',
             frozenset(['friction']): 'friction_only', frozenset(['support', 'friction']): 'both'}
    delay = min(contacts) if contacts and len(evidence) == 1 else None
    return profile['leaning'][kinds[frozenset(evidence)]], delay, reasons, conjunction_tone


def intent_redirect(intent, routing, messages):
    if isinstance(intent,str):
        intent = ' '.join(intent.casefold().replace('’', "'").split()).rstrip('?')
    canonical = routing['fixed_intent_aliases'].get(intent,intent)
    key = routing['fixed_intent_redirects'].get(canonical)
    if key is None:
        return None
    return {'message': messages[key], 'support_flow': key == 'immediate-support'}


def validate_prashna(rules, read, evaluate, require):
    routing = read('vedic/prashna/questions.yaml')
    profile = read('vedic/prashna/judgment.yaml')
    profile['core']=read(profile['aspect_core'])
    profile['natural_profile'] = read(profile['conjunction']['natural_profile'])
    # Use the Moon as querent so each probe has exactly one eligible pair.
    def probe(topic, longitude, speed=1, **case):
        chart = dict(positions={'moon':(10,13),topic:(longitude,speed)},horizon_days=2)
        return testimony(chart,case,profile,'moon',topic,'job')
    for planet, edge, tone in [('saturn',20.5,'Take care'),('jupiter',20.5,'Supportive'),('venus',19.5,'Supportive')]:
        leaning,days,reasons,quality = probe(planet,edge)
        require((leaning,reasons,quality)==('leans-toward',{'querent-support'},tone) and
                days==(edge-10)/12,'Prashna inclusive conjunction orb '+planet)
        for longitude,speed in [(edge+.001,1),(9,1),(15,13),(10,1)]:
            require(probe(planet,longitude,speed)==('unclear',None,set(),None),
                    'outside, separating, stationary or no future conjunction')
    require(probe('saturn',15,None)==(None,None,set(),None),'missing motion')
    require(probe('saturn',15,station_days={'saturn':.2})[:2]==('leans-toward',None),
            'station interrupts conjunction timing')
    ref = read('examples/prashna-reference.yaml')
    boundaries = read('shared/boundaries/responses.yaml')['messages']
    arcs = read('kp/number-horary/249-divisions.yaml')['intervals']
    entries = {r['id'].split('.')[-1]: r for r in rules.values() if r['id'].startswith('vedic.prashna.')}
    require(ref['synthetic'] is True, 'Prashna synthetic fixtures')
    require('kp.number-horary.arc' in rules, 'KP-17 delegation target')
    for category, message in routing['public_referrals'].items():
        require(entries[category]['user_text'] == boundaries[message], category + ' referral')

    require(chart_context(0,'mars','moon',{'mars':(1,1),'moon':(40,13)},False)['lord_navamsha'] is None,
            'unstable question D9 is withheld')
    require(chart_context(0,'mars','moon',{'mars':(1,1),'moon':(40,13)},True)['lord_navamsha']=='own',
            'stable question D9 dignity')
    fixed = set(read('shared/boundaries/policy.yaml')['copy']['fixed_response_topics'])
    require(set(routing['fixed_intent_redirects']) == fixed - {'diagnosis','legal-outcomes'}, 'sensitive intent coverage')
    require(intent_redirect(None,routing,boundaries) is None, 'ordinary question proceeds')
    for intent,key in routing['fixed_intent_redirects'].items():
        result = intent_redirect(intent,routing,boundaries)
        require(result['message']==boundaries[key] and set(result['message'])=={'en','kn','hi'} and
                result['support_flow']==(intent=='self-harm'), 'localized redirect '+intent)
    for alias, canonical in routing['fixed_intent_aliases'].items():
        require(intent_redirect(alias,routing,boundaries)==intent_redirect(canonical,routing,boundaries),
                'sensitive alias '+alias)
    for aliases, key in [
        (['longevity','ayurdaya','When will I die?'],'personal-limits'),
        (['miscarriage','termination',"baby’s gender"],'life-or-pregnancy'),
        (['lottery','betting','speculation','crypto'],'money-verdict'),
        (['suicidal','self-injury'],'immediate-support'),
    ]:
        for alias in aliases:
            require(intent_redirect(alias,routing,boundaries)==dict(message=boundaries[key],
                    support_flow=key=='immediate-support'),'boundary before chart: '+alias)
    covered = set()
    for case in ref['cases']:
        require(case['person'] in ('Scenario 1', 'Scenario 2', 'Scenario 3', 'Scenario 4', 'Scenario 5'), 'synthetic identity')
        redirect = intent_redirect(case.get('intent'),routing,boundaries)
        if redirect is not None:
            require(redirect['message']==boundaries[case['redirect']] and not case['expected'], 'intent precedes chart binding')
            continue
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
                lean, delay, reasons, conjunction_tone = testimony(chart, case, profile, rulers[asc], rulers[(asc+primary-1)%12], category)
                facts['conjunction_tone'] = conjunction_tone
                if 'conjunction_tone' in case:
                    require(conjunction_tone==case['conjunction_tone'],'question conjunction tone')
                moon = {**chart['positions'], **case.get('positions', {})}.get('moon')
                if moon and None not in moon:
                    positions = {**chart['positions'], **case.get('positions', {})}
                    lord = rulers[asc]
                    if positions.get(lord) and None not in positions[lord]:
                        context = chart_context(chart['asc'], lord, 'moon', positions,
                                                                 case.get('stable_navamsha') is True)
                        facts['strength_context'] = sorted(context.items())
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
    print(f"Prashna passed: {len(ref['cases'])} routing and dated cases covering {len(covered)} rules.")
