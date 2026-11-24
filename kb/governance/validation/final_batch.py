"""Worked, synthetic checks for the final KB release profiles."""
from collections import Counter
from fractions import Fraction

from other_dashas import drishti, sign_path
from public_copy import check_text


def conditional_gate(gate, chart):
    try:
        if gate in ('hora-matches-paksha','hora-matches-sect'):
            condition = chart['waxing' if gate=='hora-matches-paksha' else 'day']
            return None if condition is None or chart['hora'] not in ('sun','moon') else (chart['hora']=='sun')==condition
        if gate=='venus-d9-lagna':
            return chart['navamsha_lagna'] in (1,6) if chart['navamsha_lagna'] is not None else None
        if gate=='cancer-d12-lagna':
            return chart['d12_lagna']==3 if chart['d12_lagna'] is not None else None
        asc=chart['lagna']
        if asc is None:
            return None
        if gate=='vargottama-lagna':
            return None if chart['navamsha_lagna'] is None else asc==chart['navamsha_lagna']
        if gate=='sun-in-lagna':
            return None if chart['sun'] is None else asc==chart['sun']
        rulers='mars venus mercury moon sun mercury venus mars jupiter saturn saturn jupiter'.split()
        if gate=='tenth-lord-in-tenth':
            target=(asc+9)%12
            position=chart.get(rulers[target])
            return None if position is None else position==target
        if gate=='lagna-seventh-exchange-or-placement':
            opposite=(asc+6)%12
            values=[(chart.get(rulers[asc]),opposite),(chart.get(rulers[opposite]),asc)]
            return True if any(actual==target for actual,target in values) else None if any(
                actual is None for actual,_ in values) else False
    except KeyError:
        return None
    raise ValueError('Unknown conditional clock gate')


def candidate_minutes(start, end, step):
    if start is None or end is None:
        return []
    if end < start or step not in (1, 2):
        raise ValueError('Invalid rectification interval')
    times = list(range(start, end + 1, step))
    if times[-1] != end:
        times.append(end)
    return times


def same_graha_at_anchors(sign, anchors):
    if sign is None or len(anchors) != 3 or None in anchors:
        return None
    return all(drishti(sign, anchor) for anchor in anchors)


def annual_houses(table, age):
    if type(age) is not int or age not in table['ages']:
        return None
    row = table['edition_rows'].get(age)
    if not row or row.get('verification') != 'verified':
        return None
    houses = row['houses']
    if not row.get('locator') or sorted(houses) != list(range(1, 13)):
        raise ValueError('Verified annual row requires a locator and twelve unique houses')
    return houses


def rectification(candidates, consent, policy):
    """An event has one identity even when several timing witnesses support it."""
    if not consent:
        return None
    ranked=[]
    for time, events in candidates.items():
        antar={e['id'] for e in events if e['antar']}
        pratyantar={e['id'] for e in events if e['antar'] and e['pratyantar']}
        if len(antar)<policy['independent_antar'] or len(pratyantar)<policy['independent_pratyantar']:
            continue
        rank=(len(antar),len(pratyantar),sum(any(e.get('transit') for e in events if e['id']==i) for i in antar),
              sum(any(e.get('certain') for e in events if e['id']==i) for i in antar))
        ranked.append((rank,time))
    if not ranked:
        return None
    top=max(rank for rank,_ in ranked)
    times=sorted(time for rank,time in ranked if rank==top)
    return {'times':times,'rectified':len(times)==1,'eligible':policy['scope'] if len(times)==1 else []}


def tarot_summary(cards, spread, policy):
    if not cards or len(cards)!=len(spread) or any(c is None for c in cards):
        return None
    def modes(values):
        counts=Counter(values)
        return sorted(k for k,v in counts.items() if v==max(counts.values()))
    suits=[c['card'].split('-of-')[-1] for c in cards if '-of-' in c['card']]
    ranks=Counter(c['card'].split('-of-')[0] for c in cards if '-of-' in c['card'])
    return dict(majors=len(cards)-len(suits),reversed=sum(c['orientation']=='reversed' for c in cards),
                dominant_suits=modes(suits),elements=modes(c['element'] for c in cards),
                repeated_pips=sorted(r for r,n in ranks.items() if n>1 and r not in ('page','knight','queen','king')),
                pairs=[policy['pairs'][key] for a,b in zip(cards,cards[1:])
                       if (key:=a['card']+'|'+b['card']) in policy['pairs']],priority=spread)


def papasamya(positions, reference, exempt=()):
    if reference is None or any(positions.get(g) is None for g in ('sun','mars','saturn','rahu','ketu')):
        return None
    return {g for g in ('sun','mars','saturn','rahu','ketu') if g not in exempt and
            (positions[g]-reference)%12+1 in (1,2,4,7,8,12)}


