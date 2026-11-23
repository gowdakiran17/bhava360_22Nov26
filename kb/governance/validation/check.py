"""Validate the authoring corpus and representative boundary cases (Python 3 + PyYAML)."""
from life_areas import check_remedy, validate_life_areas
from collections import Counter
from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[2]
def read(path):
    return yaml.safe_load((ROOT / path).read_text())

def require(ok, message):
    if not ok:
        raise ValueError(message)

def evaluate(node, values):
    if 'fact' in node:
        value = values.get(node['fact'])
        if value is None:
            return None
        return value == node['value'] if node['op'] == 'eq' else value in node['value']
    if 'not' in node:
        result = evaluate(node['not'], values)
        return None if result is None else not result
    group, children = next(iter(node.items()))
    results = [evaluate(child, values) for child in children]
    decisive = group == 'any'
    if decisive in results:
        return decisive
    return None if None in results else not decisive

def check_predicate(node, facts):
    if 'fact' in node:
        spec = facts[node['fact']]
        require(node['op'] in ('eq','in'), str(node))
        values = node['value'] if node['op']=='in' else [node['value']]
        require(isinstance(values,list) and values, str(node))
        for value in values:
            if spec['type'] in ('boolean','integer','enum'):
                expected = {'boolean':bool,'integer':int,'enum':str}[spec['type']]
                require(type(value) is expected, str(node))
            if 'values' in spec:
                require(value in spec['values'], str(node))
            if 'range' in spec:
                lo,hi = spec['range']
                require(lo <= value <= hi, str(node))
        return
    require(len(node)==1, str(node))
    op, children = next(iter(node.items()))
    require(op in ('not','all','any'), str(node))
    children = [children] if op=='not' else children
    require(isinstance(children,list) and children, str(node))
    for child in children:
        check_predicate(child,facts)

