"""Synthetic full, limited and privacy projections for the six check tools."""
from datetime import date
from urllib.parse import urlparse
from numerology import calculate, fit_tone, public_debt_readings, pythagorean_stages


def validate_checkers(rules,read,require):
    cases=read('examples/checkers-reference.yaml')['tools']
    require(set(cases)==set(read('life-areas/catalog.yaml')['checker_ids']),'checker inventory')
    specs={school:read('numerology/'+school+'/calculation.yaml') for school in ('chaldean','pythagorean')}
    labels=read('shared/localization/reading.yaml')['tones']
    for tool,case in cases.items():
        recipe=read(f'checkers/{tool}/recipe.yaml')
        require(set(case['channels'])==set(recipe['reason_channels']),tool+' channel coverage')
        context=case['synthetic_context']
        ids={item['rule_id']:item for item in recipe['explain_rules']}
        rows=[dict(rule_id=rid,approved=True,matches=True,channel=ids[rid].get('channel',ids[rid]['evidence']))
              for rid in case['matched']]
        if tool=='mobile-number':
            rows[-1]['derived_direction']='support'
        require(fit_tone(recipe,rows)==case['tone'] and fit_tone(recipe,rows[:1])==case['limited']['tone'],tool+' tone')
        require(fit_tone(recipe,[dict(row,approved=False) for row in rows])=='Steady',tool+' approval')
        require(all(not value for value in case['privacy'].values()),tool+' synthetic privacy contract')
        if tool=='big-decision-muhurta':
            continue
        profile=read(recipe['numerology_profile'])
        result=calculate(profile,case['input'],context.get('school','chaldean'),specs,labels,recipe=recipe,
                         matched=rows,birth_root=context.get('birth_root'),compatibility=read('numerology/ank-jyotish/compatibility.yaml'))
        require(result['public']['localized_tone']==case['tone'] and set(result['public'])=={'localized_tone','user_text'},tool+' projection')
        if tool=='mobile-number':
            require(case['input'] not in str(result) and result['admin']['chain']==[10,1] and
                    result['admin']['absent']==list(range(2,9)),tool+' local arithmetic and privacy')
        if tool=='personal-baby-name':
            require(result['admin']['chain'][-1]==context['life_path'],'name master stage')
    lex=read('checkers/personal-baby-name/name-lexicon.yaml')['entries']
    require(len(lex)>=300 and {r['origin'] for r in lex.values()}=={'Kannada','Hindi','Sanskrit'}
            and all(all(r.get(k) for k in ('en','kn','hi','source')) for r in lex.values())
            and lex.get('Unlisted Example') is None,'attested name lookup or unavailable')
    brands=read('checkers/business-name/brand-list.yaml')['entries']
    require(len({b['name'].casefold() for b in brands})==len(brands)>=50 and
            all(b['market']=='IN' and urlparse(b['source']).scheme=='https' for b in brands),'brand list')
    for day in (13,14,16,19):
        _,hits=pythagorean_stages(date(2000,1,day),'Asha',specs['pythagorean'])
        selected=[hit for hit in hits if hit[0] in ('birthday','life-path-day')]
        require(len(selected)==2 and len(list(public_debt_readings(selected)))==1,'birth-day copy once')
