"""Authoring command for the fixed-date KB consultation. Requires the generate.py Swiss data."""
from generate import (ROOT, AT, PEOPLE, SIGNS, chart, labels, read, datetime, timedelta,
                      swe, os, yaml, Path)
from functional import OWNERS, resolve
from bhava_bala import benefic, relationship, dignity_label
from strength_grade import worksheet
from yoga_charts import references, fixture_facts, GRAHAS
from yoga_activation import existing_participants, project
from yoga_formation import participants
from check import evaluate
from timing import bind, period_notes, upcoming
from synthesis import evaluate as synthesis
from home import day_result, month
from ashtakavarga import prastara_for

AREAS = ('career','love-marriage','money','health','family-home','learning')
ASPECTS=read('vedic/aspects/full-graha.yaml')['inclusive_distances']
FUNCTIONAL=read('vedic/lordships/functional.yaml')['cells']
NATURE=read('vedic/planets/benefic-profile.yaml')
DIGNITY=read('vedic/dignity/sign-dignities.yaml')
MATRIX=read('shared/confidence/output-matrix.yaml')['rows']
STARS=read('vedic/nakshatras/catalog.yaml')['nakshatras']
VEDHA=read('vedic/transits/vedha.yaml')

def angular_distance(a,b):
    return abs((a-b+180)%360-180)

