"""Validate existing-rule synthesis profiles and free practices throughout the KB."""
import re
import unicodedata


AREAS = {
    'career', 'money', 'love-marriage', 'family-home', 'health', 'learning',
    'children', 'property-vehicles', 'travel-relocation', 'spirituality',
}
FEEDS = {
    'houses': 'vedic.houses.house-',
    'karakas': 'vedic.planets.',
    'vargas': 'vedic.vargas.',
    'dashas': 'vedic.dashas-vimshottari.',
    'transits': 'vedic.transits.',
}
PROHIBITED = re.compile(
    r'\b(?:must|mustn[’\x27]t|required|mandatory|compulsory|guarantee\w*|gems?|(?:gem|precious\s+)?stones?|'
    r'crystals?|ratnas?|lucky\s+colou?rs?|paid\s+(?:pujas?|poojas?|yantras?)|yantras?\s+for\s+sale)\b'
    r'|अनिवार्य|करना ज़रूरी|करना जरूरी|अवश्य|करना ही होगा|गारंटी|रत्न|क्रिस्टल|शुभ रंग|खरीदना होगा|भाग्यशाली रंग|स्फटिक|पत्थर'
    r'|ಕಡ್ಡಾಯ|ಮಾಡಲೇಬೇಕು|ಖಾತರಿ|ರತ್ನ|ಸ್ಫಟಿಕ|ಅದೃಷ್ಟದ ಬಣ್ಣ|ಹರಳು', re.IGNORECASE)
KINDS = {'mantra-japa', 'charity', 'fasting', 'service', 'routine', 'temple-visit'}


def check_remedy(remedy, location, require):
    require(isinstance(remedy, dict) and remedy.get('optional') is True and remedy.get('cost') == 'free',
            f'{location}: remedy must be optional and cost free')
    require(remedy.get('free', True) is True, f'{location}: conflicting free status')
    require(remedy.get('type') in KINDS | {'conduct', 'mantra'}, f'{location}: unknown practice')
    texts = remedy.get('user_text')
    require(isinstance(texts, dict) and {'en','kn','hi'} <= texts.keys(), f'{location}: remedy locales')
    for locale, text in texts.items():
        require(isinstance(text, str) and text.strip(), f'{location}: empty remedy text for {locale}')
        match = PROHIBITED.search(unicodedata.normalize('NFKC', text))
        require(match is None, f'{location}: unsuitable remedy wording in {locale}: {match}')


def validate_life_areas(rules, read, require, root):
    folders = root / 'life-areas'
    require({p.parent.name for p in folders.glob('*/summary.yaml')} == AREAS, 'life-area summary coverage')
    tones = {'Supportive','Steady','Take care'}
    for area in sorted(AREAS):
        path = f'life-areas/{area}/'
        recipe = read(path+'reading.yaml')
        require(recipe.get('summary_profile') == 'summary.yaml', area+' summary discovery')
        summary = read(path+recipe['summary_profile'])
        require(summary['area'] == area and summary['weighting_order'] == ['natal-promise','dasha','transit'],
                area+' evidence order')
        feeds = summary['feeds']
        groups = dict(FEEDS)
        if area == 'career':
            groups['house_lord_placements'] = 'vedic.house-lords.lord-10-in-house-'
            require(feeds.get('house_lord_placements') == [groups['house_lord_placements']+str(i) for i in range(1,13)], 'career tenth lord')
        require(feeds.keys() == groups.keys(), area+' feed categories')
        for group, prefix in groups.items():
            ids = feeds[group]
            require(isinstance(ids,list) and ids and len(ids)==len(set(ids)) and
                    all(rid.startswith(prefix) and rid in rules for rid in ids), f'{area}: {group} references')
        require(feeds['houses']==[FEEDS['houses']+str(n) for n in recipe['houses']]
                and feeds['karakas']==[FEEDS['karakas']+g for g in recipe['karakas']]
                and FEEDS['vargas']+recipe['varga'].lower()+'-placement' in feeds['vargas'], area+' natal binding')
        for slot, group in [('present-situation','dashas'),('upcoming-periods','dashas'),('concerns-to-watch','transits')]:
            require(recipe['slot_bindings'][slot]['rule_id'] in feeds[group],area+' '+slot)
        require(summary['summaries'].keys()==tones, area+' public tones')
        for tone, copy in summary['summaries'].items():
            texts = copy['user_text']
            require(re.search(r'\b(may|can)\b',texts['en'],re.I) and 'ಬಹುದು' in texts['kn'] and
                    re.search('सक[तें]',texts['hi']), area+' gentle wording for '+tone)
        if area=='health':
            line = summary['always_append']['user_text']
            require('see a doctor' in line['en'].lower() and 'ವೈದ್ಯ' in line['kn'] and 'डॉक्टर' in line['hi'],
                    'wellbeing clinician referral')
    kinds = set()
    planets = set()
    for path in sorted((root/'remedies').glob('*.yaml')):
        record = read(path.relative_to(root))
        require(record['id']=='remedies.conduct.'+path.stem and record['id'] not in rules, str(path))
        target = record['linked_to']
        require(target in rules and target.startswith((FEEDS['karakas'], FEEDS['houses'])), str(path)+' link')
        practice = record['remedy']['type']
        require(practice in KINDS,str(path)+' practice type')
        if path.stem in read('vedic/planets/catalog.yaml')['grahas']:
            options = record['options']
            require(practice == 'service' or options['service']['type'] == 'service', str(path)+' service')
            for name, option in options.items():
                check_remedy(option, str(path)+'.'+name, require)
            for name,kind in [('japa','mantra-japa'),('charity','charity')]:
                require(options[name]['type']==kind and all(x['url'] and x['locator'] for x in options[name]['sources']) and options[name]['sources'], str(path)+' sources')
            require(options['japa']['weekday'] in 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split(), str(path)+' weekday')
        kinds.add(practice)
        planets.add(target)
    require(kinds==KINDS and all('vedic.planets.'+g in planets for g in read('vedic/planets/catalog.yaml')['grahas']),
            'remedy coverage')
    print('KB-23 passed: ten life areas, all feed IDs, three localized tones and six free practice types.')
