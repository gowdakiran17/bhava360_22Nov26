"""Validate raw and reduced Ashtakavarga separately, retaining each contributor bit."""
import re

DIR = 'vedic/strength/ashtakavarga/'
PREFIX = 'vedic.strength-ashtakavarga.'
PLANETS = 'sun moon mars mercury jupiter venus saturn'.split()
SIGNS = 'aries taurus gemini cancer leo virgo libra scorpio sagittarius capricorn aquarius pisces'.split()


def prastara_for(offsets, natal):
    marks = {}
    for contributor, houses in offsets.items():
        bits = [0]*12
        for house in houses:
            bits[(natal[contributor]+house-1)%12] = 1
        marks[contributor] = bits
    return marks


def co_owned(a, b, occupied_a, occupied_b):
    if min(a,b)==0 or (occupied_a and occupied_b):
        return a,b
    if not (occupied_a or occupied_b):
        low = min(a,b) if a!=b else 0
        return low,low
    if occupied_a:
        return a,a if b>a else 0
    return b if a>b else 0,b


def reduce_row(raw, trines, pairs, occupied):
    trinal = raw.copy()
    for group in trines:
        cutoff = min(raw[j] for j in group)
        for j in group:
            trinal[j] -= cutoff
    reduced = trinal.copy()
    for a,b in pairs:
        reduced[a],reduced[b] = co_owned(trinal[a],trinal[b],a in occupied,b in occupied)
    return trinal,reduced


def pindas(reduced, natal, sign_weights, planet_weights):
    rashi = sum(v*w for v,w in zip(reduced,sign_weights))
    graha = sum(reduced[natal[g]]*w for g,w in zip(PLANETS,planet_weights))
    return [rashi,graha,rashi+graha]


