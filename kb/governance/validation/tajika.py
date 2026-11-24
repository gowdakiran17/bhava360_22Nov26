"""Annual-chart and question-chart reference mathematics. All positions are in degrees."""
from math import isfinite

def sign_ray(x, y):
    offset = (int(y % 360 // 30) - int(x % 360 // 30)) % 12
    if offset in (1, 5, 7, 11):
        return None
    ray = offset * 30
    return min(ray, 360-ray), (y-x-ray+180) % 360-180


def contact(core, first, second, positions):
    if first == second or any(g not in core['orb_degrees'] or not positions.get(g) for g in (first,second)):
        return None
    if any(v is None or not isfinite(v) for g in (first,second) for v in positions[g]):
        return None
    (x,v),(y,w) = positions[first],positions[second]
    ray = sign_ray(x,y)
    if ray is None:
        return None
    angle,error = ray
    limit = (core['orb_degrees'][first]+core['orb_degrees'][second])/2
    if abs(error)>limit:
        return None
    slope = w-v
    state = 'exact' if error==0 else 'stationary' if slope==0 else 'applying' if error*slope<0 else 'separating'
    return dict(angle=angle,error=error,orb=limit,state=state,days=-error/slope if state=='applying' else None)


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

def year_lord(candidates, aspects, scores, muntha_lord, moon_replacement=None):
    if not candidates or None in candidates or aspects is None:
        return None
    pool = set(candidates) & aspects.keys() or set(candidates)
    if any(scores.get(g) is None for g in pool):
        return None
    ranks = {g:(scores[g], aspects.get(g,0), g==muntha_lord) for g in pool}
    best = max(ranks.values())
    winners = [g for g in pool if ranks[g]==best]
    if len(winners)!=1:
        return None
    winner = winners[0]
    if winner=='moon':
        return moon_replacement if moon_replacement!='moon' else None
    return winner


def moon_successor(core, pos):
    if any(not pos.get(g) or None in pos[g] for g in core['orb_degrees']):
        return None
    hits = [(h['days'],g) for g in core['orb_degrees'] if g!='moon'
            and (h:=contact(core,'moon',g,pos)) and h['state']=='applying']
    if hits:
        first = min(t for t,_ in hits)
        partners = [g for t,g in hits if t==first]
        return partners[0] if len(partners)==1 else None
    ruler = RULERS[int(pos['moon'][0]%360//30)]
    return ruler if ruler!='moon' else None


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

def election(policy, core, table, natal_sign, years, asc, sect, pos):
    if None in (asc,natal_sign,years) or sect not in policy['triplicity'] or any(
            not pos.get(g) or None in pos[g] for g in core['orb_degrees']):
        return None, None, None
    sign = int(asc % 360 // 30)
    muntha = (natal_sign + years) % 12
    luminary = 'sun' if sect == 'day' else 'moon'
    candidates = [RULERS[natal_sign], RULERS[sign], RULERS[muntha],
                  RULERS[int(pos[luminary][0] // 30)], policy['triplicity'][sect][sign]]
    aspects = {}
    for g in set(candidates):
        ray = sign_ray(pos[g][0], asc)
        if ray is not None:
            aspects[g] = policy['aspect_strength']['by_angle'][ray[0]]
    strengths = {g: five_strength(table, g, pos) for g in candidates}
    return muntha, candidates, year_lord(candidates, aspects, strengths, RULERS[muntha], moon_successor(core,pos))


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
