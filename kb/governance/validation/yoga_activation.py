"""Resolve a single bound formation witness. Unknowns are distinct from inactive periods."""
from yoga_charts import GRAHAS, FIVE, ANGLES, distance
from functional import OWNERS
from yoga_formation import participants


def resolve(formed, grahas, effects, grades, maha, antar, private=False):
    if formed is False or 'cancel' in effects:
        return None,False,'omitted'
    if formed is None or not grahas or 'unknown-cancel' in effects:
        return None,None,'withheld'
    strengths=[grades.get(g) for g in grahas]
    if any(g not in ('Strong','Moderate','Weak') for g in strengths):
        return None,None,'withheld'
    gate='hidden' if all(g=='Weak' for g in strengths) else 'mild' if 'Weak' in strengths else 'full'
    active=True if maha in grahas or antar in grahas else None if not maha or not antar else False
    if private or gate=='hidden':
        return gate,active,'staff-only'
    if active is not True:
        return gate,active,'yoga-background'
    return gate,active,'yoga-mild' if gate=='mild' or 'soften' in effects else 'normal'


def project(row, formed, witness, facts, grades, maha, antar, evaluate):
    """Match the stored predicates for this witness before exposing any period reason."""
    effects=[]
    for exception in row['exceptions']:
        matched=evaluate(exception['when'],facts)
        if matched is True:
            effects.append(exception['effect'])
        elif matched is None:
            effects.append('unknown-'+exception['effect'])
    gate,active,display=resolve(formed,witness,effects,grades,maha,antar,
                                row.get('visibility')=='admin-only')
    if 'unknown-soften' in effects and display=='normal':
        display='yoga-mild'
    prefix='vedic.yoga.'+row['id'].split('.')[-1]+'.'
    return {prefix+'gate':gate,prefix+'active':active,'display':display,
            'period_evidence':active is True and display in ('normal','yoga-mild')}


def alternate_witnesses(slug, signs, house_lords, aspects, variant):
    """Additional witnesses only for the explicitly selected formation variant."""
    if variant!='mutual-full-aspect':return []
    if slug=='chandra-mangala':
        pairs=[('moon','mars')]
    elif slug in ('raja','dhana'):
        pairs=[(house_lords[a],house_lords[b]) for a in ((1,4,7,10) if slug=='raja' else (2,11))
               for b in (5,9)]
    else:
        return []
    return [{a,b} for a,b in pairs if a!=b and a in signs and b in signs and
            distance(signs[b],signs[a]) in aspects[a] and distance(signs[a],signs[b]) in aspects[b]]


