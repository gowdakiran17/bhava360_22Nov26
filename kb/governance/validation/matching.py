"""Compare the named matching profiles with a fixed, independent pair reference."""
import csv

from dosha_charts import pair_facts
from hashlib import sha256
from itertools import product


def star_lookup(groups):
    return {star: key for key, stars in groups.items() for star in stars}


def profile_tables(rules, read):
    north = read('vedic/matching/north-profile.yaml')
    south = read('vedic/matching/south-profile.yaml')['factors']
    records = {k.split('.')[-1]: v['matching'] for k, v in rules.items() if 'matching' in v}
    tables = dict(north=north, south=south, records=records)
    tables['gana'] = star_lookup(dict(enumerate(north['gana_stars'])))
    tables['nadi'] = star_lookup(records['nadi']['stars'])
    tables['rajju'] = star_lookup(south['rajju']['stars'])
    tables['friends'] = [rules['vedic.planets.'+r]['graha']['natural_friendships']['friends']
                        for r in north['lord_order']]
    return tables


def moon(arcsec, tables):
    sign = arcsec // 108000
    star = 1 + arcsec // 48000
    records = tables['records']
    return dict(sign=sign, star=star, pada=1 + arcsec % 48000 // 12000,
                varna=records['varna']['sign_class'][sign],
                vashya=records['vashya']['sign_half_classes'][sign][arcsec % 108000 >= 54000],
                yoni=tables['north']['matrixes']['yoni_star'][star-1],
                gana=tables['gana'][star], lord=records['graha-maitri']['sign_lord'][sign],
                nadi=tables['nadi'][star], rajju=tables['rajju'][star])


def factors(a, b, t):
    matrices = t['north']['matrixes']
    south = t['south']
    records = t['records']
    def lookup(key, matrix):
        return matrices[matrix][a[key]][b[key]]
    forward = 1 + (b['star']-a['star']) % 27
    reverse = 1 + (a['star']-b['star']) % 27
    nadi = records['nadi']
    classes = nadi['class_order']
    tara = records['tara']['remainder_points']
    north = [lookup('varna','varna'), lookup('vashya','vashya'), tara[forward%9]+tara[reverse%9],
             lookup('yoni','yoni'), lookup('lord','lord_friendship'), lookup('gana','gana'),
             records['bhakoot']['sign_pair_points'][a['sign']][b['sign']],
             nadi['points'][classes.index(a['nadi'])][classes.index(b['nadi'])]]
    lords = t['north']['lord_order']
    la, lb = a['lord'], b['lord']
    friendly = la == lb or lords[la] in t['friends'][lb] and lords[lb] in t['friends'][la]
    sign_distance = 1 + (b['sign']-a['sign'])%12
    animals = sorted([a['yoni'],b['yoni']])
    stars = sorted([a['star'],b['star']])
    southern = [forward%9 in south['dina']['inclusive_remainders'],
                south['gana']['accepted'][a['gana']][b['gana']],
                forward in south['mahendra']['inclusive_counts'],
                forward > south['stree-deergha']['inclusive_count_above'],
                all(animals != sorted(pair) for pair in south['yoni']['enemy_pairs']),
                sign_distance in south['rashi']['inclusive_counts'], friendly,
                b['sign']+1 in south['vashya']['column_signs_by_row'][a['sign']],
                a['rajju'] != b['rajju'], stars not in south['vedha']['mutual_obstructions']]
    return north, southern


def qualitative(directions):
    if set(directions) == {'support'}:
        return 'Supportive'
    if set(directions) == {'care'}:
        return 'Take care'
    return 'Steady'


