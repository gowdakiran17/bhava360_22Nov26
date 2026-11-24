"""Cross-system checks for review and for subsequent edits."""
from collections import defaultdict
import re
import yaml


MODAL = {'en': r'\b(?:may|can)\b', 'kn': r'ಬಹುದ|ಬಹುದು|ಬಹುದೇ', 'hi': r'सक[तें]'}
BLOCKED = re.compile(
    r"\b(?:death|deadly|accidents?|fear\w*|disaster\w*|doom\w*|curse[ds]?|terror\w*|fatal\w*|"
    r"unlucky|lucky|scores?|scored|percentage|percent|points|guaranteed|gems?|gemstones?|precious stones?|crystals?|"
    r"yantras?|pyramids?|talismans?|products?|paid pujas?|not\s+compatible)\b|[%％]|\d\s*/\s*\d|"
    r"मृत्यु|मौत|दुर्घटन|डरावन|भय|विनाश|श्राप|शाप|तबाही|गारंटी|भाग्यशाली|बदकिस्मत|प्रतिशत|"
    r"रत्न|क्रिस्टल|पिरामिड|उत्पाद|अनुकूल नहीं|असंगत|स्कोर|"
    r"ಸಾವು|ಮರಣ|ಅಪಘಾತ|ಭಯ|ಶಾಪ|ದುರಂತ|ಖಾತರಿ|ದುರಾದೃಷ್ಟ|ಅದೃಷ್ಟಶಾಲಿ|ಶೇಕಡಾ|ರತ್ನ|ಸ್ಫಟಿಕ|ಪಿರಮಿಡ್|ಉತ್ಪನ್ನ|ಹೊಂದಾಣಿಕೆ ಇಲ್ಲ|ಸ್ಕೋರ್", re.I)
TONES = {'Supportive','Steady','Take care'}


def mappings(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from mappings(child)
    elif isinstance(value, list):
        for child in value:
            yield from mappings(child)


def validate_consistency(rules, read, require, root):
    registry = read('governance/review/rule-aliases.yaml')
    for kind, aliases in registry.items():
        for source, target in aliases.items():
            require(source in rules and target in rules and target not in aliases, source+' invalid alias')
            if kind == 'copy_aliases':
                require(rules[source]['user_text'] == rules[target]['user_text'],source+' copy alias drift')
            elif source != 'vedic.doshas.ashtama-shani':
                require(rules[source]['conditions'] == rules[target]['conditions'],source+' evidence alias drift')
            else:
                first, second = (rules[i]['conditions']['all'][0] for i in (source,target))
                require(first['fact']==second['fact'] and first['value']==[second['value']]==[8], source)
    profiles = read('shared/conventions/profiles.yaml')['calculation_profiles']
    vedic, kp, western = (profiles[k] for k in ('vedic-lahiri-v1','kp-placidus-v1','western-tropical-v1'))
    require((vedic['zodiac'],vedic['houses'],vedic['ayanamsa'],vedic['sidereal_mode']) ==
            ('sidereal','whole-sign','Lahiri',1),'Vedic convention')
    require((kp['zodiac'],kp['houses'],kp['ayanamsa_family'],kp['sidereal_mode']) ==
            ('sidereal','placidus','KP',5),'KP convention')
    west = read('western/profile.yaml')
    require(west['zodiac']==western['zodiac']=='tropical' and west['houses']['default']==western['houses']=='placidus'
            and western['house_options']==list(west['houses']['systems']),'Western convention')
    require(set(read('SCHEMA.yaml')['user_tones'])==TONES,'tone registry')
    doctrines = read('shared/conventions/profiles.yaml')['doctrine_profiles']
    ids = set()
    incoming = defaultdict(set)
    facts = read('shared/fact-dictionary/catalog.yaml')['facts']
    producers = {f.get("producer") for f in facts.values()}
    namespaces = {r['system'] for r in rules.values()} | {'glossary','remedies'}
    literal = re.compile(r'(?<![\w.-])(?:'+'|'.join(sorted(namespaces))+r')(?:\.[a-z0-9][a-z0-9_-]*){2,}(?![\w-])')
    paths = [p for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and
             p.relative_to(root).as_posix() != 'governance/source-locators.yaml' and p.name != 'REVIEW-REPORT.md' and p.relative_to(root).parts[0] not in ('templates','export','dist-json')]
    typed_refs = []
    for p in paths:
        if p.suffix != '.yaml':
            continue
        doc = yaml.load(p.read_text(),Loader=getattr(yaml,'CSafeLoader',yaml.SafeLoader))
        rid = doc.get('id') if isinstance(doc,dict) else None
        if isinstance(rid,str):
            require(rid not in ids,rid+' duplicate document ID')
            ids.add(rid)
        for item in mappings(doc):
            for field in ('related_rules','reference_rules','used_by','rule_id','related_placement',
                          'reciprocal_placement','linked_to','numerology_ids','related_rule','phase_links'):
                values = item.get(field,[])
                for ref in (values if isinstance(values,list) else [values]):
                    if isinstance(ref,str) and p.name != 'SCHEMA.yaml':
                        typed_refs.append((p,ref))
            if 'en' in item and isinstance(item['en'],str):
                require(all(isinstance(item.get(loc),str) and item[loc].strip() for loc in MODAL),str(p)+' locales')
            if 'tone_resolution' in item and isinstance(item['tone_resolution'],dict):
                require(set(item['tone_resolution'].values())==TONES,str(p)+' checker tone values')
            if 'tone' in item and isinstance(item['tone'],str):
                require(item['tone'] in TONES,str(p)+' tone')
            if 'user_text' in item and isinstance(item['user_text'],dict):
                copy=item['user_text']
                for loc,modal in MODAL.items():
                    line=copy.get(loc,'')
                    require(re.search(modal,line,re.I) and not BLOCKED.search(line),str(p)+' user_text.'+loc)
    for path,ref in typed_refs:
        require(ref in ids,str(path)+' unresolved ID '+ref)
    for rid,r in rules.items():
        convention={'vedic':'vedic-lahiri-v1','jaimini':'vedic-lahiri-v1','kp':'kp-placidus-v1','western':'western-tropical-v1'}.get(r['system'])
        if convention:
            require(doctrines[r['doctrine_profile']].get('calculation')==convention,rid+' convention')
    for p in paths:
        s=p.read_text()
        owner=re.search(r'^id: ([\w.-]+)$',s,re.M)
        for m in literal.finditer(s):
            key=m[0]
            if key in ids:
                if (not owner or owner[1]!=key) and p.suffix != '.py':
                    incoming[key].add(p)
            elif key not in facts and key not in producers:
                # Finite ID patterns in schema/engine code are expanded by their module validators.
                tail=s[m.end():m.end()+1]
                prefix=key.endswith('-') or key=='vedic.vargas.d'
                require(prefix and (tail in ('{','N',"'",'"') or p.suffix=='.py'),str(p)+' unresolved '+key)
    require(all(incoming[key] for key in rules),'unreferenced rules: '+str([key for key in rules if not incoming[key]]))
    return incoming
