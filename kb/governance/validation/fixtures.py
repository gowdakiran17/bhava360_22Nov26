"""Validate recorded acceptance artefacts offline, without calculating a chart."""
import re
from public_copy import check_text

NAMES = ('Asha','Ravi','Meera','Kabir','Dev')
AREAS = {'career','love-marriage','money','health','family-home','learning'}

def validate(rules, read, require, root):
    profiles={}
    pair_groups=set()
    matrix=read('shared/confidence/output-matrix.yaml')['rows']
    for name in NAMES:
        data=read(f'examples/fixtures/{name.lower()}.yaml')
        record=data['consultation']
        require(data['synthetic'] and data['fixture']==name and data['approval']=='draft',name)
        pair_groups.update(data['pair_relationship_examples'])
        provenance=data['provenance']
        require(provenance['actual_backend']=='SEFLG_SWIEPH' and provenance['flags']==65794
                and set(provenance['files_sha256'])=={'sepl_18.se1','semo_18.se1'}
                and all(re.fullmatch('[a-f0-9]{64}',v) for v in provenance['files_sha256'].values()),name+' Swiss files')
        require(set(record['areas'])==AREAS and len(data['grahas'])==9,name+' chart coverage')
        require(record['rule_chain'] and all(rid in rules for rid in record['rule_chain']), name+' unresolved reading')
        for rid,signature in record['matched_predicates'].items():
            require(rules[rid]['conditions']==signature,name+' formation changed for '+rid)
        for ref,chain in record['transits'].items():
            require(all(rule in record['rule_chain'] for rule in chain),name+' transit chain')
        for output,mode in record['confidence'].items():
            require(mode==matrix[output][data['tier']],name+' confidence drift '+output)
        markdown=(root/'examples/worked-readings'/(name.lower()+'.md')).read_text()
        for key,phrase in record['public_en'].items():
            check_text(phrase,key,'en')
            require(phrase in markdown and not re.search(r'\d|\b(?:Strong|Weak|Moderate)\b',phrase),name+' visible copy')
        require(record['matrix_applications']['birth_panchanga']==data['stable_birth_panchanga'],name+' birth Panchanga')
        tw=record['matrix_applications']['twilight']
        require((tw['lower_deg'],tw['upper_approx_deg'],tw['upper_exclusive'])==(-6,-.83,True),'twilight edges')
        if name=='Dev':
            require(data['stable_birth_panchanga']['nakshatra'] is None and record['confidence']['kakshya']=='hide' and
                    record['matrix_applications']['varga_planets']['d9'] and record['confidence']['d9']=='hide',
                    'Dev unstable limb and independent planet-only signs')
            require(data['tier']=='C' and data['lagna'] is None and not record['transits']['lagna'] and
                    'nakshatra' in data['grahas']['moon']['unstable'] and not data['working_instant_periods'] and
                    all(not entry['windows'] for entry in record['areas'].values()),'Dev changing lunar star')
        else:
            require(data['tier']=='A' and len(record['transits']['lagna'])==9 and len(record['grades'])==9,name+' known-time coverage')
        profiles[name]=record
    require(profiles['Asha']['today']['tone']!=profiles['Ravi']['today']['tone'] and
            profiles['Asha']['month_tone']!=profiles['Ravi']['month_tone'],'same-date persona difference')
    require({'six-eight','two-twelve','angle-trine'}<=pair_groups,'three period relationship groups')
    yoga_copy=[r['user_text'] for r in rules.values() if r['system']=='vedic' and r['topic']=='yogas']
    require(all(len({text[locale] for text in yoga_copy})==82 for locale in ('en','kn','hi')),'distinct yoga readings')
    edge=read('examples/fixtures/boundaries.yaml')
    require(edge['venus_libra']=={4.99:'moolatrikona',5:'moolatrikona',14.99:'moolatrikona',15:'own-sign'},
            'four frozen Venus endpoints')
    offsets=read('vedic/strength/ashtakavarga/bindu.yaml')['offsets']['moon']
    require(all(offsets[k]==v for k,v in edge['moon_bav'].items()),'Moon contributor cells')
    require(edge['chara_cycle_two']['expected'] is None,'unimplemented second cycle')
    for category,bad,good in edge['public_copy']:
        try:check_text(bad,'planted','en')
        except ValueError as exc:require(category in str(exc),bad)
        else:raise ValueError('copy gate missed '+bad)
        check_text(good,'allowed','en')
    print('KB-46 passed: five Swiss-file charts, thirty area traces, paired persona readings and boundary probes.')
