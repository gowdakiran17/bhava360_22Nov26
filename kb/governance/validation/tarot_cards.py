"""Check the RWS inventory, Golden Dawn decans, spread bindings and admin replay."""
from collections import Counter
from functools import lru_cache
import importlib.util
import re


BLOCK = re.compile(
    r'\b(?:death|deadly|doom\w*|curs(?:e|ed|es)|catastroph\w*|disaster\w*|terror\w*|'
    r'fatal\w*|ruin(?:ed)?|guarantee\w*|inevitable|will happen)\b'
    r'|विनाश|तबाही|श्राप|शाप|अनिवार्य रूप से|निश्चित रूप से होगा'
    r'|ವಿನಾಶ|ಶಾಪ|ದುರಂತ|ಖಂಡಿತವಾಗಿಯೂ ಆಗುತ್ತದೆ',re.I)


def validate_tarot(rules,read,require,root):
    read = lru_cache(maxsize=None)(read)
    deck = read('tarot/draws/deck.yaml')['order']
    records = {r['id']:r for r in rules.values() if r['system']=='tarot'}
    require(len(deck)==len(set(deck))==78 and len(records)==156,'RWS inventory')
    suits = {'wands':'fire','cups':'water','swords':'air','pentacles':'earth'}
    ranks = 'ace two three four five six seven eight nine ten page knight queen king'.split()
    require(deck[22:]==[f'{r}-of-{s}' for s in suits for r in ranks],'minor draw order')
    require(deck[8]=='strength' and deck[11]=='justice','RWS trump order')
    decans = {}
    for i,card in enumerate(deck):
        topic = 'major-arcana' if i<22 else 'minor-arcana'
        pair = [records[f'tarot.{topic}.{card}-{side}'] for side in ('upright','reversed')]
        require(pair[0]['meaning']!=pair[1]['meaning'],card+' orientation distinction')
        for side,r in zip(('upright','reversed'),pair):
            m = r['card_profile']
            require((m['card'],m['orientation'])==(card,side) and m['tone'] in ('Supportive','Steady','Take care')
                    and len(set(m['keywords']))>=2 and r['life_areas'],r['id']+' metadata')
            require(m['element'] in suits.values() and m['golden_dawn']==pair[0]['card_profile']['golden_dawn'],card)
            require({'waite-pictorial-key','golden-dawn-book-t'}<={s['work_id'] for s in r['sources']},card+' sources')
            for text in [r['meaning'],*m['keywords'],*r['user_text'].values()]:
                require(not BLOCK.search(text),r['id']+' reflective language')
        link = pair[0]['card_profile']['golden_dawn']
        if i>=22:
            rank,suit = card.split('-of-')
            require(pair[0]['card_profile']['element']==suits[suit],card+' suit element')
            if rank in ranks[1:10]:
                require(link['kind']=='decan' and link['start_degree'] in (0,10,20) and
                        link['end_exclusive_degree']==link['start_degree']+10,card)
                key = (link['sign'],link['start_degree'])
                require(key not in decans,card+' duplicate decan')
                decans[key]=link['planet']
            elif rank in ('queen','knight','king'):
                require(link['kind']=='court-span' and link['from_degree']==link['end_exclusive_degree']==20,card)
            else:
                require(link['kind']==('elemental-root' if rank=='ace' else 'polar-quadrant'),card)
    order = 'mars sun venus mercury moon saturn jupiter'.split()
    zodiac = 'aries taurus gemini cancer leo virgo libra scorpio sagittarius capricorn aquarius pisces'.split()
    for i in range(36):
        require(decans[(zodiac[i//3],(i%3)*10)]==order[i%7],'Golden Dawn decan ruler')
    spreads = read('tarot/spreads/positions.yaml')
    catalog = read('tarot/positions/catalog.yaml')['positions']
    require(spreads['spreads'].keys()==spreads['definitions'].keys(),'spread routing')
    lengths = {'single-card':1,'three-card':3,'celtic-cross':10,'career-five':5,'relationship-five':5}
    for slug,path in spreads['definitions'].items():
        d = read('tarot/'+path)
        positions=d['positions']
        require(d['id']==slug and len(set(positions))==len(positions)==lengths.get(slug,len(positions)) and
                [catalog[k]['name'] for k in positions]==spreads['spreads'][slug],slug)
        for key in positions:
            require(all(not BLOCK.search(t) for t in catalog[key]['user_text'].values()),key)
    require(lengths.keys()<=spreads['definitions'].keys(),'required layouts')
    spec = importlib.util.spec_from_file_location('tarot_seeded_draw',root/'tarot/draws/seeded.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ref=read('examples/tarot-reference.yaml')
    args=dict(seed=bytes.fromhex(ref['seed_hex']),picks=ref['picks'],cut=ref['cut'])
    sample=mod.reading(read,ref['spread'],**args)
    admin=sample['admin']
    require([[s[k] for k in ('position','card','orientation')] for s in admin['slots']]==ref['expected'],'replay vector')
    for locale in ('en','kn','hi','fr'):
        result=mod.reading(read,ref['spread'],locale=locale,**args)
        require(result['admin']==admin and set(result['public'])=={'slots','footer'},'replay and projection')
        for slot,public in zip(admin['slots'],result['public']['slots']):
            entry=records[slot['rule_id']]
            require(public['user_text']==entry['user_text'].get(locale,entry['user_text']['en']),entry['id'])
    other=mod.reading(read,ref['spread'],reversals=False,**args)['admin']['slots']
    require([s['card'] for s in other]==[s['card'] for s in admin['slots']] and
            all(s['orientation']=='upright' for s in other),'orientation independence')
    require(mod.uniform(iter([2**32-1,8]),3)==2,'reject modulo bias')
    # A deterministic distribution smoke test, with 100 first-slot observations expected per card.
    counts=Counter()
    for i in range(7800):
        slots=mod.draw(deck,['reflection'],seed=i.to_bytes(32,'big'))['slots']
        counts[slots[0]['card']]+=1
    require(sum((counts[c]-100)**2/100 for c in deck)<140,'first-card chi-square smoke test')
    all_cards=mod.draw(deck,list(range(78)),seed=args['seed'])['slots']
    require(len({slot['card'] for slot in all_cards})==78,'no replacement')
    for term in ['doom','disaster','तबाही','ದುರಂತ']:
        require(BLOCK.search(term),'tarot copy guard')
    print('Tarot passed: 78 cards, 156 meanings, 36 decans, spread positions and reproducible draws.')
