"""Reference evaluation on supplied, boundary-stable synthetic election intervals."""
from datetime import datetime, timedelta
import re

P = 'vedic/muhurta/'
PREFIX = 'vedic.muhurta.'
DAYS = 'sunday monday tuesday wednesday thursday friday saturday'.split()
SIGNS = 'aries taurus gemini cancer leo virgo libra scorpio sagittarius capricorn aquarius pisces'.split()


def overlap(a,b,c,d):
    return max(a,c)<min(b,d)


def combust(sun, longitude, speed, body, orbs):
    distance = abs((longitude-sun+180)%360-180)
    thresholds = {orbs[branch][body] for branch in ('direct','retrograde')}
    if speed is None or speed==0:
        outcomes = {distance<=limit for limit in thresholds}
        return outcomes.pop() if len(outcomes)==1 else None
    return distance<=orbs['direct' if speed>0 else 'retrograde'][body]


def classify(values):
    return {frozenset(['support']):'Supportive',frozenset(['avoid']):'Take care'}.get(frozenset(values),'Steady')


def election(c,profile,policy,limbs,stars,eighths,orbs):
    # The fixture producer supplies no window that crosses a limb, lagna, or motion boundary.
    rise,setting,start,end = [datetime.fromisoformat(c[k]) for k in ('sunrise','sunset','start','end')]
    if not start<end or not rise<setting:
        return None,None,{}
    weekday = (rise.weekday()+1)%7
    eighth = (setting-rise)/8
    j = eighths[weekday]
    gates = set()
    if start<rise or end>setting:
        gates.add('outside-daylight')
    if overlap(start,end,rise+(j-1)*eighth,rise+j*eighth):
        gates.add('rahu-kalam')
    sun,moon,asc = [c[k]%360 for k in ('sun','moon','asc')]
    elongation = (moon-sun)%360
    half = int(elongation//6)
    karana = limbs['karana']['fixed'].get(half) or limbs['karana']['movable'][(half-1)%7]
    crosses_vishti = any(overlap(start,end,datetime.fromisoformat(a),datetime.fromisoformat(b))
                         for a,b in c.get('vishti_intervals',[]))
    if karana=='vishti' or crosses_vishti:
        gates.add('vishti')
    unresolved = False
    for body in profile['combustion'] if c.get("asta_method")!="visibility-days" and c.get("region_switches",{}).get("asta",True) else []:
        if body not in c:
            unresolved=True
            continue
        known=combust(sun,*c[body],body,orbs)
        if known:
            gates.add(body+'-combust')
        if known is None:
            unresolved=True
    if gates:
        return False,'Take care',{'blocked':sorted(gates)}
    names = c['participants']
    if unresolved or len(names)!=profile['required_people'] or len(set(names))!=len(names):
        return None,None,{}
    if any(name not in c['natal_moons'] for name in names):
        return None,None,{}
    star = int(moon*3//40)
    lagna = int(asc//30)
    tithi = int(elongation//12)+1
    values = dict(tithi=tithi,vara=DAYS[weekday],nakshatra=stars[star],yoga=limbs['yoga'][int(((moon+sun)%360)*3//40)],
                  karana=karana,lagna=SIGNS[lagna])
    evidence = {}
    for key,value in values.items():
        pref = profile['factors'][key]
        evidence[key]=next((kind for kind in ('support','avoid') if value in pref[kind]),'neutral')
    quarter = int(moon*3//10)%4+1
    if quarter in profile['quarter_cautions'].get(stars[star],[]):
        evidence['nakshatra']='avoid'
    reliefs = profile['reliefs']
    if 'entry-navamsa' in reliefs and evidence['lagna']=='avoid' and int(asc*3//10)%12==1:
        evidence['lagna']='neutral'
    if 'naming-tuesday' in reliefs and weekday==2:
        child=c.get('birth_date')
        if child is None:
            return None,None,{}
        if (rise.date()-datetime.fromisoformat(child).date()).days+1 in (10,12,16):
            evidence['vara']='neutral'
    remainder=(tithi+weekday+1+star+1+lagna+1)%9
    evidence['panchaka']='avoid' if remainder in profile['panchaka_avoid'] else 'support' if remainder in policy['panchaka']['clear'] else 'neutral'
    for person in names:
        natal=c['natal_moons'][person]%360
        birth_star=int(natal*3//40)
        tara=1+(star-birth_star)%27%9
        house=1+(int(moon//30)-int(natal//30))%12
        evidence['tara/'+person]='support' if tara in policy['tara']['support'] else 'avoid'
        if 'janma-star' in reliefs and birth_star==star:
            evidence['tara/'+person]='neutral'
        chandra='support' if house in policy['chandra']['support'] else 'avoid' if house in policy['chandra']['avoid'] else 'neutral'
        if 'chandra' in reliefs and house==8 and tara in policy['tara']['support']:
            chandra='neutral'
        evidence['chandra/'+person]=chandra
    from election_factors import classify_extra
    blocked, missing, soft = classify_extra(c, profile, policy, values, evidence, (rise,setting,start,end), DAYS, stars)
    if blocked:
        return False,'Take care',{'blocked':blocked}
    if missing:
        return None,None,{'missing':missing}
    evidence.update(soft)
    return True,classify(set(evidence.values())-{'neutral'}),evidence


def recommendations(candidates, rank):
    """All candidates belong to a single bound city, activity and set of participants."""
    unique = {(start,end,tone) for start,end,eligible,tone in candidates if eligible is True}
    return sorted(unique,key=lambda v:(rank.index(v[2]),v[0],v[1]))


def validate_muhurta(rules,read,evaluate,require):
    selection=read(P+'selection.yaml')
    policy=read(selection['ranking_policy'])
    expected='marriage griha-pravesha vehicle-purchase business-start naming travel education-start property-registration'.split()
    require(set(selection['activity_profiles'])==set(expected),'eight activity profiles')
    require(policy['ranking']==['Supportive','Steady','Take care'],'tone order')
    policy.update(interval_table=read('vedic/panchang/election-intervals.yaml'),day_yoga_table=read('vedic/panchang/election-yogas.yaml'),regions=read('vedic/muhurta/region-policy.yaml')['toggles'])
    tables=read('vedic/panchang/limb-tables.yaml')
    stars=[s['id'] for s in read(tables['nakshatra_catalog'])['nakshatras']]
    eighths=read('vedic/panchang/limbs.yaml')['day_eighths_sunday_first']['rahu']
    orbs=read('vedic/states/combustion-orbs.yaml')['orbs']
    domains=dict(tithi=range(1,31),vara=DAYS,nakshatra=stars,yoga=tables['yoga'],lagna=SIGNS,
                 karana=tables['karana']['movable']+list(tables['karana']['fixed'].values()))
    fixture=read('examples/muhurta-reference.yaml')
    require(fixture['synthetic'] and set(fixture['cases'])==set(expected),'fixture coverage')
    def run(c,p):
        return election(c,p,policy,tables,stars,eighths,orbs)
    for slug,rid in selection['activity_profiles'].items():
        r=rules[rid]
        p=r['activity_profile']
        require(p['activity']==slug and p['shared_policy']==selection['ranking_policy'] and
                p['required_people']==(2 if slug=='marriage' else 1),slug)
        require(set(p['factors'])==domains.keys() and p['combustion']==(['venus','jupiter'] if slug=='marriage' else []),slug)
        for k,d in domains.items():
            good,bad=[set(p['factors'][k][kind]) for kind in ('support','avoid')]
            require(good and bad and good.isdisjoint(bad) and (good|bad)<=set(d),(slug,k))
        require(set(p['reliefs'])=={e['when']['fact'].split('.')[-1].replace('_','-') for e in r['exceptions']},slug+' reliefs')
        require(all(not re.search(r'\d|scores?|points?',text,re.I) for text in r['user_text'].values()),slug+' public text')
        case=fixture['cases'][slug]
        c={**fixture['window'],**case}
        eligible,tone,evidence=run(c,p)
        require((eligible,tone)==(True,case['expected_tone']),(slug,eligible,tone,evidence))
        for name,kind in case['expected_reasons'].items():
            require(evidence[name]==kind,(slug,name,evidence))
        require(evaluate(r['conditions'],{'muhurta.activity':slug,'muhurta.window.eligible':eligible}) is True,slug)
        require(evaluate(r['conditions'],{'muhurta.activity':'unknown','muhurta.window.eligible':eligible}) is False,slug)
        for patch,reason in [(fixture['rahu_overlap'],'rahu-kalam'),({'moon':(c['sun']+45)%360},'vishti')]:
            ok,t,why=run({**c,**patch},p)
            require((ok,t)==(False,'Take care') and reason in why['blocked'],(slug,reason))
        require(run({**c,'participants':[]},p)[:2]==(None,None),slug+' missing participant')
        require(run({**c,**fixture['ends_at_rahu']},p)[0] is True,slug+' exact endpoint')
    for probe in fixture['probes']:
        slug=probe['activity']
        c={**fixture['window'],**fixture['cases'][slug],**probe['override']}
        ok,t,evidence=run(c,rules[selection['activity_profiles'][slug]]['activity_profile'])
        require((ok,t)==tuple(probe['result']),(probe,ok,t,evidence))
        for name,value in probe.get('reasons',{}).items():
            require(evidence[name]==value,(probe,name,evidence))
    require(combust(355,6,1,'jupiter',orbs) is True and combust(355,6.01,1,'jupiter',orbs) is False,'Jupiter wrap boundary')
    require(combust(0,9,0,'venus',orbs) is None and combust(0,8,0,'venus',orbs) is True,'Venus motion')
    for tone in policy['ranking']:
        rule=rules[PREFIX+'window-'+tone.lower().replace(' ','-')]
        require(evaluate(rule['conditions'],{'muhurta.window.tone':tone}) and
                all(not re.search(r'\d|scores?|points?',s,re.I) for s in rule['user_text'].values()),tone)
    require([r['en'] for r in read(policy['tone_labels'])['tones']]==policy['ranking'],'localized tone inventory')
    # Within one query a later supportive interval precedes a mixed one; exact duplicates render once.
    ranking_cases = fixture['ranking']
    candidates = [(datetime.fromisoformat(start),datetime.fromisoformat(end),ok,tone)
                  for start,end,ok,tone in ranking_cases['input']]
    ranked = recommendations(candidates,policy['ranking'])
    require([(a.isoformat(),b.isoformat(),t) for a,b,t in ranked]==
            [tuple(row) for row in ranking_cases['expected']], 'tone, time, duplicates and exclusion order')
    require(classify(set())=='Steady' and classify({'avoid'})=='Take care' and
            classify({'avoid','support'})=='Steady', 'tone decision matrix')
    print('Muhurta passed: eight dated activity profiles, personal reliefs, hard exclusions, and qualitative tones.')

    marriage=rules[selection['activity_profiles']['marriage']]['activity_profile']
    avoid=set(marriage['factors']['yoga']['avoid'])
    require(avoid<=set('Vishkambha Atiganda Shula Ganda Vyaghata Vajra Vyatipata Parigha Vaidhriti'.split())
            and 'Dhruva' in marriage['factors']['yoga']['support'],'marriage nitya yoga')
    base={**fixture['window'],**fixture['cases']['marriage']}
    def blocked(patch, reason):
        ok,_,info=run({**base,**patch},marriage)
        return ok is False and reason in info['blocked']
    for patch,reason in [
        ({'occupied_houses':[7]},'seventh_occupied'),({'occupied_houses':[8]},'eighth_occupied'),
        ({'star_obstructed':True},'star_obstructed'),({'adhika':True},'adhika'),
        ({'sun':240,'moon':270},'kharmas'),({'sun':359.99,'moon':29.99},'kharmas'),
        ({'moon':55},'rikta_or_new'),({'moon':15},'rikta_or_new'),
        ({'region_switches':{'chaturmas':True},'chaturmas':True},'chaturmas'),
        ({'region_switches':{'holashtak':True},'holashtak':True},'holashtak'),
        ({'asta_method':'visibility-days','invisible_luminary':True},'asta'),
        ({'vishti_intervals':[[base['sunrise'],base['end']]]},'vishti'),
    ]:
        require(blocked(patch,reason),(reason,patch))
    require(run(dict(base,occupied_houses=None),marriage)[0] is None,'missing house testimony')
    require(run(dict(base,star_interval=None),marriage)[0] is None,'unbracketed star')
    require(run(dict(base,chaturmas=True,holashtak=True),marriage)[0] is True,'regional opt-in')
    sample=read('examples/transits-vargas-elections.yaml')['M5']
    winners=[]
    for date,start,end,expected in sample['candidates']:
        c=dict(base)
        def at(hhmm): return date+'T'+hhmm+':00+05:30'
        c.update(sunrise=at('06:00'),sunset=at('18:00'),start=at(start),end=at(end),
                 star_interval=[at('05:30'),(datetime.fromisoformat(at('05:30'))+timedelta(days=1)).isoformat()])
        ok,tone,info=run(c,marriage)
        require((tone if ok else info['blocked'][0])==expected,(date,start,expected,tone,info))
        winners.append((c['start'],c['end'],ok,tone))
    require(len(recommendations(winners,policy['ranking']))==3,'M5 survivors')
    travel=rules[selection['activity_profiles']['travel']]['activity_profile']
    departure=dict(base, participants=['Asha'], direction='south',region_switches={'panchaka':True},sun=270)
    for moon,expected in [(299.99,False),(300,True),(359.99,True),(0,False)]:
        # Keep elongation fixed so that an independent Vishti interval cannot mask this gate.
        ok,_,info=run(dict(departure,moon=moon,sun=(moon-30)%360),travel)
        require(('panchaka' in info.get('blocked',[]))==expected,(moon,info))
    for location,zone,offset in [('Honolulu','Pacific/Honolulu','-10:00'),('Delhi','Asia/Kolkata','+05:30'),
                                  ('Bengaluru','Asia/Kolkata','+05:30')]:
        from zoneinfo import ZoneInfo
        # Invented short winter daylight, Friday Rahu is the fourth of eight equal intervals.
        def local(value): return '2032-12-17T'+value+':00'+offset
        c=dict(base,city=location,sunrise=local('07:00'),sunset=local('17:00'),start=local('10:45'),end=local('10:46'))
        require(datetime.fromisoformat(c['start']).astimezone(ZoneInfo(zone)).hour==10,location)
        require('rahu-kalam' in run(c,marriage)[2]['blocked'],location+' short winter Rahu interval')
        c.update(start=local('07:00'),end=local('07:01'),vishti_intervals=[[local('06:50'),local('07:01')]])
        require('vishti' in run(c,marriage)[2]['blocked'],location+' Vishti spanning sunrise')
    require([(a[:10],a[11:16],b[11:16],t) for a,b,t in recommendations(winners,policy['ranking'])]==
            [tuple(row) for row in sample['ranked_survivors']],'M5 ranked display')
