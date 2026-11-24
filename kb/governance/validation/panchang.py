"""Synthetic angular crossings, sunrise-day partitions and regional observances."""
from datetime import date, datetime, time, timedelta
from fractions import Fraction
from zoneinfo import ZoneInfo

P = 'vedic/panchang/'
DAY = timedelta(days=1)
HOUR = timedelta(hours=1)
TURN = 1296000


def partition(a,b,n):
    return [(a+(b-a)*i/n, a+(b-a)*(i+1)/n) for i in range(n)]


def overlaps(first,second):
    return max(first[0],second[0]) < min(first[1],second[1])


def lunar_month(start,end,ingresses,names):
    inside = [s for at,s in ingresses if start<=at<end]
    if inside:
        return ['ordinary' if len(inside)==1 else 'kshaya', *(names[s] for s in inside)]
    return ['adhika',next(names[s] for at,s in ingresses if at>=end)]


def new_year(month,tithi,candidate_rises):
    if month!='chaitra':
        return None
    hits = [r for r in candidate_rises if tithi[0]<=r<tithi[1]]
    return min(hits) if hits else max(r for r in candidate_rises if r<tithi[0])


def lamps(amanta_month,tithi,evenings):
    if amanta_month!=['ordinary','ashvina']:
        return None
    hits = [s.date() for s,r in evenings if overlaps(tithi,(s,s+(r-s)/5))]
    return max(hits,default=None)


