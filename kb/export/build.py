"""Export the committed Bhava360 authoring corpus. Run with Python 3.10+."""
import argparse
from collections import defaultdict
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
from tempfile import TemporaryDirectory

from jsonschema import Draft202012Validator
import yaml

from routes import routing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SYSTEMS = 'face-reading jaimini kp lal-kitab numerology palmistry tarot vastu vedic western'.split()
FORMAT = 1
INPUT_PATHS = [f'kb/{name}' for name in [*SYSTEMS,'SCHEMA.yaml','checks','checkers','glossary',
               'governance/release-flags','governance/review','life-areas','modules','remedies','shared']]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def snapshot(commit):
    blob = git('archive', '--format=tar', commit, *INPUT_PATHS)
    docs = {}
    with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
        for item in archive:
            if item.isfile() and item.name.endswith(('.yaml','.svg')):
                content = archive.extractfile(item).read().decode()
                docs[item.name[3:]] = (yaml.load(content, Loader=getattr(yaml,'CSafeLoader',yaml.SafeLoader))
                                       if item.name.endswith('.yaml') else content)
    return docs


def json_value(value):
    if isinstance(value, list):
        return [json_value(x) for x in value]
    if isinstance(value, dict):
        obj = {}
        for key, child in value.items():
            name = str(key).lower() if isinstance(key,bool) else str(key)
            if name in obj:
                raise ValueError(f'Duplicate JSON key {name}')
            obj[name] = json_value(child)
        return obj
    if isinstance(value, date):
        return value.isoformat()
    return value


def encoded(value):
    return (json.dumps(json_value(value), ensure_ascii=False, sort_keys=True, separators=(',',':'),
                       allow_nan=False) + '\n').encode()


def token(kind, name):
    return kind + '_' + hashlib.sha256(name.encode()).hexdigest()[:24]


class Messages:
    def __init__(self, settings):
        self.required = settings['required']
        self.bundles = {loc:{} for loc in self.required + settings['planned']}
        self.fallback = settings['fallback']

    def add(self, name, translations):
        key = token('m',name)
        if not all(isinstance(translations.get(loc),str) and translations[loc].strip() for loc in self.required):
            raise ValueError('Missing required translation: '+name)
        for locale, bundle in self.bundles.items():
            if key in bundle:
                raise ValueError('Repeated public message: '+name)
            word = translations.get(locale)
            bundle[key] = word if isinstance(word,str) and word.strip() else translations[self.fallback]
        return key


def practice(messages, name, remedy):
    if remedy['optional'] is not True or remedy['cost'] != 'free':
        raise ValueError('Unexpected remedy policy: '+name)
    return {'optional':True,'cost':'free','type':remedy['type'],
            'user_text':messages.add(name,remedy['user_text'])}


def canonical_refs(value, aliases):
    if isinstance(value, list):
        return [canonical_refs(v,aliases) for v in value]
    if isinstance(value, dict):
        # Citation locators identify the historical text that was reviewed.
        return {k:(v if k=='sources' else canonical_refs(v,aliases)) for k,v in value.items()}
    return aliases.get(value,value) if isinstance(value,str) else value


