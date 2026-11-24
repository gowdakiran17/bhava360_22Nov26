"""Worked examples and boundary contracts for the annual and natal reference tables."""
from itertools import chain
from math import isclose
import swisseph as swe

from tajika import (contact, election, harsha, mudda, patyayini, return_place, saham, solar_return,
                    transfer, year_lord)


def star_reading(rules, actor, minutes, stable=True):
    if minutes is None or not stable:
        return None
    minutes %= 21600
    star, = [r for r in rules.values() if 'nakshatra' in r and isinstance(r['nakshatra'], dict)
             and r['nakshatra'].get('span_arcminutes', [0,0])[0] <= minutes <
             r['nakshatra'].get('span_arcminutes', [0,0])[1]]
    data = star['nakshatra']
    quarter = data['padas'][int(minutes % 800 // 200)]
    name = star['id'].split('.')[-1]
    base = star if actor == 'moon' else rules['vedic.star-readings.lagna-' + name]
    lord = data['vimshottari_lord']
    ids = [base['id'], 'vedic.star-readings.' + actor + '-quarter-' + quarter['navamsha'],
           'vedic.star-readings.lord-' + lord]
    return name, quarter['pada'], lord, quarter['navamsha'], [rules[key]['user_text'] for key in ids]


def vimshopaka(table, scheme, dignity):
    weights = table['weights'][scheme]
    if any(dignity.get(d) not in table['dignity'] for d in weights):
        return None
    units = sum(w * table['dignity'][dignity[d]] for d, w in weights.items()) / 20
    band = max((lo, label) for label, lo in table['bands'].items() if units >= lo)[1]
    return units, band


def deity(names, longitude, tier, stable):
    if tier != 'A' or not stable or longitude is None:
        return None
    sign, arc = divmod(longitude % 360, 30)
    i = int(arc * 2)
    return names[59-i if int(sign) % 2 else i]


def check_annual(read, rules, require):
    core = read('vedic/tajika/aspects.yaml')
    def probe(x, y, u=13, v=1):
        return contact(core, 'moon', 'saturn', {'moon': (x,u), 'saturn': (y,v)})
    require(probe(20,25)['state']=='applying' and probe(25,20)['state']=='separating', 'same sign motion')
    require(probe(28,98.5)['orb']==10.5 and probe(28,98.50001) is None, 'inclusive mean orb across signs')
    require(probe(359,1)['state']=='applying' and probe(0,60)['state']=='exact' and
            probe(0,61,1,1)['state']=='stationary' and probe(None,61) is None, 'wrap, exact, stationary, unknown')
    require(transfer(core,'mercury','saturn','moon',{'mercury':(350,1),'saturn':(70,.1),'moon':(0,13)}) is None,
            'outside transfer orb')
    require(transfer(core,'mars','saturn','moon',{'mars':(353,1),'saturn':(70,.1),'moon':(0,13)})=='nakta' and
            transfer(core,'mars','venus','saturn',{'mars':(353,1),'venus':(53,1.2),'saturn':(0,.1)}) is None,
            'translation and direct perfection priority')
    require(transfer(core,'moon','mars','saturn',{'moon':(359.9,13),'mars':(52,1),'saturn':(0,.1)})=='yamaya',
            'slower collection')
    require(return_place('sidereal-lahiri','A','B')=='A' and return_place('sidereal-lahiri','A','B','birthplace')=='B'
            and return_place('sidereal-lahiri',None,'B') is None, 'return site')
    try:
        return_place('tropical','A','B')
    except ValueError:
        pass
    else:
        raise AssertionError('accepted tropical return')
    v = read('examples/annual-return-v1.yaml')
    policy = read('vedic/annual-chart/conventions.yaml')
    for key, spec in policy['yogas'].items():
        rule = rules[spec['reading']]
        require(rule['rule']==spec['formation'] and rule['exceptions'] and set(rule['user_text'])=={'en','kn','hi'},key)
    require(len(policy['yogas'])==16, 'annual yoga count')
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags=swe.FLG_MOSEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    longitude=lambda jd: swe.calc_ut(jd,swe.SUN,flags)[0][0]
    t=v['return_jd']
    require(abs(solar_return(v['target_sidereal_deg'],longitude,t-1,t+1)-t)<1e-6,'V1 return root')
    lat,lon=v['coordinates']
    asc=swe.houses_ex(t,lat,lon,b'W',swe.FLG_SIDEREAL)[1][0]
    pos={g:swe.calc_ut(t,getattr(swe,g.upper()),flags)[0][::3] for g in v['planet_longitude_and_daily_speed']}
    require(abs(asc-v['ascendant_deg'])<.001 and all(abs(pos[g][0]-old[0])<.002 for g,old in
            v['planet_longitude_and_daily_speed'].items()), 'V1 residence angles and planets')
    strength=read('vedic/annual-chart/strength.yaml')
    for terms in strength['panchavargiya']['term_end_exclusive']:
        stops=[end for _,end in terms]
        require(len(set(g for g,_ in terms))==5 and stops==sorted(set(stops)) and stops[-1]==30, 'Hadda bounds')
    m,c,w=election(policy,strength['panchavargiya'],v['natal_lagna_sign_index'],v['completed_years'],asc,v['sect'],pos)
    require((m,c,w)==(v['muntha_sign_index'],v['candidates'],v['varsheshwara']),'V1 election')
    require(year_lord(['sun','moon'],['sun','moon'],{'sun':10,'moon':10},'mars') is None and
            year_lord(['sun'],[],{},'mars')=='mars','election tie and fallback')
    a,b=v['selected_contact']
    hit=contact(core,a,b,pos)
    require(hit['state']=='applying' and isclose(hit['error'],v['aspect']['error'],abs_tol=.002) and
            (int(pos[a][0]//30)-int(pos[b][0]//30))%12 not in (hit['angle']//30,12-hit['angle']//30),
            'V1 cross-sign application')
    for operands in read('vedic/annual-chart/sahams.yaml')['day_operands'].values():
        require(len(operands)==3 and all(g in {*pos,'lagna','punya'} for g in operands),'saham operands')
    require(saham(10,350,0)==20 and saham(10,350,20)==70 and saham(None,350,20) is None,'corrected lot')
    periods=read('vedic/annual-chart/periods.yaml')
    harsha_table=strength['harsha']
    require(harsha(harsha_table,'sun',9,True,'day')==15 and harsha(harsha_table,'sun',3,False,'night')==0 and
            harsha(harsha_table,'moon',3,None,'night') is None,'Harsha independent awards')
    seq=read(periods['mudda']['sequence'])['lord_order']
    years=dict(zip(seq,[7,20,6,10,7,18,16,19,17]))
    schedule=mudda(years,'ketu',1,.25)
    require(schedule[0]==('venus',0,45) and schedule[-1]==('venus',345,360) and
            mudda(years,None,1,0) is None,'Mudda rotating year and birth balance')
    clock=periods['patyayini']['days']
    series=patyayini({'sun':30,'moon':45,'lagna':25},clock)
    require(periods['mudda']['days']==360 and series[-1][2]==clock and len(series)==2 and
            patyayini({'sun':0},clock) is None,'annual clocks')
    print('KB-52 passed: sidereal V1, residence election, sixteen yogas, mean-orb motion and two annual clocks.')


def check_natal(read,rules,require):
    n=read('examples/natal-star-n1.yaml')
    for actor in ('moon','lagna'):
        row=star_reading(rules,actor,n[actor+'_sidereal_deg']*60)
        require(list(row[:4])==[n[actor][k] for k in ('star','pada','lord','navamsha')] and
                row[4][0]==n[actor]['user_text'],actor+' N1')
    for i in range(108):
        for actor in ('moon','lagna'):
            require(star_reading(rules,actor,i*200)[1]==1+i%4,'quarter start')
    require(star_reading(rules,'moon',21600)==star_reading(rules,'moon',0) and
            star_reading(rules,'lagna',42,False) is None,'stellar wrap and stability')
    for name,count in [('jagradadi',3),('deeptadi',9),('lajjitadi',6),('shayanadi',12)]:
        states=read('vedic/avasthas/'+name+'.yaml')
        require(len(states['states'])==count and set(states['copy'])=={'en','kn','hi'},name)
    require(n['avastha']['dignity']=='own' and n['avastha']['jagradadi']=='jagrat','N1 wakeful state')
    table=read('vedic/strength/vimshopaka/weights.yaml')
    for scheme,num in [('shadvarga',6),('saptavarga',7),('dashavarga',10),('shodashavarga',16)]:
        weights=table['weights'][scheme]
        require(len(weights)==num and sum(weights.values())==20 and min(weights.values())>0,scheme)
        for dignity,expected in [('enemy',(7,'modest')),('neutral',(10,'steady')),('friend',(15,'well supported'))]:
            require(vimshopaka(table,scheme,dict.fromkeys(weights,dignity))==expected,scheme+' bands')
        require(vimshopaka(table,scheme,{}) is None,scheme+' missing')
    require(vimshopaka(table,'shadvarga',n['shadvarga'])==(n['admin_units'],n['user_words']),'N1 band')
    names=read('vedic/vargas/d60-deities.yaml')['names']
    require(len(names)==60 and deity(names,0,'A',True)==deity(names,59.99,'A',True)==names[0] and
            deity(names,30,'A',True)==names[-1] and deity(names,.5,'A',True)==names[1] and
            deity(names,.5,'B',True) is None and deity(names,None,'A',True) is None,'D60 private index')
    groups=read('vedic/muhurta/activity-factors.yaml')['nakshatra_groups']
    stars=list(chain.from_iterable(groups.values()))
    require(len(groups)==7 and len(stars)==len(set(stars))==27 and
            all('vedic.nakshatras.'+k in rules for k in stars),'seven day groups')
    print('KB-53 passed: N1, both actors at all 108 quarter starts, four states tables, four strength tables and D60 gates.')


def advanced_points(read, require):
    """Check admin-only calculations independently at wrap and division edges."""
    advanced=read('vedic/vargas/advanced.yaml')
    push=advanced['pushkara']
    for idx,cut in enumerate(push['bhaga_degree_one_based']):
        contains=lambda longitude: int(longitude%30)==cut-1
        require(contains(idx*30+cut-1) and not contains(idx*30+cut), 'Pushkara degree edge')
    require(len(push['bhaga_degree_one_based'])==12 and
            all(len(set(group))==2 for group in push['navamsha_parts_by_element'].values()),'Pushkara tables')
    gand=advanced['gandanta']
    at_joint=lambda x: x is not None and any(abs((x-j+180)%360-180)<gand['halfwidth_deg'] for j in gand['joints_deg'])
    require(at_joint(359.99) and at_joint(120) and not at_joint(5) and not at_joint(None),'gandanta edge')
    points=read('vedic/upagrahas/points.yaml')
    require(len(points['solar_offsets'])==5 and points['visibility']=='admin-only','solar points visibility')
    for sun in (0,240,359.99):
        dhuma=(sun+400/3)%360
        vyatipata=(-dhuma)%360
        parivesha=(vyatipata+180)%360
        indrachapa=(-parivesha)%360
        upaketu=(indrachapa+50/3)%360
        require(isclose(upaketu,(sun-30)%360,abs_tol=1e-9),'solar point chain')
    special=read('vedic/special-lagnas/calculations.yaml')
    require(set(special['definitions'])==set('hora ghati bhava sree indu pranapada varnada'.split()) and
            special['release']=='post-mvp','special point inventory')
    kerala=read('vedic/prashna/kerala-study.yaml')
    require(kerala['visibility']=='admin-only' and all(k in kerala for k in ('trisphuta','badhaka','ashtamangala')),
            'Kerala private observation profiles')


def check_state_witnesses(read, require):
    """Exercise independent causes, including conjunction and aspect overlaps."""
    def waking(dignity):
        if dignity in ('own','exalted','moolatrikona'):
            return 'jagrat'
        if dignity in ('friend','great-friend','neutral'):
            return 'swapna'
        if dignity in ('enemy','great-enemy','debilitated'):
            return 'sushupti'
        return None

    def brilliance(dignity, with_malefic, combust):
        state = {'exalted':'deepta','own':'swastha','great-friend':'pramudita','friend':'shanta',
                 'neutral':'dina','enemy':'duhkita','great-enemy':'khala'}.get(dignity)
        if None in (dignity,with_malefic,combust):
            return None
        result = {state} if state else set()
        if with_malefic:
            result.add('vikala')
        if combust:
            result.add('kopa')
        return result

    def disposition(dignity, house, water, joins, enemy_contact, enemy_aspect, benefic_aspect, friend_contact):
        if None in (dignity,house,water,joins,enemy_contact,enemy_aspect,benefic_aspect,friend_contact):
            return None
        causes = {'lajjita':house==5 and bool(joins & {'rahu','ketu','saturn','mars'}),
                  'garvita':dignity in ('exalted','moolatrikona'),
                  'kshudhita':dignity=='enemy' or enemy_contact or 'saturn' in joins,
                  'trishita':water and enemy_aspect and not benefic_aspect,
                  'mudita':dignity=='friend' or friend_contact or 'jupiter' in joins,
                  'kshobhita':'sun' in joins and (enemy_aspect or enemy_contact)}
        return {k for k, present in causes.items() if present}

    def numbered_state(star,graha,division,moon_star,ghati,rising):
        if None in (star,graha,division,moon_star,ghati,rising):
            return None
        return 1+(star*graha*division + moon_star + int(ghati) + rising - 1)%12

    require(waking('own')=='jagrat' and waking('neutral')=='swapna' and waking('debilitated')=='sushupti'
            and waking(None) is None,'waking states and unbound dignity')
    tested=set()
    for dignity in ('exalted','own','great-friend','friend','neutral','enemy','great-enemy'):
        tested.update(brilliance(dignity,True,True))
    require(tested==set(read('vedic/avasthas/deeptadi.yaml')['states']) and brilliance('own',False,False)=={'swastha'}
            and brilliance(None,False,True) is None,'independent brilliance witnesses')
    require(disposition('exalted',5,True,{'saturn','sun','jupiter'},False,True,False,False)==
            set(read('vedic/avasthas/lajjitadi.yaml')['states']) and
            disposition('neutral',1,False,set(),False,False,False,False)==set() and
            disposition(None,1,False,set(),False,False,False,False) is None,'overlapping disposition causes')
    require({numbered_state(1,1,1,1,h,1) for h in range(12)}==
            set(read('vedic/avasthas/shayanadi.yaml')['states'].values()) and numbered_state(1,1,1,1,9,1)==12 and
            numbered_state(1,1,1,1,10,1)==1 and numbered_state(1,1,1,1,None,1) is None,'Shayanadi remainder')
