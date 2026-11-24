"""Annual-chart and question-chart reference mathematics. All positions are in degrees."""
from math import isfinite

def contact(core, first, second, positions):
    """Choose the nearest directed aspect ray and follow its signed residual."""
    if first==second or any(g not in core['orb_degrees'] or g not in positions for g in (first,second)):
        return None
    if any(positions[g] is None or any(v is None or not isfinite(v) for v in positions[g]) for g in (first,second)):
        return None
    (x,v),(y,w)=positions[first],positions[second]
    rays={sign*angle for angle in core['angles'] for sign in (-1,1)}
    error,ray=min(((((y-x-angle+180)%360)-180,angle) for angle in rays),key=lambda pair:(abs(pair[0]),pair[1]))
    limit=(core['orb_degrees'][first]+core['orb_degrees'][second])/2
    if abs(error)>limit:return None
    slope=w-v
    state='exact' if error==0 else 'stationary' if slope==0 else 'applying' if error*slope<0 else 'separating'
    return dict(angle=abs(ray),error=error,orb=limit,state=state,days=-error/slope if state=='applying' else None)

def transfer(core, a, b, bridge, pos):
    if len({a,b,bridge})!=3 or any(not pos.get(g) or None in pos[g] for g in (a,b,bridge)):return None
    direct=contact(core,a,b,pos)
    if direct and direct['state'] in ('applying','exact'):return None
    pair=[contact(core,bridge,g,pos) for g in (a,b)]
    if not all(pair):return None
    v=abs(pos[bridge][1])
    others=[abs(pos[g][1]) for g in (a,b)]
    states={p['state'] for p in pair}
    if v>max(others) and states=={'applying','separating'}:return 'nakta'
    if v<min(others) and states=={'applying'}:return 'yamaya'

def return_place(frame,residence,birthplace,variant='residence'):
    if frame!='sidereal-lahiri':raise ValueError('Tajika requires a Lahiri sidereal return')
    if variant not in ('residence','birthplace'):raise ValueError('unknown annual location policy')
    return residence if variant=='residence' else birthplace

def solar_return(target,longitude,lo,hi):
    """Bracket one forward crossing around the anniversary; wrap at zero Aries."""
    residual=lambda t:(longitude(t)-target+180)%360-180
    if not residual(lo)<=0<=residual(hi):raise ValueError('return is not bracketed')
    for _ in range(48):
        mid=(lo+hi)/2
        if residual(mid)<0:lo=mid
        else:hi=mid
    return (lo+hi)/2

def year_lord(candidates,aspected,scores,muntha_lord):
    if any(v is None for v in candidates) or aspected is None:return None
    eligible=set(candidates)&set(aspected)
    if not eligible:return muntha_lord
    if any(scores.get(g) is None for g in eligible):return None
    top=max(scores[g] for g in eligible)
    winners=[g for g in eligible if scores[g]==top]
    return winners[0] if len(winners)==1 else None

def saham(a,b,c):
    if None in (a,b,c):return None
    return (a-b+c+(30 if (c-b)%360>(a-b)%360 else 0))%360

def patyayini(positions,year):
    if not positions or any(x is None for x in positions.values()):return None
    ordered=sorted(positions,key=lambda g:positions[g]%30)
    last=positions[ordered[-1]]%30
    if not last:return None
    start=0
    periods=[]
    for g in ordered:
        end=year*(positions[g]%30)/last
        if end>start:periods.append((g,start,end))
        start=end
    return periods

RULERS = 'mars venus mercury moon sun mercury venus mars jupiter saturn saturn jupiter'.split()
FALL = dict(sun=190, moon=213, mars=118, mercury=345, jupiter=275, venus=177, saturn=20)

def five_strength(table, planet, positions):
    """Tajika sign relation is evaluated between the guest and the term/division host."""
    if any(positions.get(g) is None for g in FALL):
        return None
    x = positions[planet][0] % 360
    sign = int(x // 30)
    term = next(host for host, stop in table['term_end_exclusive'][sign] if x % 30 < stop)
    hosts = dict(sign=RULERS[sign], term=term, decan=RULERS[(sign + 4 * int(x % 30 // 10)) % 12],
                 navamsha=RULERS[int(x * 3 // 10) % 12])
    total = 20 * abs((x - FALL[planet] + 180) % 360 - 180) / 180
    for division, host in hosts.items():
        house = (int(positions[host][0] // 30) - sign) % 12 + 1
        relation = ('own' if host == planet else 'friendly' if house in (3, 5, 9, 11)
                    else 'hostile' if house in (1, 4, 7, 10) else 'neutral')
        total += table['maxima'][division] * table['relations'][relation]
    return total / 4

def election(policy, table, natal_sign, years, asc, sect, pos):
    sign = int(asc // 30)
    muntha = (natal_sign + years) % 12
    luminary = 'sun' if sect == 'day' else 'moon'
    candidates = [RULERS[natal_sign], RULERS[sign], RULERS[muntha],
                  RULERS[int(pos[luminary][0] // 30)], policy['triplicity'][sect][sign]]
    eligible = [g for g in candidates if (int(pos[g][0] // 30) - sign) % 12 in (0,2,3,4,6,8,9,10)]
    strengths = {g: five_strength(table, g, pos) for g in eligible}
    return muntha, candidates, year_lord(candidates, eligible, strengths, RULERS[muntha])

def reception(a, b, pos):
    if a == b or any(not pos.get(g) or pos[g][0] is None for g in (a,b)):
        return None
    return RULERS[int(pos[a][0] % 360 // 30)] == b and RULERS[int(pos[b][0] % 360 // 30)] == a


def harsha(table, body, house, dignified, sect):
    if None in (house,dignified,sect) or body not in table['favourite_house']:
        return None
    group = 'day' if body in table['day'] else 'night'
    return 5 * sum((house == table['favourite_house'][body], dignified,
                    house in table[group+'_group_houses'], group == sect))


def mudda(sequence, birth_lord, years, elapsed_fraction):
    if birth_lord not in sequence or years is None or elapsed_fraction is None or not 0 <= elapsed_fraction < 1:
        return None
    lords = list(sequence)
    start = (lords.index(birth_lord) + years) % len(lords)
    periods = []
    elapsed = 0
    for i in range(10):
        g = lords[(start+i)%len(lords)]
        portion = 1-elapsed_fraction if i==0 else elapsed_fraction if i==9 else 1
        end = elapsed + sequence[g]*3*portion
        if end>elapsed:
            periods.append((g,elapsed,end))
        elapsed = end
    return periods
