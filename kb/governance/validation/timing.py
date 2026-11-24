"""Bind a KB-38 area recipe, then delegate natal promise and timing to KB-36."""
from synthesis import evaluate as synthesize, bind_reference, D9_LABELS, GOOD_D9
from functional import OWNERS, SIGNS, resolve as functional_polarity
from check import evaluate, check_predicate


def pair_facts(maha, antar, signs, lagna, read):
    if not maha or not antar or maha not in signs or antar not in signs:
        return {}
    distance=(signs[antar]-signs[maha])%12+1
    result={'dasha.pair.distance':distance}
    if lagna is not None:
        offices = {g:{(i-lagna)%12+1 for i,owner in enumerate(OWNERS) if owner==g} for g in (maha,antar)}
        result['dasha.pair.angle_trine_lords'] = bool(
            offices[maha]&{4,7,10} and offices[antar]&{5,9} or offices[antar]&{4,7,10} and offices[maha]&{5,9})
        result['dasha.pair.shared_ownership']=maha==antar and maha in OWNERS
    friends=read(f'vedic/planets/{antar}.yaml')['graha']['natural_friendships']
    if maha!=antar and antar in OWNERS and maha in OWNERS:
        natural=next((n for group,n in [('friends','friend'),('neutral','neutral'),('enemies','enemy')]
                      if maha in friends[group]),None)
        if natural:
            table=read('vedic/dignity/relationships.yaml')
            temporary='friend' if distance in table['temporary_friends'] else 'enemy'
            result.update({'dasha.pair.natural':natural,'dasha.pair.compound':table['matrix'][natural][temporary]})
    return result


def modulation(lord, pair, read):
    policy=read('vedic/dashas/vimshottari/modulation.yaml')
    facts={**pair,**{'dasha.modulation.'+k:v for k,v in lord.items()}}
    house=lord.get('occupied_house')
    if house is not None and (house not in (6,8,12) or lord.get('viparita') is not None):
        facts['dasha.modulation.unrelieved_dusthana']=house in (6,8,12) and not lord['viparita'] if house in (6,8,12) else False
    notes={}
    for group in ('lord','pair'):
        rows=policy[group+'_notes']
        notes[group]=[r for r in rows if evaluate(r['when'],facts) is True]
        for effect in ('stronger','weaker'):
            hits=[evaluate(r['when'],facts) for r in rows if r['effect']==effect]
            facts[f'dasha.{group}.has_{effect}_note']=True if True in hits else None if None in hits else False
    return notes,facts


def bind(area,chart,period,recipe,read):
    from copy import deepcopy
    bound=deepcopy(chart['window_inputs'])
    aspects=read('vedic/aspects/full-graha.yaml')['inclusive_distances']
    functional=read('vedic/lordships/functional.yaml')['cells']
    lagna=chart.get('lagna')
    houses=recipe['houses']
    signs,grades=chart['signs'],chart['grades']
    bound.update(area=area,sensitive=recipe.get('sensitive',False),
                 karakas=[grades.get(g) for g in recipe['karakas']],period=dict(period))
    divisions={v['division'] for v in recipe['vargas'] if v['release']=='mvp'}
    bound['topic_varga']='D10' if 'D10' in divisions else None
    for key,origin in [('lagna',lagna),('moon',signs.get('moon'))]:
        bound[key]=bind_reference(origin,houses[0],dict(chart,lagna=SIGNS[lagna] if lagna is not None else None),functional,aspects)
        bound[key+'_targets']=[] if origin is None else [(origin+houses[0]-1)%12,signs.get(OWNERS[(origin+houses[0]-1)%12])]
    # Production testimony is the KB-41 projection. The legacy KB-36 fixtures may
    # still supply an already-bound witness. A hidden/private witness cannot vote.
    if 'yoga_record' in chart:
        proof=chart['yoga_record']
        prefix='vedic.yoga.'+proof['slug']+'.'
        bound['yoga']=dict(active=proof.get(prefix+'active') if proof.get('period_evidence') else False,
                           gate=proof.get(prefix+'gate'), softened=proof.get('display')=='yoga-mild',
                           cancelled=proof.get('display')=='omitted')
    if lagna is None:return bound
    def lord(h):return OWNERS[(lagna+h-1)%12]
    def at(h):return {g for g,s in signs.items() if s==(lagna+h-1)%12}
    sig=recipe['significators']
    targets=set(bound['lagna_targets'])-{None}
    extra=set(sig['grahas'])|set(sig.get('lower_weight',{}))
    if sig.get('yogakaraka'):
        extra.update(g for g,r in functional[SIGNS[lagna]].items() if r['yogakaraka'])
    if sig.get('yoga_participants'):
        extra.update(chart.get('eligible_yoga_grahas',{}).get(sig['yoga_participants'],[]))
    bound['period'].update(owners={lord(h) for h in [houses[0],*sig['house_lords'],*sig.get('secondary_lords',[])]},
        occupants=set.union(at(houses[0]),*(at(h) for h in sig.get('occupant_houses',[]))),
        aspectors={g for g,s in signs.items() if any((t-s)%12+1 in aspects[g] for t in targets)},
        karakas=set(recipe['karakas'])|extra,
        negating={g for h in recipe['delay_houses'] for g in at(h)|{lord(h)}})
    return bound