def public_resources(docs, messages):
    catalog = {}
    bindings = {}

    def bind(name, record):
        key = token('p',name)
        if key in catalog:
            raise ValueError('Duplicate public resource: '+name)
        catalog[key] = record
        bindings[name] = key
    for path, doc in sorted(docs.items()):
        if path.startswith('glossary/entries/'):
            public = {k:messages.add(path+'/'+k,doc[k]) for k in ('term','meaning')}
        elif path.startswith('remedies/') and isinstance(doc,dict) and 'remedy' in doc:
            public = {'remedy':practice(messages,path,doc['remedy']),
                      'options':{k:practice(messages,path+'/'+k,v) for k,v in doc.get('options',{}).items()}}
        elif path.startswith('life-areas/') and 'summaries' in doc:
            public = {'summaries':{k:messages.add(path+'/'+k,v['user_text']) for k,v in doc['summaries'].items()}}
            if 'always_append' in doc:
                public['footer'] = messages.add(path+'/footer',doc['always_append']['user_text'])
        elif path.startswith('life-areas/') and path.endswith('/reading.yaml'):
            text = doc['slots']['what-you-can-do']
            public = {'user_text':messages.add(path,text)}
        elif path.startswith('checks/') and 'user_text' in doc.get('public',{}):
            public = {'user_text':messages.add(path,doc['public']['user_text'])}
        else:
            continue
        bind(path,public)
    for area, labels in docs['life-areas/catalog.yaml']['areas'].items():
        name = 'life-areas/catalog.yaml#'+area
        bind(name,{'label':messages.add(name,labels)})
    labels = docs['shared/localization/reading.yaml']
    for label in labels['tones']:
        name = 'tone/'+label['en']
        bind(name,{'label':messages.add(name,label)})
    for field in ('footer','reflection','unknown'):
        name = 'shared/localization/reading.yaml#'+field
        bind(name,{'user_text':messages.add(name,labels[field])})
    # Only authored, displayable slots cross the public boundary.
    for path, section, field, member in [
            ('tarot/positions/catalog.yaml','positions','user_text','user_text'),
            ('palmistry/guided-observations/choices.yaml','choices','label','label'),
            ('shared/boundaries/responses.yaml','messages','user_text',None),
            ('vedic/prashna/judgment.yaml','reason_copy','user_text',None),
            ('checkers/personal-baby-name/name-lexicon.yaml','entries','label',None),
            ('vedic/planets/catalog.yaml','grahas','label',None)]:
        for slug, item in docs[path][section].items():
            name = f'{path}#{section}/{slug}'
            bind(name,{field:messages.add(name,item[member] if member else item)})
    for path, group, member in [
            ('vedic/signs/catalog.yaml','signs','labels'),
            ('vedic/vargas/methods.yaml','methods','purpose'),
            ('vedic/strength/shadbala/components.yaml','approved_public_phrases',None)]:
        for index,item in enumerate(docs[path][group]):
            name = f'{path}#{group}/{item.get("id",index)}'
            field = 'label' if member else 'user_text'
            bind(name,{field:messages.add(name,item[member] if member else item)})
    for field in ('label','mantra','conduct','charity'):
        path = 'shared/traditional-practices/options.yaml'
        name = path+'#'+field
        bind(name,{'label' if field=='label' else 'user_text':messages.add(name,docs[path][field])})
    return catalog,bindings


