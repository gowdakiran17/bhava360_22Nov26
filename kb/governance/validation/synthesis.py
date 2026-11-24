"""Executable specification for one area with bound chart and dated transit evidence."""
from calendar import monthrange
from datetime import date, timedelta

GRADES = ['Weak','Moderate','Strong']
GOOD = {'Benefic','Yogakaraka'}
D9_LABELS = {'exaltation-sign':'exalted','exaltation-peak':'exalted','own-sign':'own',
             'debilitation-sign':'debilitated','mitra':'friend','adhi-mitra':'great-friend',
             'shatru':'enemy','adhi-shatru':'great-enemy','sama':'neutral'}
GOOD_D9 = {'exalted','own','moolatrikona','friend','great-friend'}


def majority(values):
    if not values:
        return None
    yes = values.count(True)
    if yes*2 > len(values):
        return True
    if (yes+values.count(None))*2 <= len(values):
        return False
    return None


def bind_reference(origin, area_house, chart, table, aspects):
    """Collect full aspects and functional nature before testing any natal factor."""
    from functional import OWNERS, SIGNS, resolve
    if origin is None:
        return {}
    target=(origin + area_house - 1)%12
    lord=OWNERS[target]
    placements=chart['signs']
    grades=chart['grades']
    occupants=[]
    testimony=[]
    lord_sign=placements.get(lord)
    for graha,sign in placements.items():
        if sign is None:
            return {'lord':grades.get(lord)}
        nature=resolve(table, chart.get('lagna'), graha, SIGNS[sign],
                       **chart.get('node_nature',{}).get(graha,{}))
        if sign==target:
            occupants.append((nature,grades.get(graha)))
        for destination in {target,lord_sign} - {None}:
            if (destination-sign)%12+1 in aspects[graha]:
                testimony.append(nature)
    return dict(lord=grades.get(lord), occupants=occupants,
                aspects=testimony if lord_sign is not None else None)


def reference_tests(ref):
    lord=ref.get('lord')
    occupants=ref.get('occupants')
    aspects=ref.get('aspects')
    occupied=None
    if occupants and all(n and g for n,g in occupants):
        occupied=any(n in GOOD for n,g in occupants) and not any(n=='Malefic' and g=='Weak' for n,g in occupants)
    aspected=None
    if aspects is not None and all(aspects):
        aspected=sum(n in GOOD for n in aspects)>aspects.count('Malefic')
    return [lord in GRADES[1:] if lord else None, occupied, aspected]


def double(signs, targets, aspects):
    if not targets or None in targets or any(signs.get(g) is None for g in ('jupiter','saturn')):
        return None
    return all(any((t-signs[g])%12+1 in [1,*aspects[g]] for t in targets) for g in ('jupiter','saturn'))


def collect_windows(x, tier, aspects, policy, limits, significators, weights):
    start=date.fromisoformat(x['today'])
    year=start.year+policy['horizon_years']
    horizon=start.replace(year=year,day=min(start.day,monthrange(year,start.month)[1]))
    period=x['period']
    bounds=[period['interval']]
    if tier=='A' and period.get('subinterval'):
        bounds.append(period['subinterval'])
    windows=[]
    for segment in x['segments']:
        signs=segment['signs']
        moon=double(signs,x['moon_targets'],aspects)
        if double(signs,x['lagna_targets'],aspects) is not True:
            continue
        pairs=[*bounds,segment['interval']]
        a=max([start,*[date.fromisoformat(p[0]) for p in pairs]])
        b=min([horizon,*[date.fromisoformat(p[1]) for p in pairs]])
        if a>=b:
            continue
        av=segment['av']
        pace=('unknown' if any(v is None for pair in av for v in pair) else
              'supported' if all(sav>=limits['minimum_sav_each'] and bav>=limits['minimum_own_bav_each'] for sav,bav in av) else 'slower')
        peaks={}
        for at, bodies in segment.get('peaks',{}).items():
            dt=date.fromisoformat(at)
            if tier!='A' or not a<=dt<b: continue
            if any(bodies.get(g) in x['lagna_targets'] for g in ('mars','sun')):
                peaks.setdefault('months',set()).add(at[:7])
            if a-start<=timedelta(days=30) and bodies.get('moon') in x['lagna_targets']:
                peaks.setdefault('days',set()).add(at)
        weight=sum(weights[level] for level in ('maha','antar','pratyantar')
                   if period.get(level) in significators and (level!='pratyantar' or tier=='A'))
        # The optional internal ranking term is considered only after pace/date/relevance.
        tie=segment.get('bhava_rank',0) if x.get('flags',{}).get('bhava_bala_tiebreak') else 0
        windows.append(dict(order=(-weight,-tie),start=a.isoformat(),end=b.isoformat(),pace=pace,moon=moon,
                            peaks={k:sorted(v) for k,v in peaks.items()}))
    windows.sort(key=lambda w:(w['start'],w['pace']!='supported',w['order'],w['end']))
    if not windows: return []
    selected=[windows[0],*sorted(windows[1:],key=lambda w:(w['pace']!='supported',w['start'],w['order']))[:policy['later_limit']]]
    for w in selected:
        del w['order']
    return selected


