"""Versioned RWS draw for admin replay and the KB-27 reference validator."""
import hashlib
import hmac
import secrets


def words(seed, purpose):
    prefix = b'bhava360-tarot-v1/' + purpose + b'/'
    counter = 0
    while True:
        digest = hmac.digest(seed, prefix + counter.to_bytes(8, 'big'), hashlib.sha256)
        for offset in range(0, 32, 4):
            yield int.from_bytes(digest[offset:offset+4], 'big')
        counter += 1


def uniform(stream, n):
    limit = 2**32 - 2**32 % n
    return next(value % n for value in stream if value < limit)


def draw(deck, positions, *, seed=None, reversals=True, cut=0, picks=None):
    cards = list(deck)
    if len(cards)!=78 or len(set(cards))!=78 or not 1<=len(positions)<=78:
        raise ValueError('Invalid deck or slot count')
    if type(reversals) is not bool or type(cut) is not int or not 0<=cut<78:
        raise ValueError('Invalid orientation setting or cut')
    if seed is None:
        seed = secrets.token_bytes(32)
    if not isinstance(seed,bytes) or len(seed)!=32:
        raise ValueError('Expected a 32-byte seed')
    picks = list(range(len(positions))) if picks is None else list(picks)
    if (len(picks)!=len(positions) or any(type(i) is not int or not 0<=i<78 for i in picks)
            or len(set(picks))!=len(picks)):
        raise ValueError('Invalid pick indices')
    shuffle = words(seed,b'shuffle')
    for i in range(77,0,-1):
        j = uniform(shuffle,i+1)
        cards[i],cards[j] = cards[j],cards[i]
    cards = cards[cut:]+cards[:cut]
    orientation = words(seed,b'orientation')
    slots = []
    for position,index in zip(positions,picks):
        side = 'reversed' if reversals and uniform(orientation,2) else 'upright'
        slots.append(dict(position=position,card=cards[index],orientation=side))
    return {'seed_hex':seed.hex(),'algorithm':'hmac-sha256-fy-v1','deck_version':'rws-78-v1',
            'cut':cut,'picks':picks,'reversals':reversals,'slots':slots}


def reading(read, spread_id, *, locale='en', seed=None, reversals=None, cut=0, picks=None):
    """Resolve KB records through a repository-relative read(path) callback."""
    registry = read('tarot/spreads/positions.yaml')['definitions']
    spread = read('tarot/'+registry[spread_id])
    deck = read('tarot/draws/deck.yaml')
    policy = read('tarot/draws/selection.yaml')
    if deck['version']!='rws-78-v1' or policy['algorithm']!='hmac-sha256-fy-v1':
        raise ValueError('Unsupported replay version')
    if reversals is None:
        reversals = policy['reversals_enabled_default']
    admin = draw(deck['order'],spread['positions'],seed=seed,reversals=reversals,cut=cut,picks=picks)
    admin.update(spread_id=spread_id,spread_version=spread['version'])
    positions = read('tarot/'+spread['position_catalog'])['positions']
    copy = read('shared/localization/reading.yaml')
    labels = {row['en']:row for row in copy['tones']}
    def localized(field):
        return field.get(locale,field['en'])
    slots = []
    for slot in admin['slots']:
        card,side = slot['card'],slot['orientation']
        topic = 'minor-arcana' if '-of-' in card and card!='wheel-of-fortune' else 'major-arcana'
        entry = read(f'tarot/{topic}/{card}-{side}.yaml')
        slot['rule_id'] = entry['id']
        slots.append(dict(card_name=entry['title'].rsplit(' · ',1)[0],orientation=side,
                          position_text=localized(positions[slot['position']]['user_text']),
                          localized_tone=localized(labels[entry['card_profile']['tone']]),
                          user_text=localized(entry['user_text'])))
    return {'admin':admin,'public':{'slots':slots,'footer':localized(copy['reflection'])}}
