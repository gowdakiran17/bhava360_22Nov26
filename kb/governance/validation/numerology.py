"""Reference calculations for the KB-25 profiles, tested only with invented inputs."""
from collections import Counter
from datetime import date
from string import ascii_letters, ascii_uppercase
import re
import unicodedata


class InputError(ValueError):
    """An identifier or spelling needs clarification. Never include the raw input."""


def latin_name(value):
    letters = []
    for char in unicodedata.normalize('NFC', value):
        if char in ascii_letters:
            letters.append(char.upper())
        elif not (char.isspace() or char in "-.'’"):
            raise InputError('Confirm the intended Latin spelling')
    if not letters:
        raise InputError('Enter a name')
    return ''.join(letters)


def preview(value, table):
    """Scan consonant, optional nukta, then its vowel or virama as a unit."""
    value = unicodedata.normalize('NFC', value)
    result = []
    index = 0
    while index < len(value):
        char = value[index]
        index += 1
        following = value[index:index+1]
        if char in table['consonants']:
            letter = table['consonants'][char]
            if following == table['nukta']:
                if char not in table['nukta_consonants']:
                    raise InputError('Confirm the intended Latin spelling')
                letter = table['nukta_consonants'][char]
                index += 1
                following = value[index:index+1]
            if following == table['virama']:
                vowel = ''
                index += 1
                if value[index:index+1] in ('\u200c','\u200d'):
                    index += 1
            elif following in table['signs']:
                vowel = table['signs'][following]
                index += 1
            else:
                vowel = 'A'
            result.append(letter+vowel)
        elif char in table['vowels']:
            result.append(table['vowels'][char])
        elif char in table['marks'] and index > 1 and result and result[-1][-1:] in ascii_uppercase:
            result.append(table['marks'][char])
        elif char.isspace() or char in "-.'’":
            result.append(char)
        else:
            raise InputError('Confirm the intended Latin spelling')
    spelling = ''.join(result)
    latin_name(spelling)
    return spelling


def digit_sum(number):
    return sum(int(digit) for digit in str(number))


def reduction(value, keep):
    if type(value) is not int or value < 0:
        raise InputError('Expected a nonnegative integer')
    chain = [value]
    while value >= 10 and value not in keep:
        value = digit_sum(value)
        chain.append(value)
    return chain


def letter_values(spelling, mapping):
    by_letter = {letter:n for n,group in mapping.items() for letter in group}
    return [by_letter[c] for c in spelling]


def name_metrics(value, spec):
    spelling = latin_name(value)
    selected = {'expression':spelling,'soul-urge':''.join(c for c in spelling if c in 'AEIOU'),
                'personality':''.join(c for c in spelling if c not in 'AEIOU')}
    result = {}
    for metric, letters in selected.items():
        if letters:
            weights = letter_values(letters,spec['mapping'])
            result[metric] = {'weights':weights,'chain':reduction(sum(weights),spec['preserve_at_each_reduction'])}
    return result


def date_metrics(birth, target, keep):
    def reduced(n):
        return reduction(n,keep)[-1]
    month,day = reduced(birth.month),reduced(birth.day)
    year = reduced(month+day+reduced(target.year))
    cycle_month = reduced(year+target.month)
    return {'life-path':reduced(month+day+reduced(birth.year)), 'birthday':day,
            'personal-year':year,'personal-month':cycle_month,'personal-day':reduced(cycle_month+target.day)}


def pythagorean_stages(birth, spelling, spec, method='components'):
    keep = spec['preserve_at_each_reduction']
    stages = {}
    if method=='components':
        for label,n in [('month',birth.month),('day',birth.day),('year',birth.year)]:
            stages['life-path-'+label] = reduction(n,keep)
        combined = sum(chain[-1] for chain in stages.values())
    elif method=='full-digit-sum':
        combined = digit_sum(birth.year)+digit_sum(birth.month)+digit_sum(birth.day)
    else:
        raise InputError('Unknown Life Path convention')
    stages['life-path-final'] = reduction(combined,keep)
    stages['birthday'] = reduction(birth.day,keep)
    stages.update({m:r['chain'] for m,r in name_metrics(spelling,spec).items()})
    hits = [(stage,i,n) for stage,chain in stages.items() for i,n in enumerate(chain[:-1])
            if n in spec['debt_detection']['compounds']]
    return stages,hits