def transit_context(area,chart,segment,aspects):
    """The area's specific check supplements, and cannot create, a KB-36 window."""
    lagna=chart.get('lagna')
    if lagna is None:return None
    natal=chart['signs']
    signs=segment['signs']
    def reaches(g,targets):
        start=signs.get(g)
        if start is None:return None
        return any(t is not None and (t-start)%12+1 in (1,*aspects[g]) for t in targets)
    def targets(h):
        target=(lagna+h-1)%12
        return [target,natal.get(OWNERS[target])]
    if area in ('career','love-marriage','property-vehicles','business','family-home'):
        return True  # The primary house/lord is already the required double-transit target.
    if area=='health':return reaches('saturn',[lagna,natal.get('moon')])
    if area=='travel-relocation':
        votes=[reaches(g,targets(12)[:1]) for g in ('saturn','rahu')]
        return True if True in votes else None if None in votes else False
    if area=='money':
        # SAV qualifies pace independently of Jupiter's actual contact.
        return reaches('jupiter',targets(2)+targets(11))
    lookup={'learning':(4,5,9),'children':(5,), 'spirituality':(9,)}
    return reaches('jupiter',[t for h in lookup[area] for t in targets(h)])


def period_notes(chart, area, period, read):
    recipe=read('life-areas/recipes.yaml')['recipes'][area]
    bound=bind(area,chart,period,recipe,read)
    sig=bound['period']
    direct=set().union(*(sig.get(k,[]) for k in ('owners','occupants','aspectors','karakas')))
    pair=pair_facts(period.get('maha'),period.get('antar'),chart['signs'],chart.get('lagna'),read)
    table=read('vedic/lordships/functional.yaml')['cells']
    results={}
    for level in ('maha','antar'):
        g=period.get(level)
        if not g:continue
        sign=chart['signs'].get(g)
        lagna=chart.get('lagna')
        moon=chart['signs'].get('moon')
        testimony=dict(chart.get('lord_details',{}).get(g,{}))
        testimony['grade']=chart['grades'].get(g)
        if sign is not None:
            if lagna is not None:
                testimony['occupied_house']=(sign-lagna)%12+1
                testimony['polarity']=functional_polarity(table,SIGNS[lagna],g,SIGNS[sign],
                                                        **chart.get('node_nature',{}).get(g,{}))
            if moon is not None:
                testimony['moon_house']=(sign-moon)%12+1
                testimony['moon_support']=testimony['moon_house'] in recipe['houses']
        star=period.get('star_lords',{}).get(g)
        if star is not None:testimony['star_signifies']=star in direct
        notes,facts=modulation(testimony,pair,read)
        distance=pair.get('dasha.pair.distance')
        phrase=None if distance is None or level=='maha' else ('pair-harder' if distance in (6,8) else 'pair-adjust' if distance in (2,12) else 'pair-easier')
        results[level]={'notes':notes,'facts':facts,'copy_key':phrase}
    return results


def upcoming(area, chart, periods, read):
    recipe=read('life-areas/recipes.yaml')['recipes'][area]
    policy=read('life-areas/pipeline.yaml')
    args=(policy,read('life-areas/conflict-ladder.yaml'),read('shared/confidence/output-matrix.yaml')['rows'],
          read('vedic/aspects/full-graha.yaml')['inclusive_distances'])
    windows=[]
    states=[]
    for p in periods:
        x=bind(area,chart,p,recipe,read)
        segments=x['segments']
        for segment in segments or [None]:
            if segment and transit_context(area,chart,segment,args[-1]) is not True:
                x['segments']=[]
            else:
                x['segments']=[segment] if segment else []
            result=synthesize(x,*args)
            states.append(result['state'])
            for w in result['windows']:
                tone=result['card']
                if area=='love-marriage' and tone=='Supportive' and (
                    'promise-varga-lagna' in x['unstable'] or not (x['vargottama'] or D9_LABELS.get(x['d9'],x['d9']) in GOOD_D9)):
                    tone='Steady'
                if area=='health' and tone=='Take care' and len(set(x.get('independent_cautions',[])))<2:
                    tone='Steady'
                rank=int(p.get('antar') in recipe['significators'].get('lower_weight',{}) and
                         p.get('antar') not in set(x['period'].get('owners',[]))|set(recipe['karakas']))
                pace=w['pace']
                if area=='money' and pace=='supported':
                    gains=chart.get('gains_sign_sav')
                    pace='unknown' if gains is None else 'slower' if gains<policy['transit']['pace']['minimum_sav_each'] else pace
                windows.append(dict(priority=rank,start=w['start'],end=w['end'],tone=tone,pace=pace))
    windows.sort(key=lambda w:(w['start'],w['pace']!='supported',w['priority'],w['end']))
    if windows:
        rest=sorted(windows[1:],key=lambda w:(w['pace']!='supported',w['start'],w['priority']))[:2]
        windows=[windows[0],*sorted(rest,key=lambda w:w['start'])]
    for window in windows: del window['priority']
    return states,windows