def evaluate(x, policy, ladder, matrix, aspects):
    tier=x['tier']
    primary=reference_tests(x['lagna'])
    secondary=reference_tests(x['moon'])
    if matrix['promise-functional-lordship'][tier]=='hide':
        secondary[1:]=[None,None]
    d9=D9_LABELS.get(x.get('d9'),x.get('d9'))
    varga=None if d9 is None else x['vargottama'] or d9 in GOOD_D9
    if x.get('topic_varga') and varga:
        varga_lord=x.get('topic_lord',{})
        placement=varga_lord.get('house')
        dignity=varga_lord.get('dignity')
        if placement in (1,4,5,7,9,10) or D9_LABELS.get(dignity,dignity) in ('own','exalted'):
            varga=True
        else:
            varga=False if placement is not None and dignity is not None else None
    counts=[*primary,majority([g in GRADES[1:] if g else None for g in x['karakas']]),
            majority(secondary),varga]
    for i,(key,_) in enumerate(policy['promise']['factors']):
        if matrix[key][tier]=='hide' or key in x['unstable']:
            counts[i]=None
    # Some synthetic recipes have a factor whose only witness is a cancellable yoga.
    # Resolve that witness before the thresholds, never dropping unrelated chart facts.
    for index,(key,_) in enumerate(policy['promise']['factors']):
        if key in x.get('yoga_only_factors',[]) and (x['yoga'].get('cancelled') or x['yoga'].get('active') is not True):
            counts[index]=None
    count=counts.count(True)
    thresholds=policy['promise']['thresholds']
    grade=2 if count>=thresholds['Strong'] else int(count>=thresholds['Moderate'])
    result=dict(band=GRADES[grade],card=None,windows=[],remedy_graha=None)
    if not grade: return dict(result,state='no-promise')
    period=x['period']
    direct=set().union(*(period.get(group,[]) for group in ('owners','occupants','aspectors','karakas')))
    sig=direct|{g for g,star in period['star_lords'].items() if star in direct}
    antar=period.get('antar')
    if not antar: return dict(result,state='unknown-period')
    if antar not in sig:
        state=('delay' if antar in period['negating'] else
               'background' if period.get('maha') in sig else 'not-now')
        return dict(result,state=state)
    if matrix['event-window'][tier]=='hide' or 'event-window' in x['unstable']:
        return dict(result,state='withheld')
    wins=collect_windows(x,tier,aspects,policy['window'],policy['transit']['pace'],sig,policy['period']['ordering'])
    if not wins: return dict(result,state='no-window')
    # A cancellation removes the evidence before either the factors or ladder consume it.
    yoga=x['yoga']
    yoga_display='background'
    if yoga.get('cancelled'): yoga_display='omitted'
    elif yoga.get('active') is True and 'gate' in yoga:
        yoga_display={'full':'mild' if yoga.get('softened') else 'active','mild':'mild','hidden':'omitted'}.get(yoga['gate'],'unknown')
    elif yoga.get('active') is True:
        participants=yoga['participants']
        yoga_display=('unknown' if not participants or None in participants else
                      'omitted' if all(g=='Weak' for g in participants) else
                      'mild' if 'Weak' in participants else 'active')
    lord=x['lagna']['lord']
    if lord=='Strong' and d9 in ('debilitated','enemy','great-enemy') and not x['vargottama']:
        grade=max(0,grade-1)
    elif lord=='Weak' and (d9 in ('own','exalted') or x['vargottama']):
        grade=max(grade,min(grade+1,1))
    directions=x.get('directions',{'lagna':'support','moon':'support'})
    if wins[0]['moon'] is True and directions.get('lagna') in ('support','caution') and directions['lagna']==directions.get('moon'):
        grade=min(2,grade+1)
    votes=sum(v for k,v in x.get('systems',{}).items() if k in ('kp','jaimini') and
              x.get('flags',ladder['flags']).get(k) and v in (-1,1))
    grade=max(0,min(2,grade+(votes>0)-(votes<0)))
    if {'support','caution'}<=set(x.get('remaining_primary',[])):
        grade=1
    if matrix['final-card-grade'][tier]=='cap-moderate': grade=min(1,grade)
    card=('Supportive' if grade==2 else 'Take care' if x.get('qualified_challenge') else 'Steady') if grade else None
    if not card: return dict(result,state='no-card',yoga=yoga_display)
    remedy_graha=None if card=='Supportive' or x.get('sensitive') or x['area'] in ('health','bereavement','financial-verdict','legal') else x.get('caution_lord') or antar
    for w in wins:
        if tier=='B':
            w['start']=w['start'][:7]
            w['end']=(date.fromisoformat(w['end'])-timedelta(days=1)).isoformat()[:7]
    chips=['career-chip'] if x['area']=='career' else []
    chips.extend(['season-chip','timing-chip'])
    return dict(result,state='active',chips=chips,card=card,grade=GRADES[grade],windows=wins,yoga=yoga_display,
                remedy_graha=remedy_graha,pace=wins[0]['pace'],phase_end=wins[0]['end'],action='action')


