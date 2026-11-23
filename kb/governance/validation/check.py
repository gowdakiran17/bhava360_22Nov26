"""Validate the authoring corpus and representative boundary cases (Python 3 + PyYAML)."""
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


# Check display copy at any depth, including examples, remedies and non-rule catalogues.
BANNED_USER_TERMS = re.compile(
    r'\b(?:deaths?|accidents?|fears?|feared|fearing|fearful)\b'
    r'|मृत्यु|मौत|दुर्घटना|हादस[ाे]|भय|(?<![ऀ-ॿ])डर'
    r'|ಮರಣ|ಸಾವು|ಸಾವಿನ|ಮೃತ್ಯು|ಅಪಘಾತ|ಭಯ|ಹೆದರ', re.I)


def validate_user_text(node, location, inside=False):
    if isinstance(node, dict):
        for key, value in node.items():
            validate_user_text(value, f'{location}.{key}', inside or key == 'user_text')
    elif isinstance(node, list):
        for i, value in enumerate(node):
            validate_user_text(value, f'{location}[{i}]', inside)
    elif inside and isinstance(node, str):
        match = BANNED_USER_TERMS.search(node)
        if match:
            raise ValueError(f'{location}: prohibited user_text term {match[0]}')


def main():
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
        validate_user_text(data, path.relative_to(ROOT))
        if 'rule' not in data or path.parent.name=='templates':
            continue
        rid=data['id']
        expected_fields = set(template)
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
        require(set(data['user_text'])=={'en','kn','hi'} and all(data['user_text'].values()),rid)
        require(re.search('[ಀ-೿]',data['user_text']['kn']) and re.search('[ऀ-ॿ]',data['user_text']['hi']),rid)
        require(data['approval'] in ('draft','validated','approved') and data['confidence'] in confidence_values,rid)
        if data['approval']=='approved':
            require(all(v=='approved' for v in data['native_review'].values()),rid)
            require(all(c['verification']=='verified' for c in data['sources']),rid)
            require(profiles[data['doctrine_profile']]['approval']=='approved',rid)
        require('fact' not in data['conditions'],rid)
        require(data['confidence']!='disputed' or data['traditions_differ'],rid)
        require(all(e['effect'] in ('cancel','soften') for e in data['exceptions']),rid)
        check_predicate(data['conditions'],facts)
        for modifier in data['exceptions']+data['strength_notes']:
            check_predicate(modifier['when'],facts)
        require(data['sources'],rid)
        for cite in data['sources']:
            require(cite['work_id'] in sources['works'],rid)
            if cite['edition'] is not None:
                require(sources['editions'][cite['edition']]['work_id']==cite['work_id'],rid)
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
    validate_nakshatras(rules, signs)
    validate_houses(rules, areas['areas'])
    for area in areas['areas']:
        recipe=read(f'life-areas/{area}/reading.yaml')
        require(set(recipe['slots'])==set(recipe['slot_bindings'])==set(areas['detail_slots']),area)
        for slot in recipe['slot_bindings'].values():
            if 'rule_id' in slot:require(slot['rule_id'] in rules,slot)
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
    bands=read('vedic/vargas/methods.yaml')['methods']
    require({r['chart'] for r in bands}=={'D'+str(n) for n in [1,2,3,4,7,9,10,12,16,20,24,27,30,40,45,60]},'vargas')
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
    for method in bands:
        n=int(method['chart'][1:])
        require(len(method['sign_lookup'])==12 and all(len(v)==(5 if n==30 else n) for v in method['sign_lookup'].values()),method['chart'])
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
    kem=rules['vedic.yogas.kemadruma']
    require(evaluate(kem['conditions'],{'d1.moon.eligible_flank_or_companion':False}) is True,'Kemadruma positive')
    require(evaluate(kem['exceptions'][0]['when'],{'d1.moon.distance_from_lagna':4}) is True,'Kemadruma cancellation')
    for case in read('examples/asha.yaml')['cases']:
        check_predicate(case['entry']['conditions'],facts)
        require(evaluate(case['entry']['conditions'],case['assumed_facts']) is True,'synthetic example')
    print(f'{len(rules)} rule entries validated across {len(counts)} systems; {len(facts)} fact keys.')
    print(dict(sorted(counts.items())))
if __name__=='__main__':
    main()