def validate_timing(rules,read,require):
    from synthesis import merge
    doc=read('examples/area-timing.yaml')
    base=doc['base']
    for label,case in doc['cases'].items():
        chart=merge(base,case.get('chart',{}))
        p=merge(doc['period'],case.get('period',{}))
        states,wins=upcoming(case.get('area','love-marriage'),chart,[p],read)
        if 'state' in case:require(case['state'] in states,(label,states))
        if 'window' in case:require((wins[0] if wins else None)==case['window'],(label,wins))
        if 'topic_varga' in case:
            recipe=read('life-areas/recipes.yaml')['recipes'][case['area']]
            require(bind(case['area'],chart,p,recipe,read)['topic_varga']==case['topic_varga'],label+' release gate')
        resolution=pair_facts(p['maha'],p['antar'],chart['signs'],chart['lagna'],read)
        notes,facts=modulation(case.get('lord',{}),resolution,read)
        for key,v in case.get('facts',{}).items():require(facts.get(key)==v,(label,key))
    notes=period_notes(base,'love-marriage',doc['period'],read)
    require(notes['antar']['facts']['dasha.modulation.star_signifies'] and
            notes['maha']['facts']['dasha.modulation.grade']=='Strong' and
            notes['antar']['facts']['dasha.pair.distance']==6,'T2 bound star, grade and harder pair')
    for r in rules.values():
        if r['topic']=='dashas/vimshottari' and r['id'].split('.')[-1].startswith(('pratyantar-','sookshma-')):
            level,lord=r['id'].split('.')[-1].split('-')
            evidence={'dasha.vimshottari.selected_level':level,'dasha.vimshottari.'+level+'_lord':lord}
            require(evaluate(r['conditions'],dict(evidence,**{'confidence.tier':'A'})) is True and
                    evaluate(r['conditions'],dict(evidence,**{'confidence.tier':'B'})) is False and
                    evaluate(r['conditions'],evidence) is None,r['id']+' fine precision')
    require(notes['antar']['copy_key']=='pair-harder','T2 public relationship qualification')
    registry=read('life-areas/recipes.yaml')['recipes']
    health=merge(base,{'window_inputs':{'qualified_challenge':True,'remaining_primary':['support','caution'],
                    'segments':[{'interval':['2032-03-10','2032-04-12'],'signs':{'jupiter':0,'saturn':0},
                                 'av':[[28,4],[28,4]]}]}})
    hp=dict(doc['period'],antar='mars')
    for factors,expected in [(['single-transit'],'Steady'),(['primary-transit','independent-period'],'Take care')]:
        health['window_inputs']['independent_cautions']=factors
        health['window_inputs']['tier']='B'
        _,items=upcoming('health',health,[hp],read)
        require(items and items[0]['tone']==expected,'health caution qualification')
    for area,r in registry.items():
        editorial=area in ('business','family-home','spirituality')
        require(('awaiting Vedic review' in r['tag'])==editorial,area+' recipe provenance')
    require(len(registry)==11 and registry['travel-relocation']['houses']==[3,9,12] and
            registry['children']['houses']==[5,9] and registry['money']['karakas']==['jupiter','venus'],
            'reviewed area corrections')
    policy=read('vedic/dashas/vimshottari/modulation.yaml')
    catalog=read('shared/fact-dictionary/catalog.yaml')['facts']
    for note in policy['lord_notes']+policy['pair_notes']:check_predicate(note['when'],catalog)
    for r in rules.values():
        if r['topic']=='dashas/vimshottari' and r['id'].endswith(('-maha','-antar')):
            require(r['modulation_ref'].endswith('modulation.yaml') and r['strength_notes'],r['id'])
    print(f'KB-38: eleven recipes and {len(doc["cases"])} area timing scenarios passed.')
