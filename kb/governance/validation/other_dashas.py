"""Reference calculations in exact years relative to birth; convert only at display."""
from fractions import Fraction as F
from itertools import accumulate
from vimshottari import instant, stamp

ROOT = 'vedic/dashas/'
SIGNS = 'aries taurus gemini cancer leo virgo libra scorpio sagittarius capricorn aquarius pisces'.split()
LORDS = 'mars venus mercury moon sun mercury venus mars jupiter saturn saturn jupiter'.split()
EXALT = dict(sun=0,moon=1,mars=9,mercury=5,jupiter=3,venus=11,saturn=6)


def split(start, duration, labels, weights):
    total = sum(weights)
    return [(name,start+duration*F(end-w,total),start+duration*F(end,total))
            for name,w,end in zip(labels,weights,accumulate(weights)) if w]


def rotate(items, i):
    return items[i:]+items[:i]


def contains(rows, at):
    return next(row for row in rows if row[1]<=at<row[2])


def ashtottari_eligible(cfg, chart, gate):
    if gate=='universal':
        return True
    if gate=='fortnight':
        if chart.get('daybirth') is None or chart.get('waxing') is None:
            return None
        return chart['daybirth'] != chart['waxing']
    if gate!=cfg['default_gate']:
        raise ValueError('unknown Ashtottari applicability profile')
    lagna, planets = chart.get('lagna'),chart.get('positions',{})
    if lagna is None or 'rahu' not in planets or LORDS[lagna] not in planets:
        return None
    rahu = planets['rahu']
    return rahu!=lagna and (rahu-planets[LORDS[lagna]])%12+1 in cfg['eligible_distances']