def transit_at(longitude_arcsec, marks, policy, bands):
    longitude = longitude_arcsec % (360*3600)
    sign,within = divmod(longitude,30*3600)
    lord = policy['lords'][within//(policy['width_arcminutes']*60)]
    count = sum(bits[sign] for bits in marks.values())
    tone, = [tone for tone,(lo,hi) in bands.items() if lo<=count<=hi]
    return lord,marks[lord][sign],tone


def validate_ashtakavarga(rules,read,evaluate,require):
    records = {rid[len(PREFIX):]:r for rid,r in rules.items() if rid.startswith(PREFIX)}
    targets = {g+'-bav' for g in PLANETS}
    require(set(records)==targets|{'sarvashtakavarga','shodhana','shodhya-pinda','kakshya','bindu-support',
                                  'bindu-steady','bindu-take-care'},'Ashtakavarga entry inventory')
    for slug,r in records.items():
        cfg = r['calculation']
        require(cfg['numeric_access']==['admin','tester'],slug+' numeric visibility')
        for t in r['user_text'].values():
            require(not re.search(r'\d|[%٪{}]|\b(?:scores?|points?|bindus?|pinda)\b|अंक|स्कोर|ಬಿಂದು|ಅಂಕ',t,re.I),slug+' public copy')
    table = read(DIR+'bindu.yaml')
    contributors = PLANETS+['lagna']
    totals = [48,49,39,54,56,52,39]
    require(table['contributors']==contributors and set(table['offsets'])==set(PLANETS),'eight contributors')
    expected_total = records['sarvashtakavarga']['calculation']['expected_total']
    require(sum(totals)==expected_total==337,'raw SAV total')
    for g,total in zip(PLANETS,totals):
        cfg = records[g+'-bav']['calculation']
        require(cfg['offset_table']==DIR+'bindu.yaml' and cfg['target']==g,g+' offsets pointer')
        offsets = table['offsets'][g]
        require(set(offsets)==set(contributors) and table['totals'][g]==total,g+' BAV coverage')
        for houses in offsets.values():
            require(houses==sorted(set(houses)) and all(type(h) is int and 1<=h<=12 for h in houses),g+' offsets')
    shodhana = records['shodhana']['calculation']
    reduction = read(shodhana['case_table'])
    pairs = [[SIGNS.index(s.lower()) for s in pair.split('/')] for pair in reduction['same_owner_pairs']]
    trines = shodhana['trines']
    require(shodhana['occupants']==PLANETS and trines==[[i,i+4,i+8] for i in range(4)],'shodhana profile')
    policy = records['shodhya-pinda']['calculation']
    require(policy['weights']==shodhana['case_table'],'pinda table')
    weights = reduction['rashi_weights'][policy['rashi_weight_profile']]
    planet_weights = reduction['graha_weights_sun_through_saturn']
    bands = table['transit_bands']
    require(bands=={'Take care':[0,3],'Steady':[4,4],'Supportive':[5,8]},'raw transit bands')
    kak = records['kakshya']['calculation']
    order = 'saturn jupiter mars sun venus mercury moon lagna'.split()
    require(kak['width_arcminutes']==225 and kak['lords']==order,'kakshya profile')
    for label,slug in [('Supportive','bindu-support'),('Steady','bindu-steady'),('Take care','bindu-take-care')]:
        c = records[slug]['calculation']
        require(c['tone']==label and c['band_table']==DIR+'bindu.yaml',slug)
    tone_rules = [records[k] for k in ('bindu-support','bindu-steady','bindu-take-care')]
    for count in range(9):
        marks = {p:[int(i<count)]*12 for i,p in enumerate(contributors)}
        _,_,band = transit_at(0,marks,kak,bands)
        facts = {'transit.bav.band':band,'transit.bav.supportive':band=='Supportive'}
        selected = [r['calculation']['tone'] for r in tone_rules if evaluate(r['conditions'],facts)]
        require(selected==[band],f'transit rule selection for {count} bindus')
    require(all(evaluate(r['conditions'],{}) is None for r in tone_rules),'unknown transit band')
    fixture = read('examples/ashtakavarga-reference.yaml')
    require(fixture['synthetic'] is True and set(fixture['fixtures'])=={'Asha','Ravi'},'synthetic AV charts')
    example = reduction['worked_example']
    case = fixture['fixtures'][example['fixture']]
    indices = [SIGNS.index(s) for s in example['signs']]
    occupants = [[g for g in PLANETS if case['natal_signs'][g]==i] for i in indices]
    require(example['case']=='one_occupied' and example['case'] in reduction['cases']
            and occupants==example['occupants']==[['sun'],[]], 'Asha Aries/Scorpio case')
    for stage in ('after_trikona','after_ekadhipatya'):
        require(example[stage]==[case[stage][example['target']][i] for i in indices], 'Asha '+stage)
    boundary_count = 0
    for name,case in fixture['fixtures'].items():
        natal = case['natal_signs']
        require(set(natal)==set(contributors) and all(type(v) is int and 0<=v<12 for v in natal.values()),name)
        sav = [0]*12
        for g,total in zip(PLANETS,totals):
            offsets = table['offsets'][g]
            marks = prastara_for(offsets,natal)
            bav = list(map(sum,zip(*marks.values())))
            require(bav==case['bav'][g] and sum(bav)==total,name+' '+g+' BAV')
            sav = [a+b for a,b in zip(sav,bav)]
            first,final = reduce_row(bav,trines,pairs,{natal[p] for p in shodhana['occupants']})
            require(first==case['after_trikona'][g] and final==case['after_ekadhipatya'][g],name+' '+g+' reductions')
            require(pindas(final,natal,weights,planet_weights)==case['pinda'][g],name+' '+g+' pinda')
            for sign,count in enumerate(case['bav'][g]):
                tone = 'Supportive' if count>4 else 'Take care' if count<4 else 'Steady'
                for i,lord in enumerate(order):
                    bit = int((sign-natal[lord])%12+1 in offsets[lord])
                    edge = sign*108000+i*13500
                    for point in (edge,edge+13499):
                        require(transit_at(point,marks,kak,bands)==(lord,bit,tone),name+' '+g+' transit boundary')
                        boundary_count+=1
        require(sav==case['sav'] and sum(sav)==expected_total,name+' raw SAV')
    # Published comparison has an expanded occupancy mask and its own weight variant.
    ref = read(DIR+'pinda-comparison.yaml')
    natal = dict(zip(contributors,ref['origin_indices_zero_based']))
    for i,g in enumerate(PLANETS):
        bav = list(map(sum,zip(*prastara_for(table['offsets'][g],natal).values())))
        _,final = reduce_row(bav,trines,pairs,set(ref['occupied_sign_indices']))
        weighted = pindas(final,natal,reduction['rashi_weights'][ref['rashi_weight_profile']],planet_weights)
        require(weighted[:2]==[ref['reference_rashi'][i],ref['reference_graha'][i]],g+' published pinda')
    print(f"Ashtakavarga passed for both synthetic charts: 168 BAV cells, 24 SAV cells, raw sums 337, "
          f"all reduction and pinda rows, and {boundary_count} kakshya boundary probes.")
