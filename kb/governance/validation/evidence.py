"""Validate qualitative metadata and its eligibility for synthesis."""
import re


def contribution(block, policy, *, has_parent=False, about_lord=False, polarity=None, compound=None, checker_direction=None):
    """Return an internal direction or None when the observation cannot vote."""
    direction = block['direction']
    if compound is not None:
        direction = policy['compound_direction'].get(compound, 'context')
    if checker_direction is not None:
        direction = checker_direction if checker_direction in ('support','neutral','caution') else 'context'
    if about_lord:
        direction = policy['functional_direction'].get(polarity,'context')
    if block['weight_class']=='context' or direction=='context':
        return None
    if block['weight_class']=='modifier' and not has_parent:
        return None
    return direction


def valid(block, schema, areas, declared):
    if not isinstance(block,dict) or set(block)!=set(schema['required']):
        return False
    if any(block[k] not in schema[k] for k in ('direction','weight_class','time_scope','reference')):
        return False
    relevance=block['area_strength']
    return (isinstance(relevance,dict) and set(relevance)==set(declared) and set(relevance)<=set(areas)
            and all(v in ('core','related','incidental') for v in relevance.values()))


def validate(rules, read, require, root):
    schema=read('SCHEMA.yaml')['reading_evidence']
    areas=read('life-areas/catalog.yaml')['areas']
    policy=read('shared/explain/tone-contribution.yaml')
    slow=set(read('vedic/transits/evidence.yaml')['groups']['long'])
    raw=read('vedic/transits/vedha.yaml')['support_to_obstruction']
    gochara=0
    for key,row in rules.items():
        block=row['evidence']
        require(valid(block,schema,areas,row['life_areas']),key+' invalid evidence')
        d=block['direction']
        if row['system'] in ('tarot','palmistry','face-reading') or 'dasha' in row['topic']:
            require(d=='context' and contribution(block,policy) is None,key+' reflection/period context')
        transit=re.fullmatch(r'vedic\.transits\.(\w+)-moon-house-(\d+)',key)
        if transit or key=='vedic.transits.saturn-moon':
            g,h=(transit[1],int(transit[2])) if transit else ('saturn',1)
            supportive=h in (raw[g] if g in raw else [3,6,11])
            require((d,block['reference'],block['time_scope'],block['weight_class'])==
                    ('support' if supportive else 'caution','moon','transit','primary' if g in slow else 'secondary'),key)
            require(('supportive' if supportive else 'adjustments') in row['rule'],key+' classification text')
            gochara+=1
        if row['topic']=='house-lords' and row['house_pair']['source_house'] in (6,8,12) and row['house_pair']['occupied_house'] in (6,8,12):
            yoga={6:'harsha',8:'sarala',12:'vimala'}[row['house_pair']['source_house']]
            require('vedic.yogas.'+yoga in row['related_rules'],key+' reversal link')
    sample=rules['vedic.planets-in-signs.sun-cancer']['evidence']
    require(contribution(sample,policy) is None and contribution(sample,policy,compound='mitra')=='support'
            and contribution(sample,policy,compound='adhi-shatru')=='caution','resolved compound friendship')
    for key,row in rules.items():
        if row['topic']=='house-lords':
            target=row['house_pair']['occupied_house']
            want='support' if target in (1,4,5,7,9,10) else 'caution' if target in (6,8,12) else 'neutral'
            require(row['evidence']['direction']==want,key+' lord placement')
    require(gochara==108,'complete transit classifications')
    for path in (root/'checkers').glob('*/recipe.yaml'):
        for row in read(path.relative_to(root))['explain_rules']:
            expected=row['direction']
            if expected=='ruler-matrix':
                expected='context'
            require(rules[row['rule_id']]['evidence']['direction']==expected,row['rule_id'])
    spot={'vedic.yogas.kemadruma':'caution','vedic.yogas.sakata':'caution','vedic.yogas.harsha':'support',
          'vedic.planets-in-signs.saturn-aries':'caution','vedic.planets-in-signs.sun-aries':'support'}
    for key,expected in spot.items():
        require(rules[key]['evidence']['direction']==expected,key)
    b=rules['vedic.yogas.harsha']['evidence']
    require(contribution(b,policy,about_lord=True,polarity='Malefic')=='caution' and
            contribution(b,policy,about_lord=True) is None and
            contribution(dict(b,weight_class='modifier'),policy) is None,'context, polarity and unknowns')
    require(not valid(dict(b,area_strength={'invented':'core'}),schema,areas,['invented'])
            and not valid(None,schema,areas,[]),'invalid block and area rejected')
    print(f'Evidence: {len(rules)} reading blocks, 108 Moon transits, checker directions and context gate passed.')
