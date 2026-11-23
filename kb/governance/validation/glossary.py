"""Scan all maintained KB text, independently of the authored glossary."""
from collections import defaultdict
from pathlib import Path
import re
import unicodedata as ud
import yaml

# Keep Indic vowel signs attached. Fold Latin transliteration marks only.
def words(text):
    text = ud.normalize('NFC', str(text)).casefold()
    text = re.sub(r'[a-zÀ-žḀ-ỿ]+', lambda m: ''.join(c for c in ud.normalize('NFD', m[0])
                                                      if not ud.combining(c)), text)
    return re.findall(r'[a-z0-9]+|[\u0900-\u0963\u0c80-\u0ce3]+', text)


def normalized(text):
    return ' '.join(words(text))


def corpus(root):
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root)
        if not path.is_file() or rel.parts[0] in ('glossary','export','dist-json') or '__pycache__' in rel.parts:
            continue
        if path.suffix not in ('', '.md', '.py', '.csv', '.yaml', '.svg'):
            raise ValueError(f'Classify new KB file type for glossary scan: {rel}')
        yield rel, path.read_text()


def document_ids(root, rules):
    owners = defaultdict(list)
    for rel, content in corpus(root):
        if rel.suffix == '.yaml':
            match = re.search(r'^id: ([\w.-]+)$', content, re.M)
            if match:
                owners[match[1]].append(rel)
    return {rid: {'system': paths[0].parts[0]} for rid, paths in owners.items() if len(paths)==1} | rules


def scan(root, entries, rules):
    trie = {}
    owners = {}
    for key, entry in entries.items():
        forms = [*entry['term'].values(), *entry['aliases'],
                 entry['sanskrit']['devanagari'], entry['sanskrit']['kannada']]
        for form in forms:
            path = words(form)
            if not path:
                raise ValueError(f'Empty alias: {key}')
            token = tuple(path)
            if owners.setdefault(token, key) != key:
                raise ValueError(f'Ambiguous alias: {form} ({key}, {owners[token]})')
            node = trie
            for word in path:
                node = node.setdefault(word, {})
            node[None] = key
    links = defaultdict(set)
    seen, vocabulary = set(), set()
    for rel, content in corpus(root):
        # Find rule-file owners by their canonical top-level ID.
        match = re.search(r'^id: ([\w.-]+)$', content, re.M)
        rid = match[1] if match and match[1] in rules else None
        tokens = words(str(rel) + '\n' + content)
        vocabulary.update(t for t in tokens if not t.isdecimal())
        for i, token in enumerate(tokens):
            node = trie.get(token)
            j = i + 1
            while node:
                if None in node:
                    key = node[None]
                    seen.add(key)
                    if rid and (not entries[key].get('systems') or rules[rid]['system'] in entries[key]['systems']):
                        links[key].add(rid)
                node = node.get(tokens[j]) if j < len(tokens) else None
                j += 1
    return links, seen, vocabulary