def public_debt_readings(hits):
    # The two stage traces for the same birth-day reduction explain a single observation.
    seen=set()
    for stage,index,compound in hits:
        key=('birthday' if stage=='life-path-day' else stage,index,compound)
        if key not in seen:
            seen.add(key)
            yield f'numerology.pythagorean.karmic-debt-{compound}'


def compat(table, birth_root, candidate):
    if type(birth_root) is not int or type(candidate) is not int or not (1<=birth_root<=9 and 1<=candidate<=9):
        return None
    relation = table['cells'][birth_root][candidate-1]
    return relation,table['direction'][relation]


def kua(year, opted_in, convention):
    if opted_in is not True or convention not in ('male-convention','female-convention') or not 1900<=year<=2099:
        return None
    reduced = reduction(year%100,[])[-1]
    male = convention=='male-convention'
    raw = (10-int(year>=2000))-reduced if male else 5+int(year>=2000)+reduced
    result = reduction(raw or 9,[])[-1]
    return (2 if male else 8) if result==5 else result


def identifier_digits(value, adapter):
    s = ''.join(str(unicodedata.decimal(c)) if c.isdecimal() else c for c in value.strip())
    if adapter=='phone':
        if s.startswith('+91'):
            s = s[3:]
        if not re.fullmatch(r'(?:[0-9\s-]|\([0-9]+\))+',s):
            raise InputError('Check the national mobile number')
    else:
        pattern = r'[A-Za-z0-9\s/\-]+' if adapter=='dwelling' else r'[A-Za-z0-9\s\-]+'
        if not re.fullmatch(pattern,s):
            raise InputError('Check the identifier')
    digits = [int(c) for c in s if c in '0123456789']
    if not digits or (adapter=='phone' and len(digits)!=10) or not any(digits):
        raise InputError('Check the identifier digits')
    return digits


def result_ids(school, chain):
    value = chain[-1]
    kind = 'master' if value in (11,22,33) else 'root'
    refs = [f'numerology.{school}.{kind}-{value}']
    if school=='chaldean' and 10<=chain[0]<=52:
        refs.append(f'numerology.chaldean.compound-{chain[0]}')
    return refs


def fit_tone(recipe, matched):
    """Input rows are already approved, matched and profile-compatible engine evidence.
    channel is the canonical independent evidence source, shared by arithmetic restatements.
    """
    directions = {r['rule_id']:r['direction'] for r in recipe['explain_rules']}
    channels = {}
    for row in matched:
        if row['rule_id'] in directions and row['approved'] and row['matches'] and row['channel']:
            direction = directions[row['rule_id']]
            if direction=='ruler-matrix':
                direction = row.get('derived_direction')
                if direction not in ('support','neutral','caution'):
                    continue
            channels.setdefault(row['channel'],set()).add(direction)
    if len(channels)<3:
        return 'Steady'
    votes = set.union(*channels.values()) - {'context'}
    selection = 'only_supportive' if votes=={'support'} else 'only_caution' if votes=={'caution'} else 'mixed_or_neutral'
    return recipe['tone_resolution'][selection]


