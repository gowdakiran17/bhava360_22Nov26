"""Reference lookups on observed, synthetic layouts; keep technical evidence private."""
from itertools import product
from math import floor, isfinite
import re
import unicodedata


TONES = {'Supportive','Steady','Take care'}
TERMS = re.compile(
    r'\b(?:disasters?|illness(?:es)?|loss(?:es)?|disease\w*|wealth|profits?|income|cures?|'
    r'health|money|buy\w*|purchas\w*|products?|sell\w*|demoli\w*|demolition\w*|rebuild\w*|'
    r'reconstruct\w*|renovat\w*|pyramids?|yantras?|mirrors?|crystals?|amulets?)\b|tear\s+down|knock\s+down'
    r'|आपदा|बीमारी|नुकसान|हानि|खरीद|ख़रीद|तोड़|दोबारा बना|पुनर्निर्माण|पिरामिड|यन्त्र|यंत्र|आईना|दर्पण|शीशा|उत्पाद|धनलाभ'
    r'|ವಿಪತ್ತು|ಅನಾರೋಗ್ಯ|ನಷ್ಟ|ಖರೀದಿ|ಕೆಡವ|ಒಡೆದು|ಮರುನಿರ್ಮಾಣ|ಪಿರಮಿಡ್|ಪಿರಮಿಡ|ಯಂತ್ರ|ಕನ್ನಡಿ|ಉತ್ಪನ್ನ|ಧನಲಾಭ',
    re.IGNORECASE)


def check_copy(node,require,path):
    if isinstance(node,list):
        for item in node:
            check_copy(item,require,path)
    elif isinstance(node,dict):
        for key,value in node.items():
            if key=='user_text':
                for locale,words in value.items():
                    require(not TERMS.search(unicodedata.normalize('NFKC',words)),f'{path} {locale}: restricted wording')
            else:
                check_copy(value,require,path)


def finite(value):
    return type(value) in (int,float) and isfinite(value)


def sector(angle,count):
    width = 360/count
    return floor((angle%360+width/2)/width)%count


def stable_sector(angle,error,count):
    if error>=180 or sector(angle-error,count)!=sector(angle+error,count) or error*2>=360/count:
        return None
    return sector(angle,count)


def observation(home,room,profile):
    if room.get('in_unit') is not True or room.get('use') not in profile['rooms']:
        return None
    if room.get('central') is True:
        return 'centre',None
    angle = room.get('bearing_deg')
    if room.get('central') is not False or not finite(angle):
        return None
    if home['reference']=='magnetic':
        correction = home.get('declination_deg')
        if not finite(correction):
            return None
        angle += correction
    elif home['reference']!='true':
        return None
    error = room.get('uncertainty_deg',0)
    if not finite(error) or error<0:
        return None
    index = stable_sector(angle,error,8)
    if index is None:
        return None
    sub = stable_sector(angle,error,16) if home['model']=='sixteen' else None
    return profile['directions'][index],profile['sectors16'][sub] if sub is not None else None


def pada(table,wall,distance,length):
    if wall not in table['rows'] or not all(map(finite,(distance,length))) or not 0<=distance<=length or length<=0:
        return None
    walls = ('east','south','west','north')
    if distance==length:
        wall = walls[(walls.index(wall)+1)%4]
        distance = 0
    return table['rows'][wall][floor(8*distance/length)]