def validate_glossary(rules, read, require, root):
    base = root / 'glossary'
    entries = {}
    for path in sorted((base / 'entries').glob('*.yaml')):
        row = yaml.safe_load(path.read_text())
        key = path.stem
        require(row['id'] == 'glossary.terms.' + key, str(path))
        require(set(row['term']) == set(row['meaning']) == {'en','kn','hi'} and
                all(isinstance(v,str) and v.strip() and '\n' not in v for v in row['meaning'].values()), key)
        for field,lo,hi in [('devanagari','ऀ','ॿ'),('kannada','ಀ','೿')]:
            require(any(lo <= c <= hi for c in row['sanskrit'][field]),key+' Sanskrit '+field)
        require(row['admin_note'].strip() and len(row['aliases'])==len(set(map(normalized,row['aliases']))),key)
        entries[key] = row
    inventory = (base / 'inventory.txt').read_text().splitlines()
    require(sorted(entries) == inventory,'glossary inventory and entry files differ')
    missing = catalog_keys(read) - entries.keys()
    require(not missing, 'named catalog members need glossary entries: ' + str(sorted(missing)))
    palm_refs = {rid for row in entries.values() for rid in row.get('reference_rules', [])}
    for choice in read('palmistry/guided-observations/choices.yaml')['choices'].values():
        require(set(choice['rules'].values()) <= palm_refs,'illustrated palm term missing')
    for legacy in ('terms/core.yaml','translations/additions.yaml'):
        indexed = {normalized(s) for row in entries.values() for s in [*row['aliases'],*row['term'].values()]}
        for fields in read('glossary/'+legacy)['terms'].values():
            require(all(normalized(s) in indexed for s in fields.values()),'unindexed legacy glossary label')
    for alias, key in read('glossary/aliases/lookup.yaml')['canonical_ids'].items():
        require(key.removeprefix('glossary.terms.') in entries and
                normalized(alias) in {normalized(s) for s in
                    [*entries[key.split('.')[-1]]['term'].values(),*entries[key.split('.')[-1]]['aliases']]},
                'unresolved legacy glossary alias '+alias)
    rules = document_ids(root,rules)
    links, seen, vocabulary = scan(root,entries,rules)
    reviewed = set((base / 'scan-vocabulary.txt').read_text().splitlines())
    require(vocabulary <= reviewed,'new KB vocabulary needs glossary review: '+str(sorted(vocabulary-reviewed)[:40]))
    for key,row in entries.items():
        anchors = set(row.get('reference_rules',[]))
        actual = row['used_by']
        files = row.get('used_in_files', [])
        require(all((root / f).is_file() and (root / f).resolve().is_relative_to(root) for f in files),key+' file usage')
        require((key in seen or anchors or files) and (actual or files) and actual == sorted(links[key] | anchors)
                and set(actual) <= rules.keys(), key+' glossary backlinks')
    for lang in ('en','kn','hi'):
        labels = read(f'glossary/locales/{lang}.yaml')['terms']
        require(labels == {k:r['term'][lang] for k,r in entries.items()},lang+' glossary index')
    for lang in ('te','ta','ml','es','fr'):
        row = read(f'glossary/locales/{lang}.yaml')
        require(row['fallback']=='en' and not any(row['terms'].values()),lang+' glossary fallback')
    print(f'Glossary passed: {len(entries)} terms, corpus vocabulary, aliases, locale indexes and rule links.')


def catalog_keys(read):
    """Discover named members from their owners, independently of glossary files."""
    from itertools import chain
    def slug(name):
        return '-'.join(words(name))
    limbs = read('vedic/panchang/limb-tables.yaml')
    karanas = limbs['karana']
    configs = [
        (r['id'] for r in read('vedic/signs/catalog.yaml')['signs']),
        (r['id'] for r in read('vedic/nakshatras/catalog.yaml')['nakshatras']),
        read('vedic/planets/catalog.yaml')['grahas'],
        ('house-' + str(r['number']) for r in read('vedic/houses/catalog.yaml')['houses']),
        (r['chart'].lower() for r in read('vedic/vargas/methods.yaml')['methods']),
        (slug(r['name']) for r in limbs['tithi']),
        (slug(n) + '-calendar-yoga' for n in limbs['yoga']),
        chain(karanas['fixed'].values(),karanas['movable']),
        (slug(n) + '-yogini' for n in read('vedic/dashas/yogini/periods.yaml')['sequence']),
        (slug(n) + '-choghadiya' for n in read('vedic/panchang/day-night.yaml')['choghadiya_order']),
        (slug(n) + '-age-state' for n in read('vedic/states/baladi.yaml')['state']['state_meanings']),
        (slug(n) + '-vastu-guardian' for n in read('vastu/profile.yaml')['guardians'].values()),
        read('western/aspects/orbs.yaml')['draft_natal_orbs'],
        (card + '-tarot' for card in read('tarot/draws/deck.yaml')['order']),
    ]
    return set(chain.from_iterable(configs))