def compile_files(docs, commit):
    settings = docs['SCHEMA.yaml']['supported_locales']
    messages = Messages(settings)
    aliases = docs['governance/review/rule-aliases.yaml']
    evidence, copy = aliases['evidence_aliases'], aliases['copy_aliases']
    by_id, paths = {}, {}
    for path, doc in docs.items():
        if isinstance(doc,dict) and 'rule' in doc and 'system' in doc:
            key = doc['id']
            if key in by_id or doc['system'] not in SYSTEMS:
                raise ValueError('Invalid source rule '+key)
            by_id[key], paths[key] = doc, path
    rule_paths = set(paths.values())
    grouped = defaultdict(list)
    for alias, target in evidence.items():
        if target not in by_id or alias not in by_id or target in evidence:
            raise ValueError('Invalid evidence alias '+alias)
        grouped[target].append(alias)
    for key,target in copy.items():
        if target in evidence or target in copy or by_id[key]['user_text']!=by_id[target]['user_text']:
            raise ValueError('Invalid copy alias '+key)
    routes = routing(by_id, docs, evidence)
    outputs = {}
    counts = {}
    for system in SYSTEMS:
        admin, public, resources = {}, {}, {}
        for key, doc in sorted(by_id.items()):
            if doc['system']!=system or key in evidence:
                continue
            owner = copy.get(key,key)
            public_id = token('p',key)
            text_key = token('m',owner)
            if key==owner:
                messages.add(key,doc['user_text'])
            tones = [v['tone'] for v in doc.values() if isinstance(v,dict) and 'tone' in v]
            public[public_id] = {'user_text':text_key, 'tone':tones[0] if tones else None,
                                 'remedy':practice(messages,key+'/remedy',doc['remedy']) if doc['remedy'] else None}
            record = {k:v for k,v in doc.items() if k not in ('id','user_text','remedy')}
            record['life_areas'] = sorted(set(doc['life_areas']).union(*(by_id[a]['life_areas'] for a in grouped[key])))
            admin[key] = {'aliases':sorted(grouped[key]),'copy_owner':owner,'public_key':public_id,
                          'rule':canonical_refs(record,evidence)}
        for path,doc in docs.items():
            if path.startswith(system+'/') and path not in rule_paths:
                resources[path] = canonical_refs(doc,evidence)
        outputs[f'admin/{system}.json'] = {'system':system,'rules':admin,'resources':resources}
        outputs[f'public/{system}.json'] = {'system':system,'readings':public}
        counts[system] = {'rules':len(admin),'aliases':sum(len(x['aliases']) for x in admin.values())}
    common = {path:canonical_refs(doc,evidence) for path,doc in docs.items()
              if path.split('/')[0] not in SYSTEMS and path!='governance/review/rule-aliases.yaml'}
    resources,bindings = public_resources(docs,messages)
    outputs['public/catalog.json'] = {'entries':resources}
    outputs['admin/catalog.json'] = {'resources':common,'public_keys':bindings}
    outputs['admin/routing.json'] = {'routes':routes}
    for loc,bundle in messages.bundles.items():
        outputs[f'public/locales/{loc}.json'] = {'locale':loc,'messages':bundle}
    total = len(by_id)-len(evidence)
    manifest = {'version':f'1.{commit[:12]}','commit':commit,'schema_version':FORMAT,
                'authoring_schema_version':docs['SCHEMA.yaml']['version'],'locales':settings,
                'conventions':docs['shared/conventions/profiles.yaml']['calculation_profiles'],
                'counts':{'system_counts':counts,'source_rules':len(by_id),'canonical_rules':total,
                          'evidence_aliases':len(evidence),'copy_aliases':len(copy),'routes':len(routes),
                          'routed_rules':len(set().union(*routes.values())),'messages_per_locale':len(messages.bundles['en'])}}
    return outputs,manifest


def schema_name(path):
    if path=='manifest.json':
        return 'manifest'
    if path.startswith('public/locales/'):
        return 'locale'
    view, filename = path.split('/')
    if filename=='catalog.json':
        return view+'-catalog'
    if path=='admin/routing.json':
        return 'routing'
    return view+'-system'


