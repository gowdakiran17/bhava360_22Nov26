"""Whole-sign reference evaluator for the additional draft formations. Aries is sign zero."""
from functional import OWNERS
from yoga_charts import GRAHAS, ANGLES, distance

TRINES = {1,5,9}


def participants(slug, spec, chart):
    """Return bound grahas, an empty set for a miss, or None for missing evidence."""
    signs=chart.get('signs',{})
    lagna=chart.get('lagna')
    if slug=='guru-mangala':
        if signs.get('mars') is None or signs.get('jupiter') is None:return None
        return {'mars','jupiter'} if distance(signs['mars'],signs['jupiter']) in (1,7) else set()
    if lagna is None and (spec['method'] in ('modality','distinct-count') or slug=='pravrajya' or
                          spec.get('reference')=='moon'):
        # These predicates use only signs, counts or distances from the Moon.
        lagna=0
    if lagna is None or any(signs.get(g) is None for g in GRAHAS):
        return None
    houses={g:distance(signs[g],lagna) for g in GRAHAS}
    occupied=set(houses.values())
    seven=set(GRAHAS)
    nature_required=spec['method'] in ('quadrant-nature','paired-nature','flanks') or slug in ('parvata','chamara','lagnadhi','kusuma')
    if nature_required and chart.get('benefics') is None:
        return None
    if slug in ('kahala','shankha','bheri'):
        relevant_lord=OWNERS[(lagna+(8 if slug=='bheri' else 0))%12]
        if chart.get('grades',{}).get(relevant_lord) not in ('Strong','Moderate','Weak'):
            return None
    benefics=set(chart.get('benefics',[]))
    malefics=seven-benefics
    def lord(h): return OWNERS[(lagna+h-1)%12]
    def relative(a,b): return distance(signs[a],signs[b])
    def angle(a,b): return relative(a,b) in ANGLES
    def aspect(a,b): return relative(b,a) in chart['full_aspects'][a]
    def exalted(g): return signs[g]==chart['exaltation'][g]
    def strong(g): return chart['grades'][g] in ('Strong','Moderate')
    def owners(*nums): return {lord(h) for h in nums}
    def matched(test, group): return set(group) if test else set()
    def at(h): return {g for g in seven if houses[g]==h}
    mode=spec['method']
    if mode=='modality':
        return matched(all(signs[g]%3==spec['index'] for g in seven),seven)
    if mode=='occupied-pattern':
        return matched(any(occupied==set(p) for p in spec['patterns']),seven)
    if mode=='distinct-count':
        return matched(len(occupied)==spec['count'],seven)
    if mode=='quadrant-nature':
        wanted=benefics if spec['nature']=='benefic' else malefics
        only={h for h in ANGLES if at(h) and at(h)<=wanted}
        return matched(len(only)>=3,set().union(*(at(h) for h in only)))
    if mode=='paired-nature':
        a,b=(benefics,malefics) if slug.endswith('vajra') else (malefics,benefics)
        return matched(all(at(h) and at(h)<=pool for h,pool in [(1,a),(7,a),(4,b),(10,b)]) and occupied<=ANGLES,seven)
    if mode=='flanks':
        ref=lagna if spec['reference']=='lagna' else signs['moon']
        pool=benefics if spec['nature']=='benefic' else malefics
        sides=[{g for g in seven if distance(signs[g],ref)==h} for h in (2,12)]
        return matched(all(side and side<=pool for side in sides),set.union(*sides))
    if slug=='dharma-karmadhipati':
        a,b=lord(9),lord(10)
        return matched(a!=b and (signs[a]==signs[b] or (houses[a],houses[b])==(10,9) or aspect(a,b) and aspect(b,a)),{a,b})
    if slug=='parvata':
        angular={g for g in seven if houses[g] in ANGLES}
        return matched(bool(angular) and angular<=benefics and not (at(7)|at(8))&malefics,angular)
    if slug=='kahala':
        return matched(angle(lord(4),'jupiter') and strong(lord(1)),owners(1,4)|{'jupiter'})
    if slug=='chamara':
        a=lord(1)
        if exalted(a) and houses[a] in ANGLES and aspect('jupiter',a): return {a,'jupiter'}
        return next((at(h)&benefics for h in (7,9,10) if len(at(h)&benefics)>=2),set())
    if slug=='shankha':
        return matched(strong(lord(1)) and angle(lord(5),lord(6)),owners(1,5,6))
    if slug=='bheri':
        if not strong(lord(9)):return set()
        if {1,2,7,12}<=occupied:return owners(9)|set().union(*(at(h) for h in (1,2,7,12)))
        group={'jupiter','venus',lord(1)}
        return matched(all(angle(a,b) for a in group for b in group),group|owners(9))
    if slug=='lagnadhi':
        return matched(all(houses[g] in (6,7,8) for g in ('mercury','jupiter','venus')) and not at(4)&malefics,{'mercury','jupiter','venus'})
    if slug=='kalanidhi':
        return matched(houses['jupiter'] in (2,5) and all(signs[g]==signs['jupiter'] or aspect(g,'jupiter') for g in ('mercury','venus')),{'jupiter','mercury','venus'})
    if slug=='sreenatha':
        return matched(houses[lord(7)]==10 and exalted(lord(7)) and signs[lord(9)]==signs[lord(10)],owners(7,9,10))
    if slug=='mahabhagya':
        branch=chart.get('opt_in_branch')
        if branch not in ('male-day','female-night') or chart.get('day_birth') is None:return None
        odd=branch=='male-day'
        return matched(chart['day_birth']==odd and all((s%2==0)==odd for s in (lagna,signs['sun'],signs['moon'])),{'sun','moon'})
    if slug=='kusuma':
        companions=at(houses['moon'])&benefics-{'moon'}
        return matched(lagna%3==1 and houses['venus'] in ANGLES and houses['moon'] in TRINES and companions and houses['saturn']==10,companions|{'venus','moon','saturn'})
    if slug=='parijata':
        a=lord(1); b=OWNERS[signs[a]]
        if chart.get('d9',{}).get(b) is None:return None
        group={a,b,OWNERS[signs[b]],OWNERS[chart['d9'][b]]}
        return matched(all(houses[g] in ANGLES|TRINES or exalted(g) for g in group),group)
    if slug=='pravrajya':
        return next((at(h) for h in occupied if len(at(h))>=4),set())
    raise ValueError(slug)