def validate(rules,read,require):
    yogas=read('vedic/dashas/chara/periods.yaml')
    j=read('examples/jaimini-j2.yaml')
    left=j['cycle_one']; right=j['cycle_two']
    require(sum(left)==j['switch_at_year']<70 and [12-y for y in left]==right,'J2 complements')
    cursor=0
    for years in (left,right):
        for sign,span in enumerate(years):
            if span:
                require(sign_path('chara',yogas,j['chart'],Fraction(cursor))[0]==(j['order'][sign],cursor,cursor+span),'J2 boundary')
            cursor+=span
    example = j['period_example']
    require(sign_path('chara', yogas, j['chart'], Fraction(example['elapsed_years']))[0][0] == example['sign']
            and j['user_text'] == rules[example['rule']]['user_text'], 'J2 period reading')
    require(same_graha_at_anchors(2, [2,5,8]) and not same_graha_at_anchors(2, [2,5,7])
            and same_graha_at_anchors(2, [2,None,8]) is None, 'one participant across stable anchors')
    require(candidate_minutes(-2, 3, 2) == [-2,0,2,3] and not candidate_minutes(None,3,1),
            'rectification grid covers both boundaries')
    annual = read('lal-kitab/varshphal/annual.yaml')
    require(annual['ages'] == list(range(1,121)) and annual_houses(annual,0) is None
            and annual_houses(annual,None) is None, 'annual lookup domain')
    for age in annual['ages']:
        annual_houses(annual,age)
    require(cursor==144,'two complete passes')
    require(yogas['antar_review']['visibility']=='admin-only','unverified Antar grouping')
    success={'hora-matches-paksha':{'waxing':True,'hora':'sun'},'hora-matches-sect':{'day':False,'hora':'moon'},
             'venus-d9-lagna':{'navamsha_lagna':6},'cancer-d12-lagna':{'d12_lagna':3},
             'tenth-lord-in-tenth':{'lagna':0,'saturn':9},'sun-in-lagna':{'lagna':0,'sun':0},
             'vargottama-lagna':{'lagna':4,'navamsha_lagna':4},
             'lagna-seventh-exchange-or-placement':{'lagna':0,'venus':0,'mars':2}}
    missed={'hora':'moon','day':True,'waxing':True,'navamsha_lagna':5,'d12_lagna':2,'lagna':0,'sun':1,'saturn':8,'venus':2,'mars':3}
    names='shodasottari dwadasottari panchottari sataatbika chathuraaseethi-sama dwisatpathi shastihayani shattrimsa-sama'.split()
    for name,total in zip(names,(116,112,105,100,84,72,60,36)):
        d=read('vedic/dashas/conditional/'+name+'.yaml');g=d['gate']
        require(conditional_gate(g,success[g]) is True and conditional_gate(g,missed) is False and
                conditional_gate(g,{}) is None,name+' three-valued gate')
        require(sum(d['years'])==total==d['cycle_years'] and len(set(d['order']))==len(d['years']) and d['clock']['days']>0,name)
    d8=read('examples/conditional-d8.yaml')
    require(conditional_gate('sun-in-lagna',d8['chart']) and not conditional_gate('venus-d9-lagna',d8['chart']),'D8')
    r=read('vedic/rectification/method.yaml')['accept']
    events=[dict(id=i,antar=True,pratyantar=i<2) for i in range(3)]
    require(rectification({0:events},True,r)['eligible']==['d9','d10'] and rectification({0:events},False,r) is None
            and rectification({0:events[:2]*2},True,r) is None and
            not rectification({0:events,2:events},True,r)['rectified'],'consent, independent events and tied candidate')
    policy=read('tarot/spreads/synthesis.yaml')
    cards=[rules['tarot.'+topic+'.'+slug]['card_profile'] for topic,slug in
           [('major-arcana','the-hermit-upright'),('minor-arcana','two-of-cups-reversed'),('major-arcana','the-star-upright')]]
    summary=tarot_summary(cards,policy['emphasis']['past-present-future'],policy)
    require((summary['majors'],summary['reversed'],summary['dominant_suits'])==(2,1,['cups']) and
            tarot_summary([],[],policy) is None,'synthetic draw and empty draw')
    lines=read('tarot/spreads/area-lines.yaml')['lines']
    require(set(lines)=={k for k,r in rules.items() if r['system']=='tarot'} and
            all(set(v)=={'career','relationship'} for v in lines.values()),'312 area readings')
    for rid,values in lines.items():
        for words in values.values():
            for lang in ('en','kn','hi'):check_text(words[lang],rid,lang)
    require(len(read('numerology/lo-shu/planes.yaml')['lines'])==8,'eight planes')
    pos=dict(sun=0,mars=1,saturn=7,rahu=4,ketu=10)
    require(papasamya(pos,0)=={'sun','mars','saturn'} and papasamya(pos,1)!=papasamya(pos,6) and
            papasamya(pos,None) is None,'independent matching references')
    for text in ('unlucky','incompatible','dying','urgent','must act now','tragedy','misfortune','inauspicious',
                 'अशुभ','ಅಶುಭ','दुर्घटना','ಮೃತ','मृत।','8/10','book a puja','buy a puja'):
        try: check_text(text,'planted','en')
        except ValueError: pass
        else: raise ValueError('copy gate missed '+text)
    print('Batch 7 passed: eight conditional gates, J2 two-cycle boundaries, D8, rectification, 312 area lines and public-copy probes.')