def validate_nakshatras(rules, signs):
    catalog = read('vedic/nakshatras/catalog.yaml')['nakshatras']
    fields = read('SCHEMA.yaml')['vedic_nakshatra_entries']['fields']
    lords = 'ketu venus sun moon mars rahu jupiter saturn mercury'.split()
    sign_ids = [item['id'] for item in signs]
    d9 = next(m for m in read('vedic/vargas/methods.yaml')['methods'] if m['chart']=='D9')['sign_lookup']
    records = {r['id']:r for r in rules.values() if r['system']=='vedic' and r['topic']=='nakshatras'}
    require(len(records)==len(catalog)==27, '27 nakshatras required')
    cursor = 0
    for index, star in enumerate(catalog):
        rid = 'vedic.nakshatras.' + star['id']
        record = records[rid]
        data = record['nakshatra']
        require(set(data)==set(fields) and data['number']==star['number']==index+1, rid)
        require(record['conditions']=={'all':[{'fact':'d1.moon.nakshatra','op':'eq','value':star['id']}]}, rid)
        start, end = data['span_arcminutes']
        require(start==cursor and end-start==800, rid+' gap, overlap or width')
        require(data['span_degrees']==[f'{m//60}°{m%60:02d}′' for m in (start,end)],rid+' degrees')
        require(data['vimshottari_lord']==star['vimshottari_lord']==lords[index%9],rid+' lord')
        expected = []
        for j in range(4):
            longitude = start+j*200
            sign = sign_ids[longitude//1800]
            expected.append({'pada':j+1,'rasi':sign,'navamsha':d9[sign][longitude%1800//200]})
        require(data['padas']==expected and data['signs_spanned']==list(dict.fromkeys(x['rasi'] for x in expected)),rid+' padas')
        cursor=end
    require(cursor==360*60,'nakshatra coverage must end at 360 degrees')

def combustion_match(state, graha, sun_longitude, longitude, speed):
    """Evaluate the KB threshold, allowing an unresolved motion branch at a station."""
    direct = state['orbs']['direct'].get(graha)
    if direct is None:
        return False
    retrograde = state['orbs']['retrograde'].get(graha)
    if retrograde is not None and retrograde != direct and (speed is None or speed == 0):
        return None
    if longitude is None or sun_longitude is None:
        return None
    orb = retrograde if retrograde is not None and speed is not None and speed < 0 else direct
    separation = abs((longitude - sun_longitude + 180) % 360 - 180)
    return separation <= orb


def validate_states(rules, facts):
    records = {rid.split('.')[-1]: rule for rid, rule in rules.items()
               if rule['system'] == 'vedic' and rule['topic'] == 'states'}
    fields = read('SCHEMA.yaml')['vedic_state_entries']['fields_by_state']
    require(set(records) == set(fields), 'missing or unexpected planetary state')
    for slug, record in records.items():
        require(set(record['state']) == set(fields[slug]), record['id'] + ' fields')
        fact = 'd1.state.' + slug.replace('-', '_')
        require(facts[fact]['definition'] == 'vedic/states/' + slug + '.yaml', fact)
        test = {'op': 'eq', 'value': True} if slug != 'baladi' else {'op': 'in', 'value': facts[fact]['values']}
        require(record['conditions'] == {'all': [{'fact': fact, **test}]}, fact)

    aspect = records['graha-drishti']['state']
    require(aspect['reference_table'] == 'vedic/aspects/full-graha.yaml', 'full-aspect reference')
    houses = read(aspect['reference_table'])['inclusive_distances']
    require(aspect['inclusive_distances'] == houses, 'full aspect houses differ from table')
    for graha in ('sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu'):
        special = {'mars': [4, 8], 'jupiter': [5, 9], 'saturn': [3, 10]}
        require(houses[graha] == sorted([7] + special.get(graha, [])), graha + ' full aspects')

    combustion = records['combustion']['state']
    require(combustion['reference_table'] == 'vedic/states/combustion-orbs.yaml', 'combustion reference')
    table = read(combustion['reference_table'])
    require(table['orbs'] == combustion['orbs'] and table['boundary'] == combustion['boundary'] == 'inclusive',
            'combustion profile differs from table')
    direct = {'moon': 12, 'mars': 17, 'mercury': 14, 'jupiter': 11, 'venus': 10, 'saturn': 15}
    retro = {g: direct[g] for g in direct if g != 'moon'}
    retro.update(mercury=12, venus=8)
    require(table['orbs'] == {'direct': direct, 'retrograde': retro}, 'combustion reference values')
    for speed, limits in [(1, direct), (-1, retro)]:
        for graha, orb in limits.items():
            for direction in (-1, 1):
                edge = (359 + direction * orb) % 360
                require(combustion_match(combustion, graha, 359, edge, speed), graha + ' threshold')
                require(not combustion_match(combustion, graha, 359, edge + direction * 0.01, speed),
                        graha + ' outside threshold')
    require(combustion_match(combustion, 'venus', 0, 9, 0) is None, 'unresolved Venus station')
    for graha in ('sun', 'rahu', 'ketu'):
        require(combustion_match(combustion, graha, 0, 0, 1) is False, graha + ' ineligible')


def validate_house_lords(rules):
    houses = range(1, 13)
    prefix = 'vedic.house-lords.'
    expected = {f'{prefix}lord-{a}-in-house-{b}' for a in houses for b in houses}
    actual = {r['id'] for r in rules.values() if (r['system'], r['topic']) == ('vedic', 'house-lords')}
    require(actual == expected and len(actual) == 144, 'house-lord grid is incomplete or unexpected')
    for rid in sorted(expected):
        entry = rules[rid]
        pair = entry['house_pair']
        a, b = pair['source_house'], pair['occupied_house']
        require(rid == f'{prefix}lord-{a}-in-house-{b}', rid + ' house pair')
        require(entry['conditions'] == {'all': [{'fact': f'd1.lord_{a}.distance_from_lagna',
                'op': 'eq', 'value': b}]}, rid + ' chart binding')
        src, dest = [rules[f'vedic.houses.house-{i}'] for i in (a, b)]
        tags = set(src['life_areas']) | set(dest['life_areas'])
        require(set(entry['life_areas']) == tags and len(entry['life_areas']) == len(tags), rid + ' life-area union')
        require(pair['source_groups'] == src['bhava']['groupings'] and
                pair['occupied_groups'] == dest['bhava']['groupings'], rid + ' groups')
        swap = f'{prefix}lord-{b}-in-house-{a}' if a != b else None
        require(pair['reciprocal_placement'] == swap, rid + ' reciprocal')
        eligible = {'vedic.yogas.parivartana'} if swap else set()
        for group, key in [({1, 4, 7, 10}, 'raja'), ({2, 11}, 'dhana')]:
            if (a in group and b in (5, 9)) or (b in group and a in (5, 9)):
                eligible.add('vedic.yogas.' + key)
        reversal = {6: 'harsha', 8: 'sarala', 12: 'vimala'}
        if a in reversal and b in reversal:
            eligible.add('vedic.yogas.' + reversal[a])
        require(set(entry['related_rules']) == eligible and eligible <= rules.keys(), rid + ' yoga pointers')


def validate_planets_in_houses(rules, grahas):
    prefix = 'vedic.planets-in-houses.'
    expected = {f'{prefix}{g}-house-{n}' for g in grahas for n in range(1, 13)}
    actual = {r['id'] for r in rules.values() if (r['system'], r['topic']) == ('vedic', 'planets-in-houses')}
    require(actual == expected and len(actual) == 108, 'planet-in-house grid is incomplete or unexpected')
    for rid in expected:
        entry = rules[rid]
        p = entry['placement']
        graha, number = p['graha'], p['house']
        require(rid == f'{prefix}{graha}-house-{number}' and p['reference'] == 'lagna', rid)
        condition = {'all': [{'fact': f'd1.{graha}.house_from_lagna', 'op': 'eq', 'value': number}]}
        require(entry['conditions'] == condition, rid + ' Lagna binding')
        links = ['vedic.doshas.mars-partnership'] if graha == 'mars' and number in (1, 2, 4, 7, 8, 12) else []
        require(entry.get('related_rules', []) == links and all(link in rules for link in links), rid + ' related rules')
        related_id = f'vedic.houses.{graha}-house-{number}'
        require(p['related_placement'] == related_id and rules[related_id]['conditions'] == condition, rid)
        house = rules[f'vedic.houses.house-{number}']
        require(entry['life_areas'] == house['life_areas'], rid + ' house life areas')
        effects = p['grouping_effects']
        require(set(effects) == set(house['bhava']['groupings']) and all(effects.values()), rid + ' groups')
        src = rules[f'vedic.planets.{graha}']['graha']['directional_strength']
        dig = p['dig_bala']
        peak = src['peak_house']
        require(dig['peak_house'] == peak and dig['direction'] == src['direction'] and
                dig['peak_house_matches'] is (None if peak is None else number == peak), rid + ' dig bala')
        require(p['themes'] and entry['strength_notes'] and entry['traditions_differ'], rid)
        if graha in ('rahu', 'ketu'):
            require(entry['confidence'] == 'disputed', rid + ' node doctrine')


def validate_planets_in_signs(rules, grahas, signs):
    prefix = 'vedic.planets-in-signs.'
    expected = {prefix + g + '-' + s['id'] for g in grahas for s in signs}
    actual = {r['id'] for r in rules.values() if r['system'] == 'vedic' and r['topic'] == 'planets-in-signs'}
    require(actual == expected and len(actual) == 108, 'planet-in-sign grid is incomplete or unexpected')
    for graha in grahas:
        planet = rules['vedic.planets.' + graha]['graha']
        relations = planet['natural_friendships']
        for item in signs:
            sign = item['id']
            rasi = rules['vedic.signs.' + sign]['rasi']
            rid = prefix + graha + '-' + sign
            entry = rules[rid]
            require(entry['conditions'] == {'all': [
                {'fact': 'd1.selected_point.graha', 'op': 'eq', 'value': graha},
                {'fact': 'd1.selected_point.sign', 'op': 'eq', 'value': sign}]}, rid + ' chart binding')
            ruler = rasi['ruler']
            relationship = 'self' if graha == ruler else 'unassigned'
            for key, label in [('neutral', 'neutral'), ('friends', 'friend'), ('enemies', 'enemy')]:
                if ruler in relations[key]:
                    relationship = label
            dignity = {'ruler': ruler, 'natural_relation_to_ruler': relationship}
            status = relationship
            if graha == ruler:
                status = 'own'
                dignity['own_sign_degrees'] = [0, 30]
            for key, label in [('exaltation_peak_degrees', 'exalted'), ('debilitation_peak_degrees', 'debilitated')]:
                if graha in rasi[key]:
                    dignity[key] = rasi[key][graha]
                    status = label
            if graha in rasi['moolatrikona_degree_limits']:
                dignity['moolatrikona_degree_limits'] = rasi['moolatrikona_degree_limits'][graha]
            if relations['status'] == 'unassigned':
                require(entry['confidence'] == 'disputed', rid + ' node doctrine')
                status = 'disputed'
            dignity['sign_class'] = status
            require(entry['placement']['dignity'] == dignity, rid + ' dignity disagrees with KB-01/02')
            require(entry['placement']['themes'] and entry['life_areas'] and entry['strength_notes'], rid + ' content')
            if status == 'debilitated':
                pointer = 'vedic.yogas.neecha-bhanga'
                require(any(e.get('rule_id') == pointer and e['when'] == {'fact': 'd1.dignity.neecha_bhanga_matched', 'op': 'eq', 'value': True}
                            and e['effect'] == 'soften' for e in entry['exceptions']), rid + ' cancellation')


def validate_houses(rules, areas):
    groups = {
        'kendra': {1, 4, 7, 10},
        'trikona': {1, 5, 9},
        'dusthana': {6, 8, 12},
        'upachaya': {3, 6, 10, 11},
        'maraka': {2, 7},
    }
    fields = set(read('SCHEMA.yaml')['vedic_house_entries']['fields'])
    for number in range(1, 13):
        rid = f'vedic.houses.house-{number}'
        require(rid in rules, rid + ' missing')
        record = rules[rid]
        data = record['bhava']
        require(set(data) == fields and data['number'] == number, rid + ' fields')
        require(record['conditions'] == {'all': [
            {'fact': 'd1.selected_house.number', 'op': 'eq', 'value': number}
        ]}, rid + ' selection')
        tags = record['life_areas']
        require(tags and set(tags) <= set(areas), rid + ' life areas')
        expected = {group for group, members in groups.items() if number in members}
        require(len(data['groupings']) == len(expected) and set(data['groupings']) == expected, rid + ' groupings')
        require(data['bhavat_bhavam'] == {
            'from_house': number, 'count': number, 'target_house': (2 * number - 2) % 12 + 1
        }, rid + ' derived house')
        for key in ('significations', 'natural_karakas', 'symbolic_body_parts'):
            require(isinstance(data[key], list) and data[key] and all(data[key]), rid + ' ' + key)


OUTER_BODIES = {'uranus', 'neptune', 'pluto'}
OUTER_INPUT = re.compile(r'(?<![a-z0-9])(uranus|neptune|pluto|modern[-_]outer|western)(?![a-z0-9])', re.I)
VEDIC_SYSTEMS = {'vedic', 'jaimini', 'kp'}


def check_classical_inputs(value, facts, location, visited):
    """Follow fact references, including the inputs of derived facts."""
    if isinstance(value, dict):
        for key, item in value.items():
            check_classical_inputs(key, facts, location, visited)
            check_classical_inputs(item, facts, location, visited)
    elif isinstance(value, list):
        for item in value:
            check_classical_inputs(item, facts, location, visited)
    elif isinstance(value, str):
        require(not OUTER_INPUT.search(value), f'{location}: non-classical input {value}')
        if value in facts and value not in visited:
            visited.add(value)
            check_classical_inputs(facts[value], facts, location, visited)


def validate_outer_profiles(rules):
    conventions = read('shared/conventions/profiles.yaml')
    flag = conventions['presentation_flags']['modern_outer']
    require(flag['type'] == 'boolean' and flag['default'] is False and
            set(flag['bodies']) == OUTER_BODIES and flag['calculation_inputs'] == [] and
            set(flag['when_enabled']) == {'chart_overlay', 'labelled_context'}, 'modern_outer scope')
    exclusions = {'dignity', 'friendships', 'dasha', 'yogas', 'ashtakavarga', 'shadbala',
                  'kp_significators', 'kp_star_lords', 'kp_sub_lords'}
    require(exclusions <= set(flag['excluded_from']), 'modern_outer exclusions')
    for name in ('vedic-lahiri-v1', 'kp-placidus-v1'):
        require('modern_outer' in conventions['calculation_profiles'][name]['presentation_flags'], name)
    fields = read('SCHEMA.yaml')['western_outer_planet_entries']['fields']
    for body in OUTER_BODIES:
        rid = 'western.planets.' + body
        record = rules[rid]
        attributes = record['outer_planet']
        require(set(attributes) == set(fields) and all(attributes.values()), rid + ' fields')
        require(record['conditions'] == {'all': [{'fact': 'western.natal.selected_outer',
                 'op': 'eq', 'value': body}]}, rid + ' selection')
        policy = attributes['orbs']
        require(policy['profile'] == 'western/aspects/orbs.yaml' and policy['table'] == 'draft_natal_orbs'
                and policy['boundary'] == 'inclusive', rid + ' natal orb profile')
        major = {'conjunction', 'opposition', 'square', 'trine', 'sextile'}
        table = read(policy['profile'])[policy['table']]
        require(set(policy['personal_aspects']) == major and all(table[a]['orb'] > 0 for a in major),
                rid + ' personal aspects')


# Check display copy at any depth, including examples, remedies and non-rule catalogues.
BANNED_USER_TERMS = re.compile(
    r'\b(?:deaths?|accidents?|fears?|feared|fearing|fearful)\b'
    r'|(?:ka[nṇ][tṭ]aka|a[sṣ]h?[tṭ]ama)[ -]*(?:s[hś]ani)|s[aā][dḍ][eē][ -]*s[aā]t[iī]'
    r'|(?:कंटक|कण्टक|अष्टम)\s*शनि|साढ़े\s*साती|(?:ಕಂಟಕ|ಅಷ್ಟಮ)\s*ಶನಿ|ಸಾಡೇ\s*ಸಾತಿ'
    r'|मृत्यु|मौत|दुर्घटना|हादस[ाे]|भय|(?<![ऀ-ॿ])डर'
    r'|ಮರಣ|ಸಾವು|ಸಾವಿನ|ಮೃತ್ಯು|ಅಪಘಾತ|ಭಯ|ಹೆದರ', re.I)


def validate_user_text(node, location, required, supported):
    if isinstance(node, list):
        for index, value in enumerate(node):
            validate_user_text(value, f'{location}[{index}]', required, supported)
    elif isinstance(node, dict):
        for key, value in node.items():
            field = f'{location}.{key}'
            if key == 'remedy' and value is not None:
                check_remedy(value, field, require)
            if key != 'user_text':
                validate_user_text(value, field, required, supported)
                continue
            require(isinstance(value, dict), f'{field}: expected locale map')
            require(required <= value.keys() <= supported, f'{field}: invalid locale keys {list(value)}')
            for locale, translation in value.items():
                require(isinstance(translation, str) and translation.strip(), f'{field}.{locale}: empty text')
                match = BANNED_USER_TERMS.search(translation)
                if match:
                    raise ValueError(f'{field}.{locale}: prohibited user_text term {match[0]}')


def main():
    locales = read('SCHEMA.yaml')['supported_locales']
    required = set(locales['required'])
    supported = required | set(locales['planned'])
    require(locales['fallback'] in required, 'fallback locale needs required text')
    require(set(read('governance/review/identifiers.yaml')['locales']) == supported, 'locale registry')
    confidence_values=read('governance/review/identifiers.yaml')['confidence_values']
    template=read('templates/entry.yaml')
    facts=read('shared/fact-dictionary/catalog.yaml')['facts']
    profiles=read('shared/conventions/profiles.yaml')['doctrine_profiles']
    sources=read('shared/source-editions/catalog.yaml')
    areas=read('life-areas/catalog.yaml')
    graha_fields=set(read('SCHEMA.yaml')['vedic_planet_entries']['fields'])
    counts=Counter()
    rules={}
    for path in sorted(ROOT.rglob('*.yaml')):
        data=yaml.safe_load(path.read_text())
        validate_user_text(data, path.relative_to(ROOT), required, supported)
        system_dir = path.relative_to(ROOT).parts[0]
        if system_dir in VEDIC_SYSTEMS:
            if 'rule' in data:
                inputs = [data['conditions'], *[m['when'] for m in data['strength_notes'] + data['exceptions']]]
                inputs.extend(data[k] for k in ('graha', 'bhava', 'rasi', 'nakshatra', 'state', 'placement', 'house_pair', 'varga') if k in data)
            else:
                # Calculation tables include candidate lists, weights and lord assignments.
                inputs = data
            check_classical_inputs(inputs, facts, str(path.relative_to(ROOT)), set())
        if 'rule' not in data or path.parent.name=='templates':
            continue
        rid=data['id']
        expected_fields = set(template)
        if data['system']=='palmistry' and 'guided' in data:
            expected_fields.add('guided')
        if data['system']=='tarot':
            expected_fields.add('card_profile')
        if data['system']=='vastu' and 'vastu' in data:
            expected_fields.add('vastu')
        if data['topic']=='matching' and 'matching' in data:
            expected_fields.add('matching')
        if data['topic']=='muhurta' and 'activity_profile' in data:
            expected_fields.add('activity_profile')
        if data['topic']=='strength/ashtakavarga':
            expected_fields.add('calculation')
        if data['topic']=='strength/shadbala' and rid!='vedic.strength-shadbala.six-components':
            expected_fields.add('calculation')
        if data['system'] == 'vedic' and data['topic'] == 'house-lords':
            expected_fields.update(('house_pair', 'related_rules'))
        if data['system'] == 'vedic' and data['topic'] in ('planets-in-signs', 'planets-in-houses'):
            expected_fields.add('placement')
        if data['topic'] == 'planets-in-houses' and 'related_rules' in data:
            expected_fields.add('related_rules')
        if data['system'] == 'vedic' and data['topic'] == 'vargas':
            expected_fields.add('varga')
        if data['system'] == 'vedic' and data['topic'] == 'states':
            expected_fields.add('state')
        if data['topic'] == 'doshas' and rid.split('.')[-1] in ('nadi','bhakoot','ashtama-shani','sade-sati'):
            expected_fields.add('reference_paths')
            module = 'matching' if rid.split('.')[-1] in ('nadi','bhakoot') else 'transits'
            paths = data['reference_paths']
            require(paths and all(re.fullmatch(r'vedic/'+module+r'/[a-z-]+\.yaml', p)
                                  and (ROOT/p).is_file() for p in paths), rid+' module pointers')
        if rid in {'western.planets.' + name for name in OUTER_BODIES}:
            expected_fields.add('outer_planet')
        if data['system']=='vedic' and data['topic']=='signs':
            expected_fields.add('rasi')
            require(set(data['rasi'])=={'element','modality','ruler','traditional_gender','nature',
                    'kalapurusha_body_parts','exaltation_peak_degrees','debilitation_peak_degrees','moolatrikona_sign_for','moolatrikona_degree_limits'},rid)
        if data['system']=='vedic' and data['topic']=='planets':
            expected_fields.add('graha')
            require(set(data['graha'])==graha_fields,rid)
        if re.fullmatch(r'vedic\.houses\.house-(?:[1-9]|1[0-2])', rid):
            expected_fields.add('bhava')
        if data['system']=='vedic' and data['topic']=='nakshatras':
            expected_fields.add('nakshatra')
        require(set(data)==expected_fields and rid not in rules,rid)
        rules[rid]=data
        require(re.fullmatch(r'[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*',rid),rid)
        require(path.parent==ROOT/data['system']/data['topic'],rid)
        require(data['doctrine_profile'] in profiles and set(data['life_areas'])<=areas['areas'].keys(),rid)
        if data['remedy'] is not None:
            require(isinstance(data['remedy'], dict) and 'user_text' in data['remedy'], rid + ' remedy.user_text')
        require(re.search('[ಀ-೿]',data['user_text']['kn']) and re.search('[ऀ-ॿ]',data['user_text']['hi']),rid)
        require(data['approval'] in ('draft','validated','approved') and data['confidence'] in confidence_values,rid)
        if data['approval']=='approved':
            require(all(v=='approved' for v in data['native_review'].values()),rid)
            require(all(c['verification']=='verified' for c in data['sources']),rid)
            require(profiles[data['doctrine_profile']]['approval']=='approved',rid)
        require('fact' not in data['conditions'],rid)
        require(data['confidence'] not in ('low','disputed') or any(t.get('note','').strip() for t in data['traditions_differ']),rid)
        require(all(e['effect'] in ('cancel','soften') for e in data['exceptions']),rid)
        check_predicate(data['conditions'],facts)
        for modifier in data['exceptions']+data['strength_notes']:
            check_predicate(modifier['when'],facts)
        require(data['sources'],rid)
        for cite in data['sources']:
            require(cite['work_id'] in sources['works'],rid)
            if cite['edition'] is not None:
                require(sources['editions'][cite['edition']]['work_id']==cite['work_id'],rid)
            if data['topic'] == 'planets-in-signs' and cite['work_id'] == 'brihat-jataka' and cite['chapter'] == 18:
                require(cite['verification'] == ('verified' if cite['verse'] else 'chapter-only'), rid + ' chapter 18 locator')
            if cite['verification']=='verified':
                require(cite['edition'] and (cite['verse'] or cite['other_locator']),rid)
        require(evaluate(data['conditions'],{}) is None,rid)
        counts[data['system']]+=1
    grahas = read('vedic/planets/catalog.yaml')['grahas']
    signs = read('vedic/signs/catalog.yaml')['signs']
    for graha in grahas:
        record = rules['vedic.planets.' + graha]
        require(record['conditions'] == {'all':[{'fact':'d1.selected_point.graha','op':'eq','value':graha}]}, graha)
        functional = record['graha']['nature']['functional_nature']
        require(set(functional)=={s['id'] for s in signs},graha)
        for lagna in signs:
            houses = sorted(1+(s['number']-lagna['number'])%12 for s in signs if s['lord']==graha)
            qualifies = bool(set(houses) & {4,7,10} and set(houses) & {5,9})
            require(functional[lagna['id']]=={'houses_ruled':houses,'yogakaraka':qualifies},(graha,lagna['id']))
        dignity = record['graha']['dignity']
        expected = {k:{} for k in ('own_sign_degrees','exaltation_peak_degrees','debilitation_peak_degrees','moolatrikona_degree_limits')}
        for sign in signs:
            name = sign['id']
            attributes = rules['vedic.signs.' + name]['rasi']
            if attributes['ruler'] == graha:
                expected['own_sign_degrees'][name] = [0,30]
            for field in ('exaltation_peak_degrees','debilitation_peak_degrees','moolatrikona_degree_limits'):
                if graha in attributes[field]:
                    expected[field][name] = attributes[field][graha]
            require((graha in attributes['moolatrikona_sign_for']) == (graha in attributes['moolatrikona_degree_limits']),name)
        require(dignity == expected, graha + ' dignity disagrees with sign entries')
    validate_house_lords(rules)
    validate_planets_in_houses(rules, grahas)
    validate_planets_in_signs(rules, grahas, signs)
    validate_nakshatras(rules, signs)
    validate_houses(rules, areas['areas'])
    validate_outer_profiles(rules)
    validate_states(rules, facts)
    for area in areas['areas']:
        recipe=read(f'life-areas/{area}/reading.yaml')
        require(set(recipe['slots'])==set(recipe['slot_bindings'])==set(areas['detail_slots']),area)
        for slot in recipe['slot_bindings'].values():
            if 'rule_id' in slot:require(slot['rule_id'] in rules,slot)
    validate_life_areas(rules, read, require, ROOT)
    from western import validate_western
    validate_western(rules,read,evaluate,require)
    from numerology import validate_numerology
    validate_numerology(rules,read,evaluate,require,ROOT)
    from vastu import validate_vastu
    validate_vastu(rules,read,evaluate,require,ROOT)
    for name in areas['checker_ids']:
        recipe=read(f'checkers/{name}/recipe.yaml')
        require(len(recipe['reason_channels'])>=3 and recipe['compare_limit']==3,name)
        for rule in recipe['explain_rules']:
            require(rule['rule_id'] in rules and rule['evidence'] in facts,name)
    require(counts['tarot']==156,'78 tarot cards × 2 orientations')
    for card in facts['draw.card']['values']:
        for orientation in ('upright','reversed'):
            matched=[r for r in rules.values() if r['system']=='tarot' and evaluate(r['conditions'],{'draw.card':card,'draw.orientation':orientation})]
            require(len(matched)==1,(card,orientation))
    from tarot_cards import validate_tarot
    validate_tarot(rules,read,require,ROOT)
    from palmistry import validate_palmistry
    validate_palmistry(rules,read,require,ROOT,evaluate)
    from consistency import validate_consistency
    validate_consistency(rules,read,require,ROOT)
    from glossary import validate_glossary
    validate_glossary(rules,read,require,ROOT)
    from shadbala import validate_shadbala
    validate_shadbala(rules, read, require)
    from muhurta import validate_muhurta
    validate_muhurta(rules,read,evaluate,require)
    from prashna import validate_prashna
    validate_prashna(rules, read, evaluate, require)
    from matching import validate_matching
    validate_matching(rules, read, evaluate, require, ROOT)
    from panchang import validate_panchang
    validate_panchang(rules,read,evaluate,require)
    from jaimini import validate_jaimini
    validate_jaimini(rules,read,evaluate,require)
    from kp import validate_kp
    validate_kp(rules,read,evaluate,require)
    from gochara import validate_gochara
    validate_gochara(rules,read,evaluate,require)
    from other_dashas import validate_other_dashas
    validate_other_dashas(rules,read,evaluate,require)
    from vimshottari import validate_vimshottari
    validate_vimshottari(rules,read,evaluate,require)
    from varga_charts import validate_vargas
    validate_vargas(rules, read, require)
    from ashtakavarga import validate_ashtakavarga
    validate_ashtakavarga(rules,read,evaluate,require)
    bindu=read('vedic/strength/ashtakavarga/bindu.yaml')
    for reference_positions in ([0]*8,list(range(8)),[11,6,2,0,1,4,8,3]):
        sums=[0]*12
        for graha,contributors in bindu['offsets'].items():
            row=[0]*12
            for planet,origin in zip(bindu['contributors'],reference_positions):
                offsets=contributors[planet]
                require(len(offsets)==len(set(offsets)) and all(1<=n<=12 for n in offsets),graha)
                for offset in offsets:row[(origin+offset-1)%12]+=1
            require(sum(row)==bindu['totals'][graha],graha)
            sums=[a+b for a,b in zip(sums,row)]
        require(sum(sums)==337,'raw SAV')
    for system in ['chaldean','pythagorean']:
        mapping=read('numerology/'+system+'/calculation.yaml')['mapping']
        require(sorted(''.join(mapping.values()))==list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),system)
    require(set(read('numerology/chaldean/compounds.yaml')['original_editorial_themes'])==set(range(10,53)),'compound range')
    require(sum(read('vedic/dashas/vimshottari/periods.yaml')['sequence'].values())==120,'Vimshottari')
    require(sum(read('vedic/dashas/yogini/periods.yaml')['sequence'].values())==36,'Yogini')
    require(sum(read('vedic/matching/factors.yaml')['weights'].values())==36,'Ashtakoota')
    require(len(read('vedic/padas/namakshar.yaml')['syllables'])==27,'nakshatras')
    arcs=read('kp/number-horary/249-divisions.yaml')['intervals']
    require(len(arcs)==249 and arcs[0]['start_arcsec']==0 and arcs[-1]['end_arcsec']==1296000,'KP coverage')
    for i,arc in enumerate(arcs):
        require(arc['number']==i+1 and arc['start_arcsec']<arc['end_arcsec'],'KP interval')
        require(arc['start_arcsec']//108000==(arc['end_arcsec']-1)//108000==arc['sign']-1,'KP cusp split')
        if i:require(arcs[i-1]['end_arcsec']==arc['start_arcsec'],'KP boundary')
    check=read('vedic/strength/ashtakavarga/worked-reference.yaml')
    expected=check['expected_sav']
    computed=[0]*12
    for graha,contributors in bindu['offsets'].items():
        row=[0]*12
        for key,origin in zip(check['contributor_order'],check['origin_indices_zero_based']):
            for h in contributors[key]:
                row[(origin+h-1)%12]+=1
        if graha=='mercury':require(row==check['expected_mercury_bav'],'published Mercury BAV')
        computed=[a+b for a,b in zip(computed,row)]
    require(computed==expected,'published SAV, sign by sign')
    example=read('vedic/strength/shadbala/worked-reference.yaml')
    require(sum(example['sun_sthana_components'].values())==example['expected_virupas'],'published Sthana subtotal')
    mars=rules['vedic.yogas.ruchaka']['conditions']
    require(evaluate(mars,{'d1.mars.distance_from_lagna':1,'d1.mars.own_or_exalted':True}) is True,'Ruchaka positive')
    require(evaluate(mars,{'d1.mars.distance_from_lagna':2}) is False,'Ruchaka negative')
    require(evaluate(mars,{'d1.mars.distance_from_lagna':1}) is None,'Ruchaka incomplete')
    from yoga_charts import validate_yoga_charts
    validate_yoga_charts(rules, read, evaluate, require)
    from dosha_charts import validate_doshas
    validate_doshas(rules, read, evaluate, require)
    kem=rules['vedic.yogas.kemadruma']
    require(evaluate(kem['conditions'],{'d1.moon.eligible_flank':False}) is True,'Kemadruma positive')
    require(evaluate(kem['exceptions'][0]['when'],{'d1.moon.distance_from_lagna':4}) is True,'Kemadruma cancellation')
    for case in read('examples/asha.yaml')['cases']:
        require(case['entry']['id'] in rules, 'synthetic example must reference a current rule')
        check_predicate(case['entry']['conditions'],facts)
        require(evaluate(case['entry']['conditions'],case['assumed_facts']) is True,'synthetic example')
    print(f'{len(rules)} rule entries validated across {len(counts)} systems; {len(facts)} fact keys.')
    print(dict(sorted(counts.items())))
if __name__=='__main__':
    main()