def forecast(chart, periods, policy, ladder, matrix, aspects):
    """Consider each solved period before ordering the event cards over the shared horizon."""
    candidates=[]
    for period in periods:
        record=evaluate(dict(chart,period=period),policy,ladder,matrix,aspects)
        if record.get('card'):
            candidates.extend(record['windows'])
    candidates.sort(key=lambda w:(w['start'],w['pace']!='supported',w['end']))
    if not candidates:
        return []
    return [candidates[0],*sorted(candidates[1:],key=lambda w:(w['pace']!='supported',w['start']))[:policy['window']['later_limit']]]


def screen_practice(cards):
    # Caller supplies display order; choose once after actions and phase bounds are present.
    for card in cards:
        if card.get('card') in ('Steady','Take care') and card.get('action') and card.get('phase_end') and card.get('remedy_graha'):
            return card['remedy_graha']
    return None


def merge(base, patch):
    return {**base, **{k:merge(base[k],v) if isinstance(v,dict) and isinstance(base.get(k),dict) else v
                      for k,v in patch.items()}}


def validate(read,require):
    p=read('life-areas/pipeline.yaml')
    ladder=read('life-areas/conflict-ladder.yaml')
    matrix=read('shared/confidence/output-matrix.yaml')['rows']
    aspects=read('vedic/aspects/full-graha.yaml')['inclusive_distances']
    fixtures=read('examples/synthesis-windows.yaml')
    for name,case in fixtures['cases'].items():
        x=merge(fixtures['base'],case.get('input',{}))
        r=evaluate(x,p,ladder,matrix,aspects)
        require(all(r.get(k)==v for k,v in case['expect'].items()),(name,r,case['expect']))
        if 'first' in case:
            require(r['windows'][0]==case['first'],name+' bounds/peaks')
        if 'chips' in case:
            require(r['chips']==case['chips'],name+' public reasons')
    funcs=read('vedic/lordships/functional.yaml')['cells']
    chart=dict(lagna='aries', signs={'jupiter':0,'rahu':8,'mercury':6,'mars':0},
               grades={'mars':'Strong','jupiter':'Moderate','rahu':'Weak','mercury':'Strong'})
    bound=bind_reference(0,1,chart,funcs,aspects)
    require(bound['aspects']==['Malefic'] and bound['lord']=='Strong' and
            reference_tests(bound)==[True,True,False],'functional testimony and seventh-only nodes')
    require(bind_reference(None,1,chart,funcs,aspects)=={},'missing reference')
    base=fixtures['base']
    sample=base['segments'][0]
    ranges=[('2032-03-10','2032-03-11',26),('2032-03-12','2032-03-13',26),
            ('2032-03-14','2032-03-15',28),('2032-03-16','2032-03-17',28),('2032-03-18','2032-03-19',26)]
    segments=[dict(sample,interval=[a,b],av=[[28,4],[v,4]]) for a,b,v in ranges]
    result=evaluate(dict(base,segments=segments),p,ladder,matrix,aspects)
    require([w['start'] for w in result['windows']]==[ranges[i][0] for i in (0,2,3,1)],'earliest then three later windows')
    practical=evaluate(merge(base,{'tier':'B'}),p,ladder,matrix,aspects)
    sensitive=evaluate(merge(base,{'tier':'B','area':'health'}),p,ladder,matrix,aspects)
    require(screen_practice([sensitive]) is None and screen_practice([sensitive,practical,practical])=='saturn'
            and screen_practice([dict(practical,phase_end=None)]) is None,'one free practice after action and end')
    future=dict(base['period'], interval=['2032-04-25','2032-06-01'], subinterval=None)
    earlier=dict(base['period'], interval=['2032-02-01','2032-03-22'])
    pending=dict(base['period'], antar='rahu')
    timed=forecast(base,[future,pending,earlier],p,ladder,matrix,aspects)
    require([w['start'] for w in timed]==['2032-03-10','2032-04-25'],'search across disjoint Antars')
    require(len(ladder['rungs'])==8 and not any(ladder['flags'].values()),'MVP ladder')
    require(double({'jupiter':6,'saturn':11},[10,1],aspects) and
            not double({'jupiter':6,'saturn':11},[1,5],aspects),'independent reference targets')
    print(f'KB-36: {len(fixtures["cases"])} synthesis scenarios and independent double-transit references passed.')