def dignity(g,x,positions):
    if g not in GRAHAS:return None
    sign=SIGNS[int(x//30)]
    host=OWNERS[int(x//30)]
    friends=read(f'vedic/planets/{g}.yaml')['graha']['natural_friendships']
    relation=next((kind for field,kind in [('friends','friend'),('enemies','enemy')] if host in friends[field]),'neutral')
    compound=relationship(read('vedic/dignity/relationships.yaml'),relation,(positions[host]-positions[g])%12+1)
    return dignity_label(DIGNITY,g,sign,x%30,host==g,compound)

def work(name,month_segments):
    r=read('examples/fixtures/'+name.lower()+'.yaml')
    bodies=r['grahas']
    lon={g:p['longitude'] for g,p in bodies.items()}
    pos={g:int(x//30) for g,x in lon.items()}
    asc=r['lagna']
    lagna=SIGNS.index(asc['sign']) if asc else None
    phase=r['working_instant_periods'].get('reading',{})
    period={k:v['lord'] for k,v in phase.items()}
    md,ad=period.get('maha'),period.get('antar')
    data=dict(longitude={g:lon[g] for g in GRAHAS},house_pair=(1,7),jupiter_shadbala_rupas=0,selected_graha='moon')
    tables=references(read)
    if asc:data['longitude']['lagna']=asc['longitude']
    def facts(g):
        if not asc:return {}
        f=fixture_facts(dict(data,selected_graha=g),tables)
        f.pop('d1.jupiter.saraswati_strength') # no independent Shadbala for this fixture
        return f
    grades={}
    details={}
    d9pos={g:SIGNS.index(p['d9']) for g,p in bodies.items()}
    nature={g:'benefic' if benefic(g,lon,NATURE) else 'malefic' for g in bodies}
    samples=[]
    if not asc:
        noon=datetime.fromisoformat(r['local'])
        samples=[chart(noon+timedelta(minutes=i)) for i in range(-720,721,12)]
    for g,p in bodies.items():
        inputs=dict(graha=g,lagna_withheld=lagna is None,house_lagna=None if lagna is None else (pos[g]-lagna)%12+1,
                    house_moon=(pos[g]-pos['moon'])%12+1,d1=dignity(g,lon[g],pos),d9=dignity(g,(lon[g]*9)%360,d9pos),
                    aspects={b:[(pos[g]-s)%12+1,nature[b]] for b,s in pos.items() if b!=g and (pos[g]-s)%12+1 in ASPECTS[b]},
                    natural_nature=nature[g],retrograde=p['retrograde'],combust=p['combust'],vargottama=pos[g]==d9pos[g],
                    elongation=(lon['moon']-lon['sun'])%360,relief_facts=facts(g) if g in GRAHAS else {})
        # The war test requires a resolved winner only for close classical non-luminaries.
        warriors=set(GRAHAS)-{'sun','moon'}
        inputs['war_loser']=g in warriors and any(angular_distance(lon[g],lon[b])<1 and p['latitude']<bodies[b]['latitude'] for b in warriors-{g})
        if inputs['d1']=='debilitation-sign':
            hosts=[OWNERS[pos[g]],OWNERS[SIGNS.index(DIGNITY['grahas'][g]['exaltation'])]]
            inputs['relief_identity']=dict(zip(['d1.dignity.debility_lord_angular','d1.dignity.exaltation_lord_angular'],hosts))
            for b in GRAHAS:
                if DIGNITY['grahas'][b]['exaltation']==p['sign']:inputs['relief_identity']['d1.dignity.exaltee_angular']=b
        w=worksheet(inputs,read('vedic/strength/grade.yaml'),read('vedic/yogas/neecha-bhanga.yaml'),ASPECTS,NATURE)
        # Moon-relative house changes and uncertain aspect partners affect the whole worksheet.
        if 'd9' in p['unstable'] or 'sign' in p['unstable']:w=None
        if not asc and w:
            for sample in samples:
                longs={b:pair[0] for b,pair in sample.items()}
                signs={b:int(x//30) for b,x in longs.items()}
                nav={b:int(x*9//30)%12 for b,x in longs.items()}
                distance=(signs[g]-signs['moon'])%12+1
                received={b:[(signs[g]-s)%12+1,'benefic' if benefic(b,longs,NATURE) else 'malefic']
                          for b,s in signs.items() if b!=g and (signs[g]-s)%12+1 in ASPECTS[b]}
                orb=read('vedic/states/combustion.yaml')['state']['orbs']['retrograde' if sample[g][1]<0 else 'direct'].get(g)
                close_pair=g in warriors and any(angular_distance(longs[g],longs[b])<1 for b in warriors-{g})
                if close_pair:
                    w=None
                    break
                candidate=worksheet(dict(inputs,house_moon=distance,d1=dignity(g,longs[g],signs),
                    d9=dignity(g,longs[g]*9%360,nav),aspects=received,vargottama=signs[g]==nav[g],
                    retrograde=sample[g][1]<0,natural_nature='benefic' if benefic(g,longs,NATURE) else 'malefic',
                    combust=orb is not None and angular_distance(longs['sun'],longs[g])<=orb,
                    elongation=(longs['moon']-longs['sun'])%360), read('vedic/strength/grade.yaml'),
                    read('vedic/yogas/neecha-bhanga.yaml'),ASPECTS,NATURE)
                if candidate!=w:
                    w=None
                    break
        grades[g]=w and w['grade']
        details[g]=dict(worksheet=w,d1=inputs['d1'],d9=inputs['d9'],functional=resolve(FUNCTIONAL,asc and asc['sign'],g,p['sign']))
    charts=dict(lagna=lagna,signs=pos,grades=grades)
    matched={}
    f=facts('moon')
    f.update({'d1.yoga.foundation_cancelled':False,'d1.yoga.mercury_combust':bodies['mercury']['combust'],
              'd1.yoga.mercury_deep_combust':angular_distance(lon['sun'],lon['mercury'])<=3,
              'd1.yoga.mercury_gate_miss':grades['mercury']=='Weak' and lagna is not None and (pos['mercury']-lagna)%12+1 not in (1,4,5,7,9,10),
              'd1.yoga.kemadruma_angular':None if lagna is None else any((pos[g]-lagna)%12 in (0,3,6,9) for g in GRAHAS if g!='moon'),
              'd1.yoga.moon_benefic_aspect':any(nature[g]=='benefic' and (pos['moon']-pos[g])%12+1 in ASPECTS[g] for g in GRAHAS if g!='moon')})
    for path in sorted((ROOT/'vedic/yogas').glob('*.yaml')):
        rule=read('vedic/yogas/'+path.name)
        if 'conditions' not in rule or 'participants' not in rule or not asc:continue
        slug=path.stem
        if 'formation' in rule:
            group=participants(slug,rule['formation'],dict(charts,signs={g:pos[g] for g in GRAHAS},
                benefics=[g for g in GRAHAS if nature[g]=='benefic'],full_aspects=ASPECTS,
                exaltation={g:SIGNS.index(DIGNITY['grahas'][g]['exaltation']) for g in GRAHAS},d9=d9pos))
            groups=[group] if group else []
        elif evaluate(rule['conditions'],f) is True:
            groups=existing_participants(slug,rule,data,tables,f)
        else:groups=[]
        for group in groups:
            if group:
                result=project(rule,True,group,f,grades,md,ad,evaluate)
                matched.setdefault(rule['id'],[]).append(dict(participants=sorted(group),**result))
    current=chart(AT)
    transit={g:int(x//30) for g,(x,_) in current.items()}
    trans={ref:[f'vedic.transits.{g}-{ref}-house-{(s-origin)%12+1}' for g,s in transit.items()]
           if origin is not None else [] for ref,origin in [('moon',pos['moon']),('lagna',lagna)]}
    bav={}
    if asc:
        for g,table in read('vedic/strength/ashtakavarga/bindu.yaml')['offsets'].items():
            bits=prastara_for(table,dict(pos,lagna=lagna))
            bav[g]=list(map(sum,zip(*bits.values())))
    sav=list(map(sum,zip(*bav.values()))) if bav else None
    tier=r['tier']
    period.update(interval=[phase['antar'][i][:10] for i in ('start','end')] if ad else [],
                  subinterval=[phase['pratyantar'][i][:10] for i in ('start','end')] if ad else [],
                  star_lords={g:STARS[int(x*27/360)]['vimshottari_lord'] for g,x in lon.items()})
    areas={}
    for area in AREAS:
        recipe=read('life-areas/recipes.yaml')['recipes'][area]
        lord=OWNERS[(lagna+recipe['houses'][0]-1)%12] if asc else None
        stable=asc and 'd9' not in asc['unstable'] and 'd9' not in bodies[lord]['unstable']
        unstable=[] if stable else ['promise-varga-lagna']
        if area=='career' and asc and ('d10' in asc['unstable'] or 'd10' in bodies[lord]['unstable']):unstable=['promise-varga-lagna']
        segment=dict(interval=['2026-11-24','2026-11-25'],signs=transit,av=[
            [sav[transit[g]],bav[g][transit[g]]] if sav else [None,None] for g in ('jupiter','saturn')])
        charts['window_inputs']=dict(today='2026-11-24',tier=tier,unstable=unstable,
            d9=details[lord]['d9'] if stable else None,vargottama=bool(stable and d9pos[lord]==pos[lord]),
            topic_lord={'house':(SIGNS.index(bodies[lord]['d10'])-SIGNS.index(asc['d10']))%12+1} if asc else {},
            segments=[segment],yoga={'active':False},directions={})
        eligible=[(rid,row) for rid,rows in matched.items() if area in read('vedic/yogas/'+rid.split('.')[-1]+'.yaml')['life_areas'] for row in rows if row['period_evidence']]
        charts.pop('yoga_record',None)
        if eligible:
            rid,row=eligible[0];charts['yoga_record']=dict(row,slug=rid.split('.')[-1])
        bound=bind(area,charts,period,recipe,read)
        result=synthesis(bound,read('life-areas/pipeline.yaml'),read('life-areas/conflict-ladder.yaml'),MATRIX,ASPECTS)
        states,windows=upcoming(area,charts,[period],read)
        notes=period_notes(charts,area,period,read)
        areas[area]=dict(lord=lord,promise=result['band'],state=states,windows=windows,
                         availability='Moon-only; Lagna promise withheld' if not asc else 'known-time',
                         witnesses=bound['lagna'],moon_witnesses=bound['moon'],
                         challenge_resolution=result.get('grade'),card=windows[0]['tone'] if windows else None,
                         modulation={k:[n['reason'] for n in v['notes']['pair']] for k,v in notes.items()},
                         active_yogas=sorted(set(rid for rid,_ in eligible)),practice_lord=result['remedy_graha'] if windows else None)
    day=day_result(dict(tier=tier,weekday='Tuesday',transits=transit,birth_moon=pos['moon'],
        transit_star=int(current['moon'][0]*27/360),birth_star=None if 'nakshatra' in bodies['moon']['unstable'] else int(lon['moon']*27/360),
        tithi=('Nanda','Bhadra','Jaya','Rikta','Purna')[int(((current['moon'][0]-current['sun'][0])%360)//12)%5],
        star_name=labels(current['moon'][0])['nakshatra'],moon_sign_sav=sav and sav[transit['moon']],antar=ad),
        read('modules/home/day.yaml'),VEDHA,read('vedic/muhurta/ranking-policy.yaml'),
        read('vedic/muhurta/activity-factors.yaml'),ASPECTS,OWNERS)
    segments=[(a,b,{g:(s-pos['moon'])%12+1 for g,s in signs.items()}) for a,b,signs in month_segments]
    monthly=month(segments,VEDHA,[],segments[0][0],segments[-1][1])[0]
    lunar=read('vedic/transits/'+trans['moon'][1].split('.')[-1]+'.yaml')['user_text']['en']
    public=dict(today=lunar,month={'Supportive':'You may find room to move a plan forward this month.','Steady':'You can balance familiar commitments with a little room to adjust this month.','Take care':'You can leave extra time for changes in your plans this month.'}[monthly])
    if tier=='C':public['confidence']=read('shared/confidence/copy.yaml')['messages']['moon-unknown']['en']
    for area,row in areas.items():
        if row['windows']:
            public[area]=read('vedic/dashas/vimshottari/'+area+'-upcoming.yaml')['user_text']['en']
    placement=[f'vedic.planets-in-signs.{g}-{p["sign"]}' for g,p in bodies.items() if 'sign' not in p['unstable']]
    area_rules=[]
    for area,row in areas.items():
        if row['windows']:
            area_rules.append('vedic.dashas-vimshottari.'+area+'-upcoming')
        if asc and md:
            rule=read('vedic/dashas/vimshottari/'+area+'-house-lord.yaml')
            owners={f'dasha.active_lord.owns_house_{h}':OWNERS[(lagna+h-1)%12]==md for h in range(1,13)}
            if evaluate(rule['conditions'],owners) is True:area_rules.append(rule['id'])
    periods=[f'vedic.dashas-vimshottari.{md}-maha',f'vedic.dashas-vimshottari.{md}-{ad}-antar'] if md else []
    if not asc:
        # The Moon may keep its sign while changing nakshatra. No natal period dates or Lagna timing follow.
        assert not period.get('antar') and not areas['career']['windows']
    practice=next((v['practice_lord'] for v in areas.values() if v['practice_lord']),None)
    if practice:
        remedy=read('remedies/'+practice+'.yaml')
        public['traditional_practice']=remedy['remedy']['user_text']['en']
    for summary in areas.values():
        summary['conflict_ladder']={
            'promise':summary['promise'],'activated_yogas':summary['active_yogas'],
            'functional_lord':details[summary['lord']]['functional'] if summary['lord'] else None,
            'participant_gate':'see yoga witnesses','divisional':'confirm after D1 floor',
            'references':'Lagna confirms, Moon describes experience' if asc else 'Moon only',
            'other_systems':'disabled','final':summary['card']}
    return dict(optional_practice=practice,rule_chain=placement+list(matched)+periods+area_rules+trans['moon']+trans['lagna'],grades=details,yogas=matched,
                areas=areas,transits=trans,today=day,month_tone=monthly,public_en=public,
                confidence={k:MATRIX[k][tier] for k in ('lagna','bav','sav','kakshya','d9','d10','d9-planet-sign','d10-planet-sign','birth-panchanga','shadbala-kala')})

def main():
    swe.set_ephe_path(os.environ['SWEPH_PATH'])
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    start=AT.replace(day=1,hour=0)
    # Split at real ingress boundaries. Six-hour brackets are shorter than the
    # fastest sign crossing; bisect every changing body independently.
    def signs(t):return {g:int(x//30) for g,(x,s) in chart(t).items()}
    bounds={0,30*86400}
    for h in range(0,30*24,6):
        a=h*3600;b=a+21600;left=signs(start+timedelta(seconds=a));right=signs(start+timedelta(seconds=b))
        for g in left:
            if left[g]==right[g]:continue
            lo,hi=a,b
            while hi-lo>1:
                m=(lo+hi)//2
                if signs(start+timedelta(seconds=m))[g]==left[g]:lo=m
                else:hi=m
            bounds.add(hi)
    edges=sorted(bounds)
    segments=[(a,b,signs(start+timedelta(seconds=a))) for a,b in zip(edges,edges[1:])]
    for person in PEOPLE:
        name=person[0]
        rec=work(name,segments)
        predicates={}
        for rid in rec['rule_chain']:
            system,topic,slug=rid.split('.')
            folder='dashas/vimshottari' if topic=='dashas-vimshottari' else topic
            predicates[rid]=read(f'{system}/{folder}/{slug}.yaml')['conditions']
        rec['matched_predicates']=predicates
        rec['matrix_applications']={
            'varga_planets':{key:{g:p[key] for g,p in read('examples/fixtures/'+name.lower()+'.yaml')['grahas'].items()
                                 if key not in p['unstable']} for key in ('d9','d10')},
            'birth_panchanga':read('examples/fixtures/'+name.lower()+'.yaml')['stable_birth_panchanga'],
            'kala_bala':'withhold time-dependent subtotal' if name=='Dev' else 'eligible with resolved rise/set',
            'twilight':{'lower_deg':-6,'upper_approx_deg':-0.83,'upper_exclusive':True,'variant':'classical ghatika sandhya'}}

        path=ROOT/'examples/fixtures'/(name.lower()+'.yaml')
        data=yaml.safe_load(path.read_text());data['consultation']=rec
        path.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True))
        lines=[f'# {name} · synthetic worked reading','',f'24 November 2026 · {data["city"]}. Birth-time tier {data["tier"]}.','',
               '## Reading','',*(f'- **{key.replace('_',' ').title()}** · {s}' for key,s in rec['public_en'].items()),'',
               '## Admin worksheet','',f'Today resolves to {rec["today"]["tone"]}. The calendar month resolves to {rec["month_tone"]}.',
               '', '| Area | Natal promise | Dated result |', '|---|---|---|',
               *(f'| {k} | {v["promise"]} | {", ".join(v["state"])} |' for k,v in rec['areas'].items()),'',
               f'The [reference chart](../fixtures/{name.lower()}.yaml) records graha positions, precision, strength worksheets, yoga witnesses and cancellations, period modulation, the conflict-ladder outcome, separate transit references and eligible practices. Windows here answer the query for this local day.']
        natal=data['grahas']
        maha=data['working_instant_periods'].get('reading',{})
        lines+=['','### Consultation in order','',
                f"At the working instant the Moon is in {natal['moon']['sign'].title()}. "
                +(f"The ascendant is {data['lagna']['sign'].title()}." if data['lagna'] else
                  "The local date crosses a lunar-star boundary. Lagna, its house lords and dated periods are withheld."),
                '', 'The table below binds each period, yoga and transit to this chart before the six area recipes select a card.', '',
                '| Stage | Chart evidence |','|---|---|',
                '| Period | '+(' / '.join(maha[k]['lord'].title() for k in ('maha','antar')) if maha else 'Withheld')+' |',
                '| Strength | '+', '.join(g.title()+' '+(v['worksheet']['grade'] if v['worksheet'] else 'withheld') for g,v in rec['grades'].items())+' |',
                '| Yoga | '+('; '.join(key.split('.')[-1]+' '+rows[0]['display'] for key,rows in rec['yogas'].items()) or 'No resolved Lagna-based witness')+' |',
                '| Transit from Moon | '+', '.join(rec['transits']['moon'][:2])+' |',
                '| Transit from Lagna | '+(', '.join(rec['transits']['lagna'][:2]) or 'Withheld')+' |',
                '| Practice | '+(rec['optional_practice'] or 'None selected')+' |']
        (ROOT/'examples/worked-readings'/(name.lower()+'.md')).write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