def validate_outputs(outputs, manifest, docs):
    validators = {}
    for path, value in {**outputs,'manifest.json':manifest}.items():
        name = schema_name(path)
        if name not in validators:
            schema = json.loads((HERE/'schema'/(name+'.json')).read_text())
            Draft202012Validator.check_schema(schema)
            validators[name] = Draft202012Validator(schema)
        error = next(validators[name].iter_errors(value),None)
        if error:
            raise ValueError(f'{path} / {error.json_path}: {error.message[:500]}')

    canonical, historical, public_ids, messages = set(), set(), set(), set()
    for system in SYSTEMS:
        rows = outputs[f'admin/{system}.json']['rules']
        public = outputs[f'public/{system}.json']['readings']
        if set(public)!={r['public_key'] for r in rows.values()}:
            raise ValueError(system+' public projection mismatch')
        if canonical & rows.keys() or public_ids & public.keys():
            raise ValueError(system+' duplicate identity')
        canonical.update(rows)
        public_ids.update(public)
        for key,row in rows.items():
            if row['rule']['system']!=system or row['copy_owner'] not in rows:
                raise ValueError(key+' invalid owner')
            if historical.intersection(row['aliases']):
                raise ValueError(key+' repeated evidence alias')
            historical.update(row['aliases'])
            if public[row['public_key']]['user_text']!=public[rows[row['copy_owner']]['public_key']]['user_text']:
                raise ValueError(key+' shared wording mismatch')
    source = {r['id'] for r in docs.values() if isinstance(r,dict) and 'rule' in r and 'system' in r}
    if canonical & historical or canonical | historical != source:
        raise ValueError('Alias coverage mismatch')
    routes = outputs['admin/routing.json']['routes']
    for name,ids in routes.items():
        if set(ids)-canonical or ids!=sorted(set(ids)):
            raise ValueError('Invalid route '+name)
    if set().union(*(ids for name,ids in routes.items() if name!='screen/admin-tester'))!=canonical:
        raise ValueError('Missing non-admin route')

    def collect(value):
        if isinstance(value,dict):
            for item in value.values():
                collect(item)
        elif isinstance(value,str) and value.startswith('m_'):
            messages.add(value)
    for path,value in outputs.items():
        if path.startswith('public/') and not path.startswith('public/locales/'):
            collect(value)
    for loc in manifest['locales']['required']+manifest['locales']['planned']:
        if set(outputs[f'public/locales/{loc}.json']['messages'])!=messages:
            raise ValueError(loc+' missing or orphan message')
    if set(outputs['admin/catalog.json']['public_keys'].values())!=set(outputs['public/catalog.json']['entries']):
        raise ValueError('Broken public resource bindings')


def source_revision(ref):
    revision = git('rev-parse','--verify','--end-of-options',ref+'^{commit}').decode().strip()
    # A commit containing generated files cannot embed its own hash.
    source_specs = [spec for path in INPUT_PATHS for spec in (
        [path] if path.endswith('.yaml') else [f':(glob){path}/**/*.{ext}' for ext in ('yaml','svg')])]
    return git('log','-1','--format=%H',revision,'--',*source_specs).decode().strip()


def build(commit):
    docs = snapshot(commit)
    outputs, manifest = compile_files(docs,commit)
    files = {path:encoded(doc) for path,doc in outputs.items()}
    manifest['files'] = {path:{'schema':'schema/'+schema_name(path)+'.json','bytes':len(data),
                               'sha256':hashlib.sha256(data).hexdigest()} for path,data in files.items()}
    # Validate the actual serialized representation, including YAML integer-key tables.
    validate_outputs({p:json.loads(b) for p,b in files.items()},manifest,docs)
    files['manifest.json'] = encoded(manifest)
    return files


def publish(files, dest, check):
    import fcntl
    import os
    # Serialize concurrent directory swaps without creating a tracked lock file.
    fd = os.open(HERE,os.O_RDONLY)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX)
        current = {p.relative_to(dest).as_posix() for p in dest.rglob('*') if p.is_file()}
        if check:
            if current!=files.keys() or any((dest/p).read_bytes()!=b for p,b in files.items()):
                raise ValueError('Checked-in distribution differs from rebuilt files')
            return
        if current-files.keys():
            raise ValueError('Unexpected files in output directory: '+str(sorted(current-files.keys())))
        with TemporaryDirectory(prefix='.kb-json-',dir=dest.parent) as tmp:
            stage = Path(tmp)/'new'
            backup = Path(tmp)/'previous'
            for path,data in files.items():
                target = stage/path
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(data)
            if dest.exists():
                dest.rename(backup)
            try:
                stage.rename(dest)
            except BaseException:
                if backup.exists():
                    backup.rename(dest)
                raise
    finally:
        os.close(fd)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',default='HEAD',help='Committed authoring snapshot')
    parser.add_argument('--check',action='store_true',help='Compare a rebuild with the existing distribution')
    args = parser.parse_args()
    revision = source_revision(args.revision)
    files = build(revision)
    publish(files,HERE.parent/'dist-json',args.check)
    print(f'{revision}: {len(files)} validated files, {sum(map(len,files.values())):,} bytes')