def calculate(tool, value, school, specs, labels, locale='en', *, confirmed_latin=None,
              recipe=None, matched=(), mode=None, birth_root=None, compatibility=None):
    if mode=='city' and tool['adapter']=='dwelling':
        return {'delegate':tool['parent_recipe'],'mode':'city'}

    adapter = tool['adapter']
    if adapter=='letters':
        metric = name_metrics(confirmed_latin if confirmed_latin is not None else value,specs[school])['expression']
        chain = metric['chain']
        refs = [specs[school]['metrics']['expression'],*result_ids(school,chain)]
        audit = dict(metric,rule_ids=refs)
    else:
        digits = identifier_digits(value,adapter)
        chain = reduction(sum(digits),[])
        audit = dict(chain=chain,rule_ids=result_ids('ank-jyotish',chain))
        if adapter=='phone':
            counts = Counter(digits)
            audit['repeated'] = sorted(d for d,count in counts.items() if count>1)
            audit['absent'] = sorted(set(range(10))-counts.keys())
    if compatibility is not None and 'compatibility_table' in tool:
        candidate = reduction(chain[-1],[])[-1]
        pair = compat(compatibility,birth_root,candidate)
        if pair is not None:
            rid = next(r for r in tool['numerology_ids'] if r.endswith('-ruler-compatibility'))
            audit['ruler_reason'] = dict(rule_id=rid,relation=pair[0],derived_direction=pair[1],channel='birth-root-comparison')
            audit['rule_ids'].append(rid)
            # Only caller-approved matches participate. Derive direction here from the actual pair.
            matched = [dict(row,**audit['ruler_reason']) if row['rule_id']==rid else
                       dict(row,channel='birth-root-comparison') if row['rule_id'].endswith(('birth-root','brand-root','vehicle-number-root')) else row
                       for row in matched]
    if compatibility is None or 'ruler_reason' not in audit:
        matched = [row for row in matched if not row['rule_id'].endswith('-ruler-compatibility')]
    tone = fit_tone(recipe,matched) if recipe is not None else 'Steady'
    label = next(row for row in labels if row['en']==tone)
    words = tool['public']['user_text']
    return {'admin':audit,'public':{'localized_tone':label.get(locale,label['en']),
                                   'user_text':words.get(locale,words['en'])}}


PROHIBITED = re.compile(r'\b(?:un)?luck(?:y|ier|iest|ily|iness)?\b|\b(?:mis)?fortun(?:e\w*|ate\w*)\b'
                        r'|भाग्य|किस्मत|सौभाग्य|दुर्भाग्य|क़िस्मत|ಅದೃಷ್ಟ|ದುರಾದೃಷ್ಟ|ಸೌಭಾಗ್ಯ',re.I)


def validate_public_words(node, location, require):
    if isinstance(node,list):
        for item in node:
            validate_public_words(item,location,require)
    elif isinstance(node,dict):
        for key,value in node.items():
            if key=='user_text':
                for locale,text in value.items():
                    require(not PROHIBITED.search(unicodedata.normalize('NFKC',text)),f'{location}: {locale} wording')
            else:
                validate_public_words(value,location,require)


