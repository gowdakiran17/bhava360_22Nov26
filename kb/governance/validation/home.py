"""Reference evaluation for personalised local-calendar screens. Sign indices start at Aries=0."""
from collections import Counter
from gochara import house, blocked


def testimony(planet, positions, vedha):
    distance = positions.get(planet)
    if distance is None:
        return None
    if distance not in vedha['support_to_obstruction'][planet]:
        return 'caution'
    obstacles = blocked(vedha, planet, positions)
    return None if obstacles is None else 'neutral' if obstacles else 'support'


def best_time(day, policy):
    if any(day.get(key) is None for key in ('daylight','candidates','exclusions')):
        return None
    sunrise, sunset = day['daylight']
    choices = []
    for kind, start, end in day['candidates']:
        if kind == 'abhijit' and day['weekday'] == 'Wednesday':
            continue
        pieces = [(max(start, sunrise), min(end, sunset))]
        for _, left, right in day['exclusions']:
            remaining = []
            for a, b in pieces:
                if a < right and left < b:
                    remaining.extend([(a, min(b,left)), (max(a,right), b)])
                else:
                    remaining.append((a,b))
            pieces = remaining
        for a,b in pieces:
            if b-a >= policy['minimum_minutes']:
                choices.append((policy['candidates'].index(kind), a-b, a, b))
    if choices:
        return list(min(choices)[2:])


def day_result(day, policy, vedha, ranking, activity, aspects, owners):
    signs = day['transits']
    origin = day.get('birth_moon')
    positions = {g:house(sign, origin) for g, sign in signs.items()} if origin is not None else {}
    chandra = testimony('moon', positions, vedha)
    stars = (day.get('transit_star'), day.get('birth_star'))
    tara = None if None in stars else 1 + (stars[0]-stars[1]) % 27 % 9
    tara_dir = None if tara is None else ('neutral' if tara==1 else
                'support' if tara in ranking['tara']['support'] else 'caution')
    sav = day.get('moon_sign_sav')
    av = None if sav is None else 'support' if sav >= policy['factors']['sav']['minimum'] else 'neutral'
    tone = next(t for a,b,c,t in policy['tone_resolution']
                if all(x=='any' or x==y for x,y in zip((a,b,c),(chandra,tara_dir,av))))
    antar = day.get('antar')
    focus = []
    if antar and (owners[signs['moon']]==antar or
                  house(signs['moon'],signs[antar]) in aspects[antar]):
        focus = day.get('owned_areas',[])
    choices = policy['activities']
    group = next((k for k,v in activity['nakshatra_groups'].items() if day['star_name'] in v),None)
    good = [choices['focus'][area] for area in focus if area in choices['focus']]
    good += [a for a in choices['eligible'] if group in activity['activity_preferences'][a]]
    if day.get('tithi') in choices['tithi']:
        good.append(choices['tithi'][day['tithi']])
    easy = ['starting-work','travel'] if tara_dir=='caution' or day.get('tithi')=='Rikta' else []
    good = [a for a in dict.fromkeys(good) if a not in easy][:choices['limits']['good']]
    # Clip independent Vishti to the civil date, including the part before sunrise.
    exclusions=[span for span in (day.get('exclusions') or []) if day.get('daylight') or span[0]=='vishti']
    context={k:day.get(k,[]) for k in ('fast_events','moon_contacts','slow_phase_boundaries')}
    return dict(context=context, tithi=day.get('tithi'), tone=tone, moon_house=positions.get('moon'), tara=tara, chandra=chandra, focus=focus,
                good=good, easy=easy, best=best_time(day, policy['best_time']),
                exclusions=exclusions,
                chips=[k for k,v in [('moon-chip',chandra),('star-chip',tara),('season-chip',focus)] if v])


def tomorrow(today, following, fast_events):
    if following is not None and today is not None and following != today:
        return 'tomorrow-tone'
    if any(e in ('ingress','direct-station','retrograde-station') for e in fast_events):
        return 'tomorrow-change'


def week(days, fast_testimonies, boundaries):
    if len(days)!=7 or len(fast_testimonies)!=7:
        raise ValueError('Seven consecutive local dates starting Monday are required')
    changed = any(a!=b for a,b in zip(fast_testimonies,fast_testimonies[1:]))
    return [day['tone'] for day in days], ('week-period' if boundaries else
                                         'week-movement' if changed else 'week-continuity')


def calendar_week(days, boundaries, policy, vedha, ranking, activity, aspects, owners):
    from datetime import date, timedelta
    start=date.fromisoformat(days[0]['date'])
    if start.weekday()!=0 or len(days)!=7:
        raise ValueError('Week must start Monday')
    daily=[]
    fast=[]
    for i,day in enumerate(days):
        if date.fromisoformat(day['date'])!=start+timedelta(days=i):
            raise ValueError('Nonconsecutive local dates')
        daily.append(day_result(day,policy,vedha,ranking,activity,aspects,owners))
        positions={g:house(s,day['birth_moon']) for g,s in day['transits'].items()} if day.get('birth_moon') is not None else {}
        fast.append(tuple(testimony(g,positions,vedha) for g in ('sun','mercury','venus','mars')))
    return week(daily,fast,[b for b in boundaries if days[0]['date']<=b<=days[-1]['date']])