def validate_panchang(rules,read,evaluate,require):
    table,params,clock,cal = [read(P+f+'.yaml') for f in
                              ('limb-tables','limbs','day-night','calendar-profiles')]
    fixture = read('examples/panchang-reference.yaml')
    require(fixture['synthetic'] and set(fixture['cities'])=={'Bengaluru','Delhi','Mumbai'},'dated Panchang fixtures')
    days = 'sunday monday tuesday wednesday thursday friday saturday'.split()
    lords = 'sun moon mars mercury jupiter venus saturn'.split()
    require(list(table['vara'].items())==list(zip(days,lords)), 'vara table')
    stars = read(table['nakshatra_catalog'])['nakshatras']
    require(len(stars)==27 and all(table['nakshatra_id'].format(id=s['id']) in rules for s in stars),'KB-03 links')
    widths = params['width_arcseconds']
    require(widths==dict(tithi=43200,karana=21600,nakshatra=48000,yoga=48000),'angular widths')
    names = 'Pratipada Dvitiya Tritiya Chaturthi Panchami Shashthi Saptami Ashtami Navami Dashami Ekadashi Dvadashi Trayodashi Chaturdashi'.split()
    for i,row in enumerate(table['tithi']):
        require(row==dict(number=i+1,index0=i,paksha='shukla' if i<15 else 'krishna',
                          name=(names+['Purnima']+names+['Amavasya'])[i]),row)
    require(len(table['tithi'])==30 and table['yoga']==
            'Vishkambha Priti Ayushman Saubhagya Shobhana Atiganda Sukarma Dhriti Shula Ganda Vriddhi Dhruva Vyaghata Harshana Vajra Siddhi Vyatipata Variyan Parigha Shiva Siddha Sadhya Shubha Shukla Brahma Indra Vaidhriti'.split(),'limb inventory')
    def karana(i):
        fixed = table['karana']['fixed']
        return fixed[i] if i in fixed else table['karana']['movable'][(i-1)%7]
    movable = 'bava balava kaulava taitila gara vanija vishti'.split()
    require([karana(i) for i in range(60)]==['kimstughna']+movable*8+['shakuni','chatushpada','naga'],'karana sequence')
    eighths = params['day_eighths_sunday_first']
    require(eighths==dict(rahu=[8,2,7,5,6,4,3],yamaganda=[5,4,3,2,1,7,6],gulika=[7,6,5,4,3,2,1]),'day eighths')
    def fires(slug,key,value):
        return evaluate(rules['vedic.panchang.'+slug]['conditions'],{'panchang.'+key:value})
    for limb,width in widths.items():
        count=TURN//width
        for i in range(count):
            lo=i*width
            require((lo%TURN)//width==i and ((lo-Fraction(1,100))%TURN)//width==(i-1)%count,(limb,i))
    zone = ZoneInfo(fixture['zone'])
    def stamp(s):
        return datetime.fromisoformat(s).replace(tzinfo=zone)
    for case in fixture['months']:
        events=[(stamp(at),sign) for at,sign in case['ingresses']]
        result=lunar_month(stamp(case['start']),stamp(case['end']),events,cal['amanta_months_by_entered_sign'])
        require(result==case['expected'],case)
        require(fires('adhika-masa','adhika_masa.active',result[0]=='adhika')==(result[0]=='adhika'),case)
    for city,c in fixture['cities'].items():
        day=date.fromisoformat(c['date'])
        def at(t,offset=0):
            return datetime.combine(day+offset*DAY,time.fromisoformat(t),tzinfo=zone)
        prev,rise,set_,next_rise=[at(t,offset) for t,offset in zip(c['anchors'],[-1,0,0,1],strict=True)]
        w=(day.weekday()+1)%7
        sun,moon=[v*3600 for v in c['degrees']]
        angles=dict(tithi=moon-sun,karana=moon-sun,nakshatra=moon,yoga=moon+sun)
        rs,rm=[fixture['rates_deg_per_day'][g]*3600 for g in ('sun','moon')]
        rates=dict(tithi=rm-rs,karana=rm-rs,nakshatra=rm,yoga=rm+rs)
        result={};bounds={}
        for label,angle in angles.items():
            width=widths[label]
            lo=angle//width*width
            result[label]=(angle%TURN)//width
            # Exact hours relative to the synthetic sunrise. Probe on both sides of every solved crossing.
            bounds[label]=[Fraction(24*(edge-angle),rates[label]) for edge in (lo,lo+width)]
            for edge,h in zip((lo,lo+width),bounds[label],strict=True):
                require(angle+rates[label]*h/24==edge and (edge-Fraction(1,100))//width==edge//width-1,city)
        t=result['tithi']+1
        require([days[w],t,stars[result['nakshatra']]['id'],table['yoga'][result['yoga']],karana(result['karana'])]==c['limbs'],city+' five limbs')
        require(bounds['tithi']==c['tithi_bounds_hours_from_rise'],city+' true synthetic crossings')
        for slug,valid in [('purnima',[15]),('amavasya',[30]),('ekadashi',[11,26])]:
            for probe in {t,*valid,1}:
                require(fires(slug,'tithi.number',probe)==(probe in valid),slug)
        for label,slots in eighths.items():
            window=partition(rise,set_,8)[slots[w]-1]
            require(window==tuple(at(x) for x in c['windows'][label]),city+' '+label)
        for label,a,b in [('abhijit',rise,set_),('brahma',prev,rise)]:
            j,n=clock[label]
            require(partition(a,b,n)[j-1]==tuple(at(x) for x in c['windows'][label]),city+' '+label)
        for night,a,b in [(False,rise,set_),(True,set_,next_rise)]:
            phase='night' if night else 'day'
            seq=clock['night_cycle' if night else 'choghadiya_order']
            first=seq.index(clock[phase+'_first_sun_through_sat'][w])
            for i,(left,right) in enumerate(partition(a,b,8)):
                require(a<=left<right<=b and seq[(first+i*clock[phase+'_step'])%7]==c[phase+'_choghadiya'][i],city+' choghadiya')
            cycle=clock['hora_cycle']
            require(cycle=='saturn jupiter mars sun venus mercury moon'.split(),'hora order')
            start=cycle.index(lords[w])+(12 if night else 0)
            require(cycle[start%7]==c[phase+'_first_hora'],city+' first hora')
            for i,(left,right) in enumerate(partition(a,b,12)):
                slot=(left-a)*12//(b-a)
                require(slot==i and left<right and cycle[(start+slot)%7]==cycle[(cycle.index(c[phase+'_first_hora'])+i)%7],city+' hora')
        for instant,expected in [(rise-timedelta(seconds=1),days[w-1]),(rise,days[w]),
                                (next_rise-timedelta(seconds=1),days[w]),(next_rise,days[(w+1)%7])]:
            anchor=max(a for a in (rise-DAY,rise,next_rise) if a<=instant)
            require(days[(anchor.weekday()+1)%7]==expected,city+' sunrise day')
        for instant,hit in [(rise,True),(next_rise,False)]:
            require(fires('sankranti','sankranti.active',rise<=instant<next_rise) is hit,city+' ingress day')
        pradosha=(set_,set_+(next_rise-set_)/5)
        for tide,number,hit in [((rise,set_),13,False),((set_,next_rise),28,True),((set_,next_rise),14,False)]:
            require(fires('pradosh','pradosh.active',number in (13,28) and overlaps(tide,pradosha)) is hit,city+' pradosh')
        if city=='Bengaluru':
            lunar=(rise-2*HOUR,rise+22*HOUR)
            require(new_year('chaitra',lunar,[rise-DAY,rise,next_rise])==rise,'Ugadi at sunrise')
            require(new_year('chaitra',(rise+HOUR,next_rise-HOUR),[rise,next_rise])==rise,'skipped Pratipada')
            require(new_year('chaitra',(rise,next_rise+HOUR),[rise,next_rise])==rise,'repeated Pratipada')
        if city=='Delhi':
            evenings=[(prev,rise),(set_,next_rise)]
            require(lamps(['ordinary','ashvina'],(rise-12*HOUR,rise+12*HOUR),evenings)==day,'Deepavali at dusk')
            require(lamps(['ordinary','ashvina'],(prev,set_+HOUR),evenings)==day,'both evenings')
            require(lamps(['ordinary','ashvina'],(rise,set_),evenings) is None,'no evening overlap')
            require(lamps(['adhika','ashvina'],(rise,set_+HOUR),evenings) is None,'month gate')
    print('Panchang passed: three dated city fixtures, all five limbs, sixty karanas, day/night windows, month and festival cases.')

    from election_factors import slots, star_slots, intersect, combinations
    offsets = read(P+'election-intervals.yaml')
    yogas = read(P+'election-yogas.yaml')
    names=[star['id'] for star in stars]
    require(list(offsets['stars'])==names and len(offsets['durmuhurta'])==7,'offset coverage')
    for name in names:
        spans=star_slots(0,1440,name,offsets)
        require(all(0<=a<b<=1440 and abs(b-a-96)<1e-8 for group in spans.values() for a,b in group),name)
        require(star_slots(None,1440,name,offsets)['amrit'] is None,name+' unknown start')
    require(star_slots(0,600,'mula',offsets)['varjyam']==[(200,240),(560,600)],'Mula two intervals')
    require(not intersect((240,300),[(200,240)]) and intersect((239,300),[(200,240)]),'half-open contact')
    require(slots(0,600,15,[3])==[(120,160)] and slots(600,1440,15,[4])==[(824,880)],'short day / Tuesday night')
    require('guru-pushya' in combinations(yogas,'thursday','pushya',None,3,names),'Guru Pushya')
    require('tri-pushkar' in combinations(yogas,'sunday','krittika',None,17,names) and
            'tri-pushkar' not in combinations(yogas,'monday','krittika',None,17,names),'Pushkar weekday')

    from election_factors import star_blocked
    require(star_blocked(0,{'sun':16},False,yogas) and star_blocked(0,{'rahu':8},False,yogas)
            and not star_blocked(1,{'sun':16},False,yogas) and star_blocked(1,None,False,yogas) is None,
            'inclusive Latta forward, backward, wrap and unknown')