def lunar(system,cfg,chart,at):
    moon = F(chart['moon_arcseconds'])%(360*3600)
    if system=='yogini':
        labels = cfg['lord_order']
        weights = [cfg['sequence'][l] for l in labels]
        star,used = divmod(moon,cfg['star_width_arcseconds'])
        i = (star+3)%8  # zero-based equivalent of one-based star + 3, zero remainder = eighth
        fraction = used/cfg['star_width_arcseconds']
        shift = 0
    else:
        if ashtottari_eligible(cfg,chart,chart.get('ashtottari_gate',cfg['default_gate'])) is not True:
            return None
        labels,weights = cfg['order'],cfg['years']
        edges = cfg['arc_edges_minutes']
        arc = moon/60
        if arc<edges[0]:
            arc+=21600
        i = next(j for j in range(8) if edges[j]<=arc<edges[j+1])
        fraction = (arc-edges[i])/(edges[i+1]-edges[i])
        shift = 1
    start = -fraction*weights[i]
    cycle = cfg['cycle_years']
    start += ((at-start)//cycle)*cycle
    major = contains(split(start,cycle,rotate(labels,i),rotate(weights,i)),at)
    lord,left,right = major
    j = (labels.index(lord)+shift)%len(labels)
    return major,contains(split(left,right-left,rotate(labels,j),rotate(weights,j)),at)


def drishti(src,dst):
    if src==dst:
        return True
    if src%3==2:
        return dst%3==2
    return (src%3,dst%3) in ((0,1),(1,0)) and (src-dst)%12 not in (1,11)


class SignChart:
    def __init__(self, chart, even):
        self.pos = chart['positions']
        self.degree = chart['degree_in_sign']
        self.even = {SIGNS.index(s) for s in even}

    def years(self, sign, lord):
        pos = self.pos[lord]
        basic = ((sign-pos if sign in self.even else pos-sign)%12) or 12
        if lord not in EXALT:
            return basic
        return basic + (pos==EXALT[lord]) - (pos==(EXALT[lord]+6)%12)

    def support(self, sign, lord):
        return sum(drishti(self.pos[g],sign) for g in ('jupiter','mercury',lord))

    def owner(self, sign, *, for_period=True):
        usual = LORDS[sign]
        if sign not in (7,10):
            return usual
        other = 'ketu' if sign==7 else 'rahu'
        a,b = self.pos[usual],self.pos[other]
        if a==sign:
            return usual if b==sign else other
        if b==sign:
            return usual
        def rank(g):
            s = self.pos[g]
            progress = self.degree[g]
            if g in ('rahu','ketu'):
                progress = 30-progress
            final = self.years(sign,g) if for_period else progress
            return (list(self.pos.values()).count(s),self.support(s,LORDS[s]),s==EXALT.get(g),
                    s%3,final)
        if rank(usual)==rank(other):
            raise ValueError('co-lord evidence tied')
        return max((usual,other),key=rank)

    def stronger(self, sign):
        def rank(s):
            lord = self.owner(s)
            d = self.degree[lord]
            return (list(self.pos.values()).count(s),self.support(s,lord),
                    any(self.pos[g]==s==e for g,e in EXALT.items()),
                    s%2!=self.pos[lord]%2,s%3,30-d if lord in ('rahu','ketu') else d)
        opposite = (sign+6)%12
        if rank(sign)==rank(opposite):
            raise ValueError('sign strength tied')
        return max((sign,opposite),key=rank)

    def direction(self,seed,direction):
        if self.pos['saturn']==seed:
            return 1
        return -direction if self.pos['ketu']==seed else direction


def sign_path(system,cfg,chart,at):
    c = SignChart(chart,cfg['even_footed'])
    seed = chart['lagna'] if system=='chara' else c.stronger(chart['lagna'])
    direction = -1 if (seed+8)%12 in c.even else 1
    offsets = range(12)
    if system=='narayana':
        direction = c.direction(seed,direction)
        if c.pos['saturn']!=seed:
            offsets = cfg['normal_offsets'][('movable','fixed','dual')[seed%3]]
    order = [(seed+direction*i)%12 for i in offsets]
    if at<0:
        raise ValueError('sign period starts at birth')
    cursor = F(0)
    durations = {}
    passes = cfg['cycles'] if system=='chara' else 2
    for cycle in range(passes):
        for sign in order:
            if cycle==0:
                durations[sign] = c.years(sign,c.owner(sign))
                if system=='narayana':
                    durations[sign] = min(durations[sign],cfg['first_pass_max_years'])
            span = durations[sign] if cycle==0 else 12-durations[sign]
            if span<0:
                raise ValueError('invalid duration under selected strength profile')
            if cursor <= at < cursor+span:
                break
            cursor += span
        else:
            continue
        break
    else:
        raise ValueError('outside defined sign-dasha sequence')
    major = sign,cursor,cursor+span
    s,left,right = major
    if system=='chara':
        step = 1 if SIGNS[s] in cfg['antar_forward'] else -1
        first = (s+step)%12
    else:
        strong = c.stronger(s)
        first = c.pos[c.owner(strong)]
        step = c.direction(strong,1 if first%2==0 else -1)
    sub = contains(split(left,right-left,[(first+step*i)%12 for i in range(12)],[1]*12),at)
    return (SIGNS[s],left,right),(SIGNS[sub[0]],*sub[1:])


def wheel(cfg,chart,at,role):
    if role!='admin':
        return None
    star,arc = divmod(F(chart['moon_arcseconds'])%1296000,cfg['star_width_arcseconds'])
    pada,used = divmod(arc,cfg['pada_width_arcseconds'])
    group = next(g for g,d in cfg['groups'].items() if star+1 in d['stars_one_based'])
    sister = group[:-1]+('2' if group.endswith('1') else '1')
    stream = [s for g in (group,sister) for row in cfg['groups'][g]['padas'] for s in row]
    stream = rotate(stream,9*pada)
    years = cfg['sign_years']
    start = -used/cfg['pada_width_arcseconds']*sum(years[s] for s in stream[:9])
    elapsed = -start
    index = next(i for i,total in enumerate(accumulate(years[s] for s in stream[:9])) if elapsed<total)
    start += sum(years[s] for s in stream[:index])
    stream = rotate(stream,index)
    major = contains(split(start,sum(years[s] for s in stream[:9]),list(range(9)),[years[s] for s in stream[:9]]),at)
    i,left,right = major
    children = stream[i:i+9]
    return (stream[i],left,right),contains(split(left,right-left,children,[years[s] for s in children]),at)


def junction(outgoing,incoming,query_start,query_end):
    if outgoing[2]!=incoming[1]:
        raise ValueError('junction requires adjacent sibling intervals')
    edge = incoming[1]
    return edge if query_start<=edge<query_end else None


def validate_other_dashas(rules, read, evaluate, require):
    fixtures = read('examples/other-dashas-reference.yaml')
    require(fixtures['synthetic'] is True and set(fixtures['charts'])=={'Asha','Ravi'},'synthetic dasha fixtures')
    year_days = read(ROOT+'vimshottari/periods.yaml')['year_days']
    # These five systems use the two clocks in their existing reference tables.
    clocks = {name: year_days[name] for name in ('mean-gregorian', 'savana')}
    require(sum(read(ROOT+'ashtottari/periods.yaml')['years'])==108 and
            sum(read(ROOT+'yogini/periods.yaml')['sequence'].values())==36,'lunar cycle totals')
    checked = 0
    for name,chart in fixtures['charts'].items():
        for system,case in chart['reference'].items():
            cfg = read(ROOT+system+'/periods.yaml')
            at = F(case['query_years_after_birth'])
            if system in ('yogini','ashtottari'):
                path = lunar(system,cfg,chart,at)
            elif system=='kalachakra':
                path = wheel(cfg,chart,at,'admin')
                require(wheel(cfg,chart,at,'tester') is None,'private Kalachakra')
            else:
                path = sign_path(system,cfg,chart,at)
            for clock,expected in case['dates'].items():
                year = F(clocks[clock])*86400
                for row,ref in zip(path,expected,strict=True):
                    actual = [row[0],stamp(instant(chart['birth'])+row[1]*year),stamp(instant(chart['birth'])+row[2]*year)]
                    require(actual==ref,f'{name} {system} {clock}: {actual} vs {ref}')
                    checked+=1
            require(set(case['dates'])==set(clocks),system+' clocks')
        require(set(chart['reference'])=={'yogini','ashtottari','chara','narayana','kalachakra'},'system coverage')
    a = fixtures['charts']['Asha']
    cfg = read(ROOT+'ashtottari/periods.yaml')
    require(ashtottari_eligible(cfg,{},cfg['default_gate']) is None,'unknown eligibility')
    require(lunar('ashtottari',cfg,{**a,'positions':{**a['positions'],'rahu':a['lagna']}},0) is None,'Rahu in Lagna')
    for day in (True,False):
        for waxing in (True,False):
            require(ashtottari_eligible(cfg,dict(daybirth=day,waxing=waxing),'fortnight')==(day!=waxing),'alternate gate')
    cfg = read(ROOT+'yogini/periods.yaml')
    old = lunar('yogini',cfg,a,0)[0]
    new = lunar('yogini',cfg,a,old[2])[0]
    boundary = junction(old,new,old[2],old[2]+1)
    require(boundary==new[1] and junction(old,new,old[2]-1,old[2]) is None,'junction edge ownership')
    for clock,expected in fixtures['sandhi_utc'].items():
        require(stamp(instant(a['birth'])+boundary*F(clocks[clock])*86400)==expected,'junction UTC')
    # Verify a partial quarter that starts inside a later occurrence of Scorpio (Rao example 95).
    cfg = read(ROOT+'kalachakra/periods.yaml')
    scorpio,sub = wheel(cfg,{'moon_arcseconds':165000},F(0),'admin')
    require(scorpio==('scorpio',F(-9,4),F(19,4)),'partial Kalachakra pada')
    require(sub[1]<=0<sub[2],'child spanning birth in partial Kalachakra pada')
    require(wheel(cfg,{'moon_arcseconds':165000},F(19,4),'admin')[0][0]=='libra','Kalachakra occurrence continuation')
    for group in cfg['groups'].values():
        require(len(group['padas'])==4 and all(len(row)==9 for row in group['padas']), 'four Kalachakra padas')
    stars = [i for group in cfg['groups'].values() for i in group['stars_one_based']]
    require(sorted(stars)==list(range(1,28)),'Kalachakra star partition')
    r = fixtures['charts']['Ravi']
    require(sign_path('chara',read(ROOT+'chara/periods.yaml'),r,F(1))[0][0]=='aries','reverse Chara succession')
    require(sign_path('narayana',read(ROOT+'narayana/periods.yaml'),r,F(9))[0][0]=='gemini','fixed Narayana sixth-step progression')
    gate = rules['vedic.dashas-kalachakra.pada-wheel']['conditions']
    require(evaluate(gate,{'dasha.kalachakra.pada_wheel':True,'dasha.access.admin':False}) is False,'admin rule gate')
    print(f'Other dashas: {checked} synthetic major/subperiod date intervals, both junction clocks and eligibility gates passed.')