def validate_numerology(rules,read,evaluate,require,root):
    systems = ('chaldean','pythagorean')
    specs = {s:read(f'numerology/{s}/calculation.yaml') for s in systems}
    ref = read('examples/numerology-reference.yaml')
    require(ref['synthetic'] is True,'synthetic numerology identifiers')
    for school, spec in specs.items():
        groups = list(ref['letter_groups'][school].split())
        require(spec['mapping']==dict(enumerate(groups,1)) and
                sorted(''.join(groups))==list(ascii_uppercase),school+' exact complete table')
        keep = spec['preserve_at_each_reduction']
        require(keep==([11,22,33] if school=='pythagorean' else []),school+' master convention')
        for number,expected in ref['reduction'][school].items():
            require(reduction(number,keep)==expected,school+' reduction chain')
        for n in range(1,1001):
            chain = reduction(n,keep)
            require(chain[-1] in [*range(1,10),*keep] and all(digit_sum(a)==b for a,b in zip(chain,chain[1:]))
                    and (keep or chain[-1]==1+(n-1)%9),school+' reduction invariant')
        for metric,rid in spec['metrics'].items():
            require(evaluate(rules[rid]['conditions'],{f'number.{school}.computed-metric':metric}) is True,rid)
        for case in ref['dates']:
            result = date_metrics(date.fromisoformat(case['birth']),date.fromisoformat(case['target']),keep)
            require(result==case[school],school+' dated cycles '+str(result))
        for name, expected in ref['name_metrics'][school].items():
            result = name_metrics(name,spec)
            require({k:v['chain'] for k,v in result.items()}==expected,school+' vowel partitions '+name)
    for v in (11,22,33):
        rid, = result_ids('pythagorean',[v])
        require(evaluate(rules[rid]['conditions'],{'number.pythagorean.master':v}) is True, rid)
    expressions = ref['name_metrics']['pythagorean']['Asha Rao']['expression']
    require(reduction(ref['dates'][0]['pythagorean']['life-path']+expressions[-1],[11,22,33])[-1]
            == ref['maturity'],'Pythagorean maturity')
    scripts = read('numerology/transliteration.yaml')['scripts']
    for case in ref['transliteration']:
        require(preview(case['input'],scripts[case['script']])==case['preview'],'Indic preview')
        require(latin_name(case['confirmed'])==case['key'],'confirmed Latin spelling')
    selector = read('numerology/profiles.yaml')['system_selection']
    require(selector['India']=='chaldean' and selector['other_default']=='pythagorean','market defaults')
    labels = read('shared/localization/reading.yaml')['tones']
    profiles = {}
    for path in sorted((root/'checks').glob('*/profile.yaml')):
        tool = read(path.relative_to(root))
        slug = path.parent.name
        profiles[slug] = tool
        parent = read(tool['parent_recipe'])
        require(parent['numerology_profile']==str(path.relative_to(root)) and tool['check']==slug,slug+' binding')
        require(all(rid.startswith('numerology.') and rid in rules for rid in tool['numerology_ids']),slug+' references')
        require(tool['public']['fields']==['localized_tone','user_text'] and tool['public']['tones']==
                ['Supportive','Steady','Take care'],slug+' projection')
    require(set(profiles)=={case['check'] for case in ref['tools']},'five check fixtures')
    for case in ref['tools']:
        tool = profiles[case['check']]
        for school in systems:
            results = [calculate(tool,x,school,specs,labels) for x in case['equivalent']]
            require(all(r==results[0] for r in results),case['check']+' canonical equivalents')
            require(calculate(tool,case['equivalent'][0],school,specs,labels)==results[0],case['check']+' repeat')
            result = results[0]
            require(result['admin']['chain']==case[school],case['check']+' independent total '+school)
            require(all(i in rules for i in result['admin']['rule_ids']),case['check']+' derived references')
            require(set(result['public'])=={'localized_tone','user_text'} and result['public']['localized_tone']=='Steady',
                    case['check']+' limited evidence projection')
    for case in ref['transliteration']:
        result = calculate(profiles['personal-baby-name'],case['input'],'chaldean',specs,labels,
                           confirmed_latin=case['confirmed'])
        require(result==calculate(profiles['personal-baby-name'],case['key'],'chaldean',specs,labels),
                'confirmed spelling controls calculation')
    tool = profiles['house-relocation']
    require(calculate(tool,'Bengaluru','chaldean',specs,labels,mode='city')==
            {'delegate':tool['parent_recipe'],'mode':'city'}, 'city-only bypass')
    for case in ref['tone_cases']:
        slug = case.get('check','business-name')
        tool = profiles[slug]
        value = next(c['equivalent'][0] for c in ref['tools'] if c['check']==slug)
        recipe = read(tool['parent_recipe'])
        ids = [r['rule_id'] for r in recipe['explain_rules']]
        rows = [dict(rule_id=ids[i], approved=case.get('approved',True),matches=True,channel=str(i))
                for i in case['indices']]
        result = calculate(tool,value,'chaldean',specs,labels,recipe=recipe,matched=rows)
        require(result['public']['localized_tone']==case['expected'],'independent evidence tone')
    case = ref['scenario_n1']
    for method in ('components','full-digit-sum'):
        stages,hits = pythagorean_stages(date(1992,3,12),case['letter_input'],specs['pythagorean'],method)
        require(stages==case[method] and hits==[],method+' synthetic stages')
    dated = date_metrics(date.fromisoformat(case['synthetic_date']),date.fromisoformat(case['cycle_target']),[11,22,33])
    require(all(dated[key.replace('_','-')]==case['cycle_chains'][key][-1]
                for key in ('personal_year','personal_month','personal_day')), 'Scenario N1 calendar cycles')
    for raw,chain in [(29,[29,11]),(1999,[1999,28,10,1]),(11,[11])]:
        require(reduction(raw,[11,22,33])==chain,'master stage edge')
    edge = date(1999,11,29)
    component = pythagorean_stages(edge,'A',specs['pythagorean'])[0]
    full = pythagorean_stages(edge,'A',specs['pythagorean'],'full-digit-sum')[0]
    require(component['life-path-month']==[11] and component['life-path-day']==[29,11]
            and component['life-path-year']==[1999,28,10,1] and full['life-path-final']==[41,5],'date variant edges')
    # Exercise a calendar boundary independently of a fixture identity.
    distinct = date(1999,11,3)
    first = pythagorean_stages(distinct,'A',specs['pythagorean'])[0]['life-path-final'][-1]
    second = pythagorean_stages(distinct,'A',specs['pythagorean'],'full-digit-sum')[0]['life-path-final'][-1]
    require(first!=second,'distinguishable life path variants')
    for n in [13,14,16,19]:
        _,hits = pythagorean_stages(date(2000,1,n),'A',specs['pythagorean'])
        require(('birthday',0,n) in hits and ('life-path-day',0,n) in hits,'stage binding')
    matrix = read('numerology/ank-jyotish/compatibility.yaml')
    for a in range(1,10):
        require(len(matrix['cells'][a])==9 and all(compat(matrix,a,b)[1] in ('support','neutral','caution') for b in range(1,10)),'complete root matrix')
    require(compat(matrix,None,1) is None and compat(matrix,1,0) is None,'unknown compatibility')
    result = calculate(profiles['mobile-number'],case['mobile'],'pythagorean',specs,labels,birth_root=3,compatibility=matrix)
    require(result['admin']['ruler_reason']['derived_direction']==case['direction'] and 'ruler_reason' not in result['public'],'mobile reason')
    require(kua(1992,False,'female-convention') is None and kua(1992,True,None) is None
            and kua(1992,True,'male-convention')==8 and kua(1899,True,'male-convention') is None,'optional Kua')
    grid = read('numerology/lo-shu/grid.yaml')
    require(grid['default_fill']=='birth-digits-only' and grid['derived_additions']==[]
            and grid['arrows_and_planes']=='deferred','Lo Shu school boundary')
    kp = read('numerology/kua/profile.yaml')['input_policy']
    require(kp['requires_explicit_opt_in'] and kp['default_gender'] is None and
            not kp['inferred_from_name_or_chart'] and kp['missing_or_declined']=='withhold','Kua consent')
    for slug in ('mobile-number','vehicle-number','business-name'):
        profile = profiles[slug]
        sample = next(x['equivalent'][0] for x in ref['tools'] if x['check']==slug)
        recipe = read(profile['parent_recipe'])
        for birth_root in (None,1,3,8):
            computed = calculate(profile,sample,'chaldean',specs,labels,recipe=recipe,birth_root=birth_root,compatibility=matrix)
            candidate = reduction(computed['admin']['chain'][-1],[])[-1]
            reason = computed['admin'].get('ruler_reason')
            require(reason is None if birth_root is None else
                    reason['derived_direction']==compat(matrix,birth_root,candidate)[1],slug+' matrix integration')
    for term in ('lucky','unlucky','fortune','fortunate','misfortune','भाग्य','ಅದೃಷ್ಟ'):
        require(PROHIBITED.search(term), 'missing prohibited term '+term)
    for slug,value in ref['reject']:
        try:
            calculate(profiles[slug],value,'chaldean',specs,labels)
        except InputError:
            continue
        raise ValueError('Unexpected accepted synthetic '+slug+' input')
    for folder in ('numerology','checks','checkers'):
        for path in (root/folder).rglob('*.yaml'):
            validate_public_words(read(path.relative_to(root)),str(path.relative_to(root)),require)
    print('KB-25 passed: both complete letter tables, metric and master reductions, Indic previews and five repeatable checker profiles.')