def validate_matching(rules, read, evaluate, require, root):
    validate_summary(read,require)
    t = profile_tables(rules, read)
    policy = read('vedic/matching/factors.yaml')
    north_order = policy['reference']['northern_order']
    south_order = policy['reference']['southern_order']
    for key in south_order:
        require(t['records']['porutham-'+key] == t['south'][key], 'Porutham table '+key)
    def pack(values):
        return ','.join(format(x,'g') for x in values)
    seen = set()
    with (root / policy['reference']['file']).open() as f:
        for row in csv.DictReader(f):
            i,j = int(row['row_star']),int(row['column_star'])
            require((i,j) not in seen,'duplicate matching reference')
            seen.add((i,j))
            results = []
            for q,r in product(range(4),repeat=2):
                a,b = [moon((s-1)*48000 + k*12000 + 6000,t) for s,k in ((i,q),(j,r))]
                n,s = factors(a,b,t)
                if q == r == 0:
                    require([pack(n),pack(s)] == [row['north_at_first_pada'],row['south_at_first_pada']],
                            f'matching base reference {i}/{j}')
                results.append(pack(n+s))
            require(sha256('\n'.join(results).encode()).hexdigest() == row['all_pada_pairs_sha256'],
                    f'matching pada sweep {i}/{j}')
    require(seen == set(product(range(1,28),repeat=2)), 'complete ordered grid')
    for sign,expected in [(8,[1,0]),(9,[0,2])]:
        require([moon(sign*108000+54000+k,t)['vashya'] for k in (-1,0)] == expected,'Vashya half-sign edge')
    fixture = read('examples/matching-reference.yaml')
    require(fixture['synthetic'] and [(c['row'],c['column']) for c in fixture['pairs']]
            == [('Scenario 1','Scenario 2'),('Scenario 3','Scenario 4')], 'synthetic matching identities')
    matching_rules = {k:v for k,v in rules.items() if k.startswith('vedic.matching.')}
    for case in fixture['pairs']:
        a,b = [moon(d*3600,t) for d in case['moon_degrees']]
        n,s = factors(a,b,t)
        require(n == case['north'] and s == case['south'],f"{case['row']} independent values: {n} {s}")
        kb10 = pair_facts(*case['moon_degrees'],fixture['apply_kb10_parihara'],
                          read('vedic/signs/catalog.yaml')['signs'],rules)
        relief = {'nadi': a['star']==b['star'] and a['pada']!=b['pada'],
                  'bhakoot': n[6]==0 and s[6]}
        facts = {'match.pair.ready':all(case['consent']), 'match.moons.stable':True,
                 'match.nadi.same':a['nadi']==b['nadi'], 'match.nadi.pada_parihara':relief['nadi'],
                 'match.bhakoot.lord_parihara':relief['bhakoot']}
        require(kb10['match.nadi.pada_parihara']==relief['nadi'] and
                (kb10['match.bhakoot.zero'] and kb10['match.bhakoot.lord_parihara'])==relief['bhakoot'],
                'KB-10 relief parity')
        for key in relief:
            exception = matching_rules['vedic.matching.'+key]['exceptions'][0]
            require(evaluate(exception['when'],facts) == case[key+'_softened'],key+' relief')
        directions = ['context' if relief.get(k) else 'care' if v==0 else 'support'
                      if v==policy['weights'][k] else 'context' for k,v in zip(north_order,n)]
        require(qualitative(directions) == case['tone'],'northern tone')
        for mode, keys in [('north',north_order),('south',['porutham-'+k for k in south_order])]:
            inputs = {**facts,'match.profile':mode}
            fired = {k.split('.')[-1] for k,v in matching_rules.items() if evaluate(v['conditions'],inputs) is True}
            expected = set(keys)
            if mode=='north' and facts['match.nadi.same']:
                expected.add('shared-star-class')
            require(fired==expected,mode+' factor isolation')
            for key in ('match.pair.ready','match.moons.stable'):
                require(not any(evaluate(v['conditions'],{**inputs,key:False}) is True
                                for v in matching_rules.values()),key+' gate')
        southern_directions = ['support' if v else 'care' for v in s]
        if a['sign'] == b['sign']:
            southern_directions[south_order.index('rashi')] = 'context'
        if not s[south_order.index('rashi-lord')]:
            southern_directions[south_order.index('rashi-lord')] = 'context'
        if b['gana']==2 and a['gana']!=2:
            southern_directions[south_order.index('gana')] = 'context'
        require(qualitative(southern_directions)==case['tone'], 'southern tone')
        for key,flag in [('chart-cross-check','match.context.ready'),('manglik-comparison','match.mars.ready')]:
            rule = matching_rules['vedic.matching.'+key]
            inputs = {**facts, 'match.profile':'context', flag:True}
            require(evaluate(rule['conditions'],inputs) is True and
                    evaluate(rule['conditions'],{**inputs,flag:False}) is False, key+' context binding')
        for locale in ('en','kn','hi'):
            labels = read('shared/localization/reading.yaml')['tones']
            for slug in ('nadi','porutham-rajju'):
                public = {'localized_tone':next(x[locale] for x in labels if x['en']==case['tone']),
                          'user_text':matching_rules['vedic.matching.'+slug]['user_text'][locale]}
                require(set(public)==set(policy['access']['public_fields']) and
                        all(isinstance(v,str) and not any(c.isdigit() for c in v) for v in public.values()),
                        'localized projection')
    for probe in fixture['raman_relief_probes']:
        a,b = [moon(d*3600,t) for d in probe['moons']]
        n,s = factors(a,b,t)
        quarter_classes = (0,1,2,2,1,0)
        qa,qb = [quarter_classes[((x['star']-1)*4+x['pada']-1)%6] for x in (a,b)]
        values = {'match.nadi.quarter_relief':probe['selected'] and n[7]==0 and qa!=qb,
                  'match.bhakoot.raman_relief':probe['selected'] and n[6]==0 and s[6]}
        for slug in ('nadi','bhakoot'):
            exception = matching_rules['vedic.matching.'+slug]['exceptions'][1]
            require(exception['effect']=='cancel' and evaluate(exception['when'],values)==probe[slug],
                    f'{slug} cancellation on {probe}')
    require(qualitative(['support'])=='Supportive' and qualitative(['care'])=='Take care','unmixed tones')
    require(policy['access']['public_fields']==['localized_tone','user_text'],'matching public whitelist')
    for key,entry in matching_rules.items():
        for ref in entry.get('matching',{}).get('related_rules',[]):
            require(ref in rules,key+' dependency')
        for text in entry['user_text'].values():
            require(not any(c.isdigit() for c in text) and 'not compatible' not in text.lower(),key+' public copy')
    print('Matching passed: 729 ordered star pairs, 11,664 ordered pada comparisons across both profiles, two synthetic couples.')


