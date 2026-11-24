"""Internal worksheet consuming resolved D1/D9 facts; missing inputs withhold the grade."""
from functional import GRAHAS


def band(total, policy):
    for grade in ('Strong','Moderate'):
        if total >= policy['bands'][grade]:
            return grade
    return 'Weak'


def worksheet(x, p, cancellation, full_aspects, natural):
    graha = x.get('graha')
    flags = ('lagna_withheld','combust','war_loser','retrograde','vargottama')
    flags = tuple(k for k in flags if not (k=="war_loser" and graha in ("sun","moon","rahu","ketu") or k=="combust" and graha in ("rahu","ketu")))
    if graha not in GRAHAS or any(type(x.get(key)) is not bool for key in flags):
        return None
    h = x.get('house_moon' if x['lagna_withheld'] else 'house_lagna')
    if type(h) is not int or not 1 <= h <= 12:
        return None
    node = graha in ('rahu','ketu')
    dignity = [p['node_dignity'] if node else p['dignity'].get(x.get(key)) for key in ('d1','d9')]
    if None in dignity:
        return None
    if not node and x['d1']=='debilitation-sign':
        facts = x.get('relief_facts', {})
        matches = [facts.get(test['fact']) for test in cancellation['conditions']['any']]
        if any(value is not None and type(value) is not bool for value in matches):
            return None
        # Predicates may attest the same actual lord/angular contact.
        identities = x.get('relief_identity', {})
        angular={'d1.dignity.debility_lord_angular','d1.dignity.exaltation_lord_angular','d1.dignity.exaltee_angular'}
        matched_angular={k for k in angular if facts.get(k) is True}
        if len(matched_angular)>1 and not matched_angular.issubset(identities):
            return None
        lo = len({identities.get(t['fact'],t['fact']) for t, matched in
                  zip(cancellation['conditions']['any'],matches) if matched})
        hi = lo + matches.count(None)
        awards = p['cancellation_awards']
        if awards[min(2,lo)] != awards[min(2,hi)]:
            return None
        dignity[0] = awards[min(2,lo)]
    ht = p['house_terms']
    house = ht['other']
    if h in (1,4,5,7,9,10):
        house = ht['angle_or_trine']
    elif graha in natural['always_malefic'] and h in (3,6,11):
        house = ht['malefic_upachaya']
    elif h in (6,8,12):
        house = ht['difficult']
    aspects = x.get('aspects')
    if not isinstance(aspects,dict):
        return None
    net = 0
    for caster, aspect in aspects.items():
        if caster == graha or caster not in full_aspects or not isinstance(aspect,(list,tuple)) or len(aspect)!=2:
            return None
        distance, nature = aspect
        if distance not in full_aspects[caster] or nature not in ('benefic','malefic'):
            return None
        if (caster in natural['always_benefic'] and nature!='benefic' or
                caster in natural['always_malefic'] and nature!='malefic'):
            return None
        net += p['aspect_unit'] if nature=='benefic' else -p['aspect_unit']
    kind = x.get('natural_nature')
    if graha in natural['always_benefic']:
        kind = 'benefic'
    if graha in natural['always_malefic']:
        kind = 'malefic'
    if x['retrograde'] and kind not in ('benefic','malefic'):
        return None
    cap = p['aspect_net_cap']
    terms = dict(d1=dignity[0], house=house, aspects=max(-cap,min(cap,net)),
                 combust=p['combust'].get(graha,p['combust']['other']) if not node and x['combust'] else 0,
                 war=p['war_loser'] if not node and graha not in ('sun','moon') and x['war_loser'] else 0,
                 retrograde=p['retrograde_benefic'] if x['retrograde'] and kind=='benefic' else 0,
                 d9=dignity[1]*p['d9_factor'], vargottama=p['vargottama'] if x['vargottama'] else 0)
    if graha == 'moon':
        phase = x.get('paksha')
        if phase not in p['moon_paksha']:
            return None
        terms['paksha'] = p['moon_paksha'][phase]
    total = sum(terms.values())
    return dict(terms=terms,total=total,grade=band(total,p))


def validate(read,require):
    p = read('vedic/strength/grade.yaml')
    cancellation = read('vedic/yogas/neecha-bhanga.yaml')
    aspects = read('vedic/aspects/full-graha.yaml')['inclusive_distances']
    natural = read('vedic/planets/benefic-profile.yaml')
    cases = read('examples/planet-strength-grade.yaml')['cases']
    def run(x):
        return worksheet(x,p,cancellation,aspects,natural)
    raja = read('vedic/yogas/neecha-bhanga-raja.yaml')
    require(raja['conditions']['all'][0] == cancellation['conditions'],
            'Raja relief branches must match the canonical rule')
    for name,x in cases.items():
        x['relief_facts'] = {leaf['fact']:leaf['fact'] in x.get('matched_relief',[])
                             for leaf in cancellation['conditions']['any']}
        row=run(x)
        require([row['total'],row['grade']]==x['expected'],name)
    require([band(v,p) for v in (.999,1,1.001,2.999,3,3.001)]==
            ['Weak','Moderate','Moderate','Moderate','Strong','Strong'],'grade boundaries')
    x=cases['P1']
    require(run(dict(x,lagna_withheld=True)) is None and
            run(dict(x,lagna_withheld=True,house_moon=6))['terms']['house']==1,'Moon reference and upachaya')
    require(run(dict(x,aspects=None)) is None and run(dict(x,aspects={'rahu':[5,'malefic']})) is None,
            'absent aspect data and node aspect convention')
    require(run(dict(x,aspects={'mars':[4,'malefic'],'rahu':[7,'malefic'],'sun':[7,'malefic']}))['terms']['aspects']==-1,
            'aspect cap')
    require(run(dict(x,graha='ketu',d1=None,d9=None))['terms']['d1']==0,'node dignity')
    require(run(dict(cases['P2'],retrograde=True,natural_nature='benefic',war_loser=True))['total']==-1,
            'conditional Mercury retrograde and war')
    relief=dict(cases['P3']['relief_facts'])
    relief['d1.dignity.exchange_with_dispositor']=True
    require(run(dict(cases['P3'],relief_facts=relief))['terms']['d1']==1 and
            run(dict(cases['P3'],relief_facts={})) is None,'multiple and unknown cancellation')
    require(run(dict(x,aspects={'venus':[7,'benefic'],'jupiter':[9,'benefic'],'moon':[7,'benefic']}))['terms']['aspects']==1,
            'benefic aspect cap')
    for graha in GRAHAS:
        require(run(dict(x,graha=graha,aspects={},retrograde=False,paksha='waxing')) is not None,graha+' eligible')
    require(run(dict(x,shadbala=0)) == run(dict(x,shadbala=100)), 'Shadbala independence')
    require(read('vedic/strength/user-words.yaml')['planet_grade']==
            {'Strong':'supported','Moderate':'steady','Weak':'modest'}, 'planet words')
    same = {key:'shared-angular-lord' for key,value in relief.items() if value}
    require(run(dict(cases['P3'], relief_facts=relief, relief_identity=same))['terms']['d1']==0,'overlapping relief')
    require(run(dict(x,graha='rahu',combust=True,war_loser=True,aspects={}))['terms']['war']==0,'node penalties')
    require(run(dict(cases['P3'],paksha='waning',war_loser=True))['total']==0.5,'waning and luminary war')
    print('Planet strength: P1 3 Strong, P2 -0.5 Weak, P3 1 Moderate; edges and unknowns passed.')
