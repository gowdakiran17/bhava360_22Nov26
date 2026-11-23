"""Compare executable varga rules with the independently stored sign lookup rows."""
from bisect import bisect_right
from fractions import Fraction


def calculate(calc, longitude, signs):
    natal, within = divmod(longitude % 360, 30)
    natal = int(natal)
    parity = natal % 2
    side = ('odd', 'even')[parity]
    if 'bands' in calc:
        index = bisect_right(calc['bands'][side], within) - 1
        return calc['by_parity'][side][index]
    part = int(within * calc['parts'] // 30)
    if 'by_parity' in calc:
        return calc['by_parity'][side][part]
    seed = calc['seed']
    if seed == 'natal':
        start = natal
    elif seed == 'natal_plus_parity_offset':
        start = natal + calc['offsets'][parity]
    elif seed == 'natal_plus_modality_offset':
        start = natal + calc['offsets'][natal % 3]
    else:
        group = {'element_sign': natal % 4, 'modality_sign': natal % 3, 'parity_sign': parity}[seed]
        start = signs.index(calc['starts'][group])
    return signs[(start + calc['stride'] * part) % 12]


def validate_vargas(rules, read, require):
    methods = read('vedic/vargas/methods.yaml')['methods']
    fixture = read('examples/varga-sweep.yaml')
    signs = [r['id'] for r in read('vedic/signs/catalog.yaml')['signs']]
    grid = range(fixture['start_degree'], fixture['stop_degree_exclusive'], fixture['step_degree'])
    require(fixture['synthetic'] is True and fixture['fixture']=='Asha' and grid==range(360), 'synthetic degree grid')
    epsilon = Fraction(fixture['boundary_offset_arcseconds'], 3600)
    require(epsilon == Fraction(1,3600), 'one arcsecond boundary probe')
    factors = [1,2,3,4,7,9,10,12,16,20,24,27,30,40,45,60]
    sixteen = [3.5,1,1,.5,.5,3,.5,.5,2,.5,.5,.5,1,.5,.5,4]
    ten = [3,1.5,1.5,0,1.5,1.5,1.5,1.5,1.5,0,0,0,1.5,0,0,5]
    require(sum(sixteen)==sum(ten)==20, 'Vimshopaka normalization')
    require([m['chart'] for m in methods]==[f'D{n}' for n in factors], 'sixteen method rows')
    records = {r['id']:r for r in rules.values() if r['system']=='vedic' and r['topic']=='vargas'}
    require(set(records)=={f'vedic.vargas.d{n}-placement' for n in factors}, 'sixteen varga entries')
    checked = 0
    for n,m,w16,w10 in zip(factors, methods, sixteen, ten):
        rid = f'vedic.vargas.d{n}-placement'
        rule = records[rid]
        v = rule['varga']
        calc = v['calculation']
        require(v['method_id']==m['id'] and v['vimshopaka_points']==dict(shodasavarga=w16,dashavarga=w10), rid)
        require(v['whole_sign_houses'] and all(f'vedic.houses.house-{h}' in rules for h in v['whole_sign_houses']), rid+' houses')
        require(rule['conditions']=={'all':[{'fact':f'varga.d{n}.verified_placement','op':'eq','value':True}]},rid+' placement gate')
        if n == 60:
            require(m['read_access']=='held',rid+' held method')
        boundaries = m['degree_boundaries']
        require(set(m['sign_lookup'])==set(signs), rid+' lookup coverage')
        if n != 30:
            require(boundaries=={'equal_parts':n,'sign_span_arcsec':108000} and calc['parts']==n,rid+' division count')
        for natal, source in enumerate(signs):
            origin = 30*natal
            edges = (boundaries[('odd','even')[natal%2]] if n==30 else
                     [Fraction(30*i,n) for i in range(n+1)])
            row = m['sign_lookup'][source]
            require(len(row)==(5 if n==30 else n) and len(row)==len(edges)-1 and edges[0]==0 and edges[-1]==30 and
                    all(a<b for a,b in zip(edges,edges[1:])), rid+' reference partitions')
            # Bind expected signs to intervals in the static reference. Probe edges from
            # within each interval so both sides are tested even at adjacent sign seams.
            for i,(lo,hi) in enumerate(zip(edges,edges[1:])):
                probes = {lo,lo+epsilon,hi-epsilon}
                probes.update(d-origin for d in grid[origin:origin+30] if lo <= d-origin < hi)
                for offset in probes:
                    got = calculate(calc,Fraction(origin+offset),signs)
                    require(got==row[i],f'{rid} at {source} {offset}°: {got}, expected {row[i]}')
                checked += len(probes)
        require(calculate(calc,Fraction(360),signs)==m['sign_lookup'][signs[0]][0],rid+' zodiac wrap')
    print(f'{checked} synthetic varga sign comparisons passed across 16 charts, including every whole degree and division boundary.')