def summary(case, policy, locale):
    total=case['raw_total']
    if not case['consented'] or not case['moons_stable'] or total is None or not 0<=total<=36:
        return None
    band='care' if total<18 else 'mixed' if total<25 else 'close'
    votes=[{'care':'care','mixed':'context','close':'support'}[band]]
    explanations=['understanding',band]
    for factor in ('bhakoot','nadi'):
        if case[factor]['formed'] and not case[factor]['cancelled']:
            votes.append('care')
        elif case[factor]['formed']:
            explanations.append(factor+'-relief')
    mars=case['mars']
    # Compare only the residual results after each chart's natal reliefs.
    if None not in (mars['first'],mars['second']):
        if (mars['first'] or mars['second']) and not (mars['first'] and mars['second'] and mars['comparable']):
            votes.append('care')
            explanations.append('kuja-difference')
        elif mars['first'] and mars['second']:
            explanations.append('kuja-balance')
    for channel in ('partnership','moon-lagna','d9','period'):
        direction=case['cross'].get(channel)
        if direction is not None:
            explanations.append(channel)
            votes.append('care' if direction=='caution' else direction)
    explanations.append('prompt')
    tone=qualitative(votes)
    return {'localized_tone':policy['tone_labels'][tone][locale],'user_text':[policy['messages'][key][locale] for key in explanations]}


def validate_summary(read, require):
    p=read('vedic/matching/summary.yaml')
    case=read('examples/matching-summary.yaml')
    for locale in ('en','kn','hi'):
        result=summary(case,p,locale)
        require(result['localized_tone']==p['tone_labels'][case['tone']][locale] and result['user_text']==[p['messages'][k][locale] for k in case['message_keys']], 'Scenario P3')
    for points,expected in [(17.5,'Take care'),(18,'Steady'),(24.5,'Steady'),(25,'Supportive'),(36,'Supportive')]:
        require(summary(dict(case,raw_total=points,cross={}),p,'en')['localized_tone']==expected,'band endpoint')
    require(summary(dict(case,consented=False),p,'en') is None and summary(dict(case,raw_total=None),p,'en') is None,'missing consent or total')
    close=dict(case,raw_total=30,cross={})
    require(summary(dict(close,nadi=dict(formed=True,cancelled=False)),p,'en')['localized_tone']=='Steady'
            and summary(close,p,'en')['localized_tone']=='Supportive','Nadi relief')
    require(summary(dict(close,mars=dict(first=True,second=False,comparable=False)),p,'en')['localized_tone']=='Steady','one residual Kuja')