def month(segments, vedha, events, start, end):
    """Contiguous half-open segments split at every ingress and obstruction endpoint."""
    houses = {g:Counter() for g in ('sun','mars','mercury','venus')}
    totals = {g:Counter() for g in houses}
    cursor = start
    for left,right,positions in segments:
        if left!=cursor or right<=left or right>end:
            raise ValueError('Incomplete or overlapping month')
        for g, durations in totals.items():
            position=positions.get(g)
            houses[g][position] += right-left
            durations[position,testimony(g,positions,vedha)] += right-left
        cursor=right
    if cursor!=end:
        raise ValueError('Incomplete month')
    stances = {}
    for g, visits in houses.items():
        dominant=next((h for h,v in visits.items() if 2*v>end-start),None)
        stances[g]=next((stance for (h,stance),duration in totals[g].items()
                         if dominant is not None and h==dominant and 2*duration>visits[h]),None)
    sun = stances['sun']
    tone = ('Supportive' if sun=='support' else 'Take care') if (
        sun in ('support','caution') and list(stances.values()).count(sun)>=3) else 'Steady'
    priority = ['sankranti','ingress','station','antar']
    eligible=set()
    for d,k,g in events:
        if not start<=d<end: continue
        if k=='ingress' and g=='sun': k='sankranti'
        if (k=='sankranti' and g=='sun' or k in ('station','ingress') and g in totals
                or k=='antar'):
            eligible.add((d,k,g))
    upcoming = sorted(eligible,
                      key=lambda e:(e[0],priority.index(e[1]),e[2]))[:3]
    return tone, upcoming


def month_screen(segments, vedha, events, start, end, saturn_house, saturn_sav, antar_nature):
    tone,upcoming=month(segments,vedha,events,start,end)
    sankranti=[]
    for day in sorted({d for d,k,g in events if g=='sun' and k in ('ingress','sankranti') and start<=d<end}):
        positions=next(positions for a,b,positions in segments if a<=day<b)
        sankranti.append((day,positions.get('sun')))
    return dict(tone=tone,upcoming=upcoming,sankranti=sankranti,
                phase=phase(saturn_house,saturn_sav,antar_nature))


def phase(saturn_house, sav, antar_nature):
    if saturn_house not in (12,1,2):
        return []
    keys = ['phase']
    if sav is not None and sav>=28:
        keys.append('phase-support')
    if antar_nature in ('Benefic','Yogakaraka'):
        keys.append('phase-timing')
    return keys


def validate(read, require):
    from functional import OWNERS
    from public_copy import check_text, LOCALES
    policy=read('modules/home/day.yaml')
    vedha=read('vedic/transits/vedha.yaml')
    ranking=read('vedic/muhurta/ranking-policy.yaml')
    activity=read('vedic/muhurta/activity-factors.yaml')
    aspects=read('vedic/aspects/full-graha.yaml')['inclusive_distances']
    fixture=read('examples/home-days.yaml')
    cases={}
    for name,case in fixture['cases'].items():
        day={**fixture['base'],**case.get('input',{})}
        result=day_result(day,policy,vedha,ranking,activity,aspects,OWNERS)
        require(all(result[k]==v for k,v in case['expect'].items()),(name,result,case['expect']))
        cases[name]=result
    require(all(cases['Asha'][k]!=cases['Ravi'][k] for k in ('tara','moon_house')), 'personal Moon references')
    require(tomorrow('Steady','Steady',[]) is None and tomorrow('Steady','Supportive',[])
            and tomorrow('Steady','Steady',['retrograde-station']), 'tomorrow conditional')
    days,headline=week([cases['D1']]*7,[1,1,2,2,2,2,2],['antar'])
    require(days==['Steady']*7 and headline=='week-period','week priority')
    supportive=dict.fromkeys(vedha['eligible_blockers'],11)
    adverse=dict.fromkeys(supportive,12)
    adverse['venus']=6
    for a,b,tone in [(8,2,'Supportive'),(2,8,'Take care'),(5,5,'Steady')]:
        value,events=month([(0,a,supportive),(a,a+b,adverse)],vedha,[(1,'sankranti','sun'),(10,'antar','jupiter')],0,10)
        require(value==tone and len(events)==1,'duration majority '+value)
    days=[dict(fixture['base'],date=f'2032-03-{i:02}',weekday=weekday) for i,weekday in
          enumerate(('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'),1)]
    require(calendar_week(days,['2032-03-07'],policy,vedha,ranking,activity,aspects,OWNERS)==
            (['Steady']*7,'week-period'),'actual Monday-Sunday screen')
    result=month_screen([(0,4,adverse),(4,10,supportive)],vedha,
        [(4,'ingress','sun'),(4,'sankranti','sun'),(5,'station','saturn'),(5,'antar','mars'),
         (6,'station','venus'),(8,'ingress','mercury')],0,10,2,28,'Yogakaraka')
    require(result['sankranti']==[(4,11)] and result['tone']=='Supportive' and
            result['upcoming']==[(4,'sankranti','sun'),(5,'antar','mars'),(6,'station','venus')],
            'actual sankranti house, deduplication, slow events outside list and three-item limit')
    require(phase(12,28,'Benefic')==['phase','phase-support','phase-timing'] and not phase(3,30,'Benefic'),'phase')
    messages=read('modules/home/copy.yaml')['messages']
    for i,segment in enumerate(('rising','middle','closing'),1):
        rule=read(f'vedic/transits/sade-sati-{segment}.yaml')
        require(rule['user_text']==messages[f'phase-{i}'],'single source for phase wording')
    keys=['phase','Supportive','Steady','Take care']
    keys += [f'{kind}-{a}' for kind in ('good','easy') for a in policy['activities']['eligible']]
    for key in keys:
        for locale in LOCALES:
            texts=[messages[f'{key}-{i}'].get(locale,messages[f'{key}-{i}']['en']) for i in (1,2,3)]
            require(len(set(texts))==3,key+' variants')
            for t in texts: check_text(t,key,locale)
    print(f'KB-37: {len(cases)} personal day cases, week and month windows, eight-locale copy passed.')
