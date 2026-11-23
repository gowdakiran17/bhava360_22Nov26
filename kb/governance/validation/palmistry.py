"""Check illustrated palm choices, hand binding, privacy and public reflections."""
import importlib.util
import re
from functools import lru_cache
from xml.etree import ElementTree

FEATURES = {
    'hands': 'earth air fire water',
    'mounts': 'jupiter saturn apollo mercury venus luna mars mars-upper mars-lower',
    'lines': 'heart head life life-short life-broken fate sun mercury union',
    'marks': 'cross star island grid triangle square',
    'fingers': 'long short thumb-long thumb-short',
}
BLOCK = re.compile(
    r'\b(?:life[ -]?span|longevity|life expectancy|death|die|dying|fatal\w*|fear\w*|'
    r'illness\w*|disease\w*|accident\w*|disaster\w*|wealth\w*|riches|doom\w*)\b'
    r'|(?:number of|how many|one|two|three|\d+) (?:marriages|children|child|marriage)\b'
    r'|आयु|जीवनकाल|बीमारी|दुर्घटन|मृत्यु|मौत|भय|धनलाभ|बच्चों की संख्या|विवाहों की संख्या'
    r'|ಆಯುಷ್ಯ|ಜೀವಿತಾವಧಿ|ಸಾವು|ಅನಾರೋಗ್ಯ|ಅಪಘಾತ|ಭಯ|ಸಂಪತ್ತು|ಮಕ್ಕಳ ಸಂಖ್ಯೆ|ಮದುವೆಗಳ ಸಂಖ್ಯೆ', re.I)


def validate_palmistry(rules, read, require, root, evaluate):
    read = lru_cache(None)(read)
    folder = 'palmistry/guided-observations/'
    catalog = read(folder + 'choices.yaml')['choices']
    expected = {group + '-' + option for group, options in FEATURES.items() for option in options.split()}
    require(set(catalog) == expected, 'palmistry feature inventory')
    intake = read(folder + 'questions.yaml')
    photo = intake['photo']
    require(intake['mode'] == 'illustrated-self-selection' and photo['feature_flag'] == 'palm_photo'
            and photo['separate_explicit_consent_required'] is True and photo['retention_days_default'] == 0
            and all(photo[k] is False for k in ('enabled_by_default','photo_ai_enabled','store_by_default','logging','training')),
            'palmistry photo defaults')
    spec = importlib.util.spec_from_file_location('palm_guided_reading', root / folder / 'reading.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    def project(observations, **kwargs):
        return module.guided_reading(read, rules, observations=observations, **kwargs)
    palms = {r['id']:r for r in rules.values() if r['system'] == 'palmistry'}
    for rid, rule in palms.items():
        require(all(not BLOCK.search(t) for t in [rule['meaning'], *rule['user_text'].values()]), rid + ' public language')
    ids, assets = set(), set()
    for key, choice in catalog.items():
        labels = choice['label']
        require({'en','kn','hi'} <= labels.keys() and all(not BLOCK.search(t) for t in labels.values()), key)
        path = (root / 'palmistry' / choice['illustration']).resolve()
        require(path.parent == (root / folder / 'illustrations').resolve() and path not in assets and
                ElementTree.parse(path).getroot().tag == '{http://www.w3.org/2000/svg}svg', key + ' illustration')
        assets.add(path)
        require(set(choice['rules']) == {'left','right'}, key)
        for hand, rid in choice['rules'].items():
            rule = palms[rid]
            ids.add(rid)
            other = 'right' if hand == 'left' else 'left'
            require(rule['guided']['choice'] == key and rule['guided']['hand'] == hand and
                    rule['guided']['tone'] in ('Supportive','Steady','Take care'), rid)
            for side, answer, selected, expected_hit in ((hand,True,key,True),(other,True,key,False),
                                                        (hand,False,key,False),(hand,True,'unselected',False)):
                facts = {'palm.guided.hand':side,'palm.guided.choice':selected,'palm.guided.confirmed':answer}
                require(evaluate(rule['conditions'], facts) is expected_hit, rid + ' conditions')
            observation = dict(hand=hand,feature=key,answer='confirmed')
            for locale in ('en','kn','hi','fr'):
                result = project([observation], consent=True, dominant='left', locale=locale)
                admin, = result['admin']
                public, = result['public']
                require(set(public) == {'localized_tone','user_text','reflection_footer'} and
                        public['user_text'] == rule['user_text'].get(locale,rule['user_text']['en']) and
                        admin['rule_id'] == rid and admin['role'] == ('dominant' if hand=='left' else 'non-dominant'), rid)
            for answer in ('absent','unsure'):
                require(not project([observation,dict(observation,answer=answer)], consent=True)['public'], rid)
    require(ids == {rid for rid, rule in palms.items() if 'guided' in rule} and len(ids)==2*len(expected),
            'palmistry paired inventory')
    require(project([observation],consent=False)=={'admin':[],'public':[]}, 'palmistry consent')
    try:
        project([dict(observation,photo=b'fixture')],consent=True)
    except ValueError:
        pass
    else:
        require(False,'photo input accepted')
    print('Palmistry passed: 32 illustrated features on both hands, localized projections, consent and photo defaults.')