def validate_vastu(rules,read,evaluate,require,root):
    profile = read('vastu/profile.yaml')
    fixture = read('examples/vastu-reference.yaml')
    zones = 'north northeast east southeast south southwest west northwest centre'.split()
    rooms = 'entrance kitchen bedroom pooja study toilet staircase water-tank'.split()
    require(profile['directions']==zones and set(profile['rooms'])==set(rooms),'Vastu inventory')
    require(profile['sectors16']=='N NNE NE ENE E ESE SE SSE S SSW SW WSW W WNW NW NNW'.split(),'sixteen sectors')
    require(profile['rendering']['access']['public']==['localized_tone','user_text'] and
            set(profile['rendering']['tones'])==TONES,'Vastu public projection')
    labels = read(profile['rendering']['labels'])['tones']
    scores = {-1:'Take care',0:'Steady',1:'Supportive'}
    entries = {k.split('.')[-1]:r for k,r in rules.items() if k.startswith('vastu.rooms.')}
    require(set(entries)=={z+'-'+r for z,r in product(zones,rooms)},'all 72 placement entries')
    for z,r in product(zones,rooms):
        key = z+'-'+r
        facts = {'vastu.observed.sector':z,'vastu.observed.room':r}
        active = [k for k,v in entries.items() if evaluate(v['conditions'],facts) is True]
        require(active==[key],key+' exclusive lookup')
        data = entries[key]['vastu']
        require((data['zone'],data['room'])==(z,r) and data['reason'] and data['tone']==scores[data['score']],key)
        if r=='water-tank':
            for kind,expected in [('overhead',z in ('west','southwest')),('underground',z in ('north','northeast')),('unspecified',False)]:
                value = -1 if kind=='underground' and z=='southwest' else int(expected)
                require(data['by_tank_type'][kind]==dict(score=value,tone=scores[value]),key+'/'+kind)
    require(evaluate(entries['southeast-kitchen']['conditions'],{'vastu.southeast-kitchen':True}) is True,
            'existing southeast kitchen observation')
    for shape in ('regular','irregular'):
        require(evaluate(rules['vastu.plots.'+shape+'-footprint']['conditions'],{'vastu.plot.shape':shape}) is True,
                shape+' shape binding')
    for slope,slug in [('level','level'),('north-eastward','fall-north-east'),('other','other-fall')]:
        require(evaluate(rules['vastu.plots.'+slug]['conditions'],{'vastu.plot.slope':slope}) is True,
                slope+' plot binding')
    require(list(profile['guardians'].values())=='Kubera Ishana Indra Agni Yama Nirriti Varuna Vayu Brahma'.split(),
            'directional guardians')
    expected_grahas = 'mercury jupiter sun venus mars rahu saturn moon'.split()+[None]
    for z,g in zip(zones,expected_grahas):
        rid = 'vastu.directions.'+('northeast-rulership' if z=='northeast' else z)
        data = rules[rid]['vastu']
        require(data['deity']==profile['guardians'][z] and data['graha']==profile['grahas'][z]==g,rid)
    require(fixture['synthetic'],'Vastu fixtures')
    for home in fixture['homes'].values():
        actual = {}
        for room in home['rooms']:
            place = observation(home,room,profile)
            if place is None:
                continue
            slug = place[0]+'-'+room['use']
            entry = entries[slug]
            data = entry['vastu']
            tone = data.get('by_tank_type',{}).get(room.get('tank_type','unspecified'),data)['tone']
            actual[room['id']] = [slug,tone]
            label = next(row for row in labels if row['en']==tone)
            for locale in ('en','kn','hi'):
                public = dict(localized_tone=label[locale],user_text=entry['user_text'][locale])
                require(all(isinstance(t,str) and not any(ch.isdigit() for ch in t) for t in public.values()),slug)
        require(actual==home['expected'],'synthetic home observations')
    base = fixture['homes']['Asha']
    test = base['rooms'][0]
    for n in (8,16):
        for i in range(n):
            edge = (i+0.5)*360/n
            require(sector(edge-0.0001,n)==i and sector(edge,n)==(i+1)%n and stable_sector(edge,0.1,n) is None,
                    f'angular edge {n}/{i}')
    require(observation({**base,'declination_deg':None},test,profile) is None,'unknown magnetic correction')
    require(observation({**base,'declination_deg':-5},{**test,'bearing_deg':3},profile)==('north',None),'west declination')
    require(observation({**base,'reference':'true','model':'sixteen'},{**test,'bearing_deg':30},profile)
            ==('northeast','NNE'),'independent optional sector')
    table = read('vastu/entrances/padas.yaml')
    refs = {'east':'Shikhi Parjanya Jayanta Indra Surya Satya Bhrisha Antariksha',
            'south':'Vayu Pusha Vitatha Brihatkshata Yama Gandharva Bhringaraja Mriga',
            'west':'Pitri Dauvarika Sugriva Kusumadanta Varuna Asura Shesha Papayakshma',
            'north':'Roga Ahi Mukhya Bhallata Soma Bhujaga Aditi Diti'}
    for idx,(wall,names) in enumerate(refs.items()):
        for i,name in enumerate(names.split()):
            for at in (i,i+0.999):
                require(pada(table,wall,at,8)==dict(id=wall[0].upper()+str(i+1),deity=name),wall+' pada')
        following = list(refs)[(idx+1)%4]
        require(pada(table,wall,8,8)==pada(table,following,0,8),wall+' end corner')
    require(pada(table,'east',None,8) is None,'door facing alone cannot assign pada')
    link = profile['house_check']
    require(read(link['recipe'])['layout_profile']=='vastu/profile.yaml' and
            read(link['profile'])['parent_recipe']==link['recipe'] and all(r in rules for r in link['references']),
            'house-check integration')
    for path in (root/'vastu').rglob('*.yaml'):
        check_copy(read(path.relative_to(root)),require,path)
    for word in ('illness','disaster','loss','demolish','buy a mirror','rebuilding','yantra','pyramid','खरीद','ಕನ್ನಡಿ'):
        require(TERMS.search(word),'copy guard '+word)
    print('KB-26 passed: 72 room-zone pairs, both tank types, 32 entrance padas, true/magnetic and rented-flat fixtures.')