def existing_participants(slug,row,case,tables,facts):
    coords=case['longitude']
    signs={g:int(v//30) for g,v in coords.items()}
    lagna=signs['lagna']
    def lord(h):return OWNERS[(lagna+h-1)%12]
    def host(g):return OWNERS[signs[g]]
    def dist(g,ref):return distance(signs[g],signs[ref])
    def witness(a,b):
        return a!=b and (signs[a]==signs[b] or host(a)==b and host(b)==a)
    tokens=row['participants']
    group={g for g in tokens if g in GRAHAS}
    group.update(lord(int(t.split(':')[1])) for t in tokens if t.startswith('lord:'))
    if 'flanking-grahas' in tokens:
        ref='sun' if 'sun' in group else 'moon'
        sides={'sunapha':[2],'vesi':[2],'anapha':[12],'vosi':[12]}.get(slug,[2,12])
        group.update(g for g in FIVE if dist(g,ref) in sides)
    elif 'exchanging-lords' in tokens:
        group.update(lord(h) for h in case['house_pair'])
    elif slug in ('raja','dhana'):
        # Keep distinct lord-pair matches distinct for both activation and cancellation.
        pairs=[{lord(a),lord(b)} for a in ([2,11] if slug=='dhana' else sorted(ANGLES))
               for b in [5,9] if witness(lord(a),lord(b))]
        return pairs
    elif slug in ('amala','vasumati'):
        acceptable=[10] if slug=='amala' else [3,6,10,11]
        eligible={'jupiter','venus'}
        if 0<(coords['moon']-coords['sun'])%360<180:eligible.add('moon')
        if all(signs['mercury']!=signs[g] for g in ('mars','sun','saturn')):eligible.add('mercury')
        return [match for ref in ('lagna','moon') if
                (match:={g for g in eligible if dist(g,ref) in acceptable}) and
                (slug=='amala' or match==eligible)]
    elif 'recovered-graha' in tokens:
        g=case['selected_graha'];group.add(g)
        exaltation=next(iter(tables[1][g]['dignity']['exaltation_peak_degrees']))
        exalt_lord=next(s['lord'] for s in tables[0] if s['id']==exaltation)
        branches={'exchange_with_dispositor':{host(g)},'debility_lord_angular':{host(g)},
                  'exaltation_lord_angular':{exalt_lord},'mutual_kendras':{host(g),exalt_lord},
                  'dispositor_aspect':{host(g)},'exalted_navamsha':set(),
                  'navamsha_lord_support':{OWNERS[int(coords[g]*9//30)%12],lord(1)},
                  'exaltee_angular':{p for p in GRAHAS if tables[0][signs[g]]['id'] in tables[1][p]['dignity']['exaltation_peak_degrees']}}
        return [group|extra for k,extra in branches.items() if facts['d1.dignity.'+k]]
    return [group]


def validate(yogas,read,evaluate,require,tables,fixture_facts):
    doc=read('examples/yoga-charts.yaml')
    legacy={case['id']:case for case in doc['cases']}
    scenario=doc['gate_cases']
    require(set(scenario)==set(yogas),'gate scenario per yoga')
    for slug,row in yogas.items():
        case=scenario[slug]
        for polarity in ('positive','negative'):
            if 'formation' in row:
                chart={**doc['shape_defaults'],**case[polarity]}
                chart['full_aspects']=tables[2]
                group=participants(slug,row['formation'],chart)
                formed=evaluate(row['conditions'],{row['conditions']['all'][0]['fact']:None if group is None else bool(group)})
                witnesses=[group]
            else:
                chart=legacy[case[polarity]]
                facts=fixture_facts(chart,tables)
                formed=evaluate(row['conditions'],facts)
                witnesses=existing_participants(slug,row,chart,tables,facts) if formed else []
            require(formed==(polarity=='positive'),(slug,polarity))
            if formed:
                require(witnesses and all(witnesses),slug+' forming grahas')
                actual=witnesses[0]
        a=sorted(actual)[0]
        outsider=next(g for g in (*GRAHAS,'rahu','ketu') if g not in actual)
        normal=dict.fromkeys(actual,'Moderate')
        private=row.get('visibility')=='admin-only'
        def check(grades,maha,antar,effects,expected):
            result=resolve(True,actual,effects,grades,maha,antar,private)
            require(result==expected,(slug,result,expected))
        check(normal,outsider,a,[],('full',True,'staff-only' if private else 'normal'))
        check(normal,outsider,outsider,[],('full',False,'staff-only' if private else 'yoga-background'))
        check(normal,None,outsider,[],('full',None,'staff-only' if private else 'yoga-background'))
        check(dict.fromkeys(actual,'Weak'),a,outsider,[],('hidden',True,'staff-only'))
        check(normal,a,outsider,['cancel'],(None,False,'omitted'))
        check(normal,a,outsider,['soften'],('full',True,'staff-only' if private else 'yoga-mild'))
        if len(actual)>1:
            check({**normal,a:'Weak'},a,outsider,[],('mild',True,'staff-only' if private else 'yoga-mild'))
        base_facts={}
        for ex in row['exceptions']:
            # Normalize legacy nested conditions to a known non-match in this gate probe.
            def leaves(node):
                if 'fact' in node: yield node
                elif 'not' in node: yield from leaves(node['not'])
                else:
                    for child in next(iter(node.values())):yield from leaves(child)
            for t in leaves(ex['when']):
                v=t['value']
                base_facts[t['fact']]=False if isinstance(v,bool) else 0 if isinstance(v,(list,int)) else 'unmatched'
        withdrawal='d1.yoga.foundation_cancelled'
        result=project(row,True,actual,dict(base_facts,**{withdrawal:True}),normal,a,outsider,evaluate)
        require(result['display']=='omitted' and not result['period_evidence'],slug+' bound cancellation')
        result=project(row,True,actual,{},normal,a,outsider,evaluate)
        require(result['display']=='withheld' and not result['period_evidence'],slug+' unknown cancellation')
        for ex in row['exceptions']:
            # Bound predicate expectations and each recognized cancellation/softening effect.
            def inputs(node):
                if 'fact' in node:
                    value=node['value']
                    return {node['fact']:value[0] if node['op']=='in' else value}
                if 'not' in node:return {k:not v for k,v in inputs(node['not']).items()}
                return {k:v for child in next(iter(node.values())) for k,v in inputs(child).items()}
            require(evaluate(ex['when'],inputs(ex['when'])) is True,(slug,ex))
    y=doc['Scenario Y4']
    sep=abs((y['mercury_deg']-y['sun_deg']+180)%360-180)
    orb=read('vedic/states/combustion-orbs.yaml')['orbs'][y['motion']]['mercury']
    r=yogas['budhaditya']
    formed=evaluate(r['conditions'],{'d1.mercury.distance_from_sun':distance(int(y['mercury_deg']//30),int(y['sun_deg']//30))})
    ex=next(e for e in r['exceptions'] if e['when'].get('fact')=='d1.yoga.mercury_combust')
    effects=[ex['effect']] if evaluate(ex['when'],{'d1.yoga.mercury_combust':sep<=orb}) else []
    for antar,expected in y['expected'].items():
        require(list(resolve(formed,{'sun','mercury'},effects,y['grades'],'saturn',antar))==expected,'Scenario Y4 '+antar)
    require(alternate_witnesses('chandra-mangala',{'moon':0,'mars':6},{},tables[2],'mutual-full-aspect')
            and not alternate_witnesses('chandra-mangala',{'moon':0,'mars':6},{},tables[2],None),'optional mutual aspect')
    for antar,expected in y['expected'].items():
        bound={ex['when']['fact']:False for ex in r['exceptions']}
        bound['d1.yoga.mercury_combust']=sep<=orb
        output=project(r,formed,{'mercury','sun'},bound,y['grades'],'saturn',antar,evaluate)
        require(output['display']==expected[-1] and output['period_evidence']==(antar=='mercury'),'Y4 stored rules')
    print(f'KB-41: {len(yogas)} formations with chart misses, cancellation, softening, grade and period checks.')
