"""Count verification-bearing source blocks in authored YAML, including nested option tables."""
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def citations(value):
    if isinstance(value, dict):
        sources = value.get('sources')
        if isinstance(sources,list):
            for source in sources:
                if isinstance(source,dict) and 'verification' in source:
                    yield source
        for child in value.values():
            yield from citations(child)
    elif isinstance(value,list):
        for child in value:
            yield from citations(child)


def inventory(root=ROOT):
    counts = Counter()
    for path in sorted(root.rglob('*.yaml')):
        rel = path.relative_to(root)
        if rel.parts[0] in ('templates','dist-json') or str(rel)=='governance/source-locators.yaml':
            continue
        for source in citations(yaml.load(path.read_bytes(),Loader=yaml.CSafeLoader)):
            state = source['verification']
            if state=='pending' and source.get('to_verify') is not True:
                raise ValueError(f'{rel}: pending source lacks to_verify: true')
            if state in ('verified_locator','locator_medium') and (
                    not source.get('work_id') or not source.get('chapter') or source.get('verse') is not None
                    or state=='locator_medium' and not source.get('locator_note')):
                raise ValueError(f'{rel}: incomplete mapped locator')
            counts[state]+=1
    return dict(sorted(counts.items()))


def validate_baseline(mapping, expected, rules):
    reading = other = templates = 0
    for area in mapping['areas']:
        for row in area['entries']:
            ids = row.get('rule_ids', [row.get('rule_id')])
            if row['blocks'] != len(ids):
                raise ValueError('Incorrect locator group size: '+row['path'])
            if Path(row['path']).parts[:2] == ('kb','templates'):
                templates += len(ids)
            else:
                reading += sum(rid in rules for rid in ids)
                other += sum(rid not in rules for rid in ids)
    nested = len(mapping['meta']['nested_pending_not_counted'])
    top = reading + other + templates
    actual = dict(reading_rules=reading, other_authored_top_level=other, excluded_templates=templates,
                  mapped_top_level=top,nested_remedies=nested,mapped_authored_total=top-templates+nested)
    if actual != expected or top != mapping['meta']['pending_total']:
        raise ValueError(f'Locator map scope mismatch: {actual}')


def validate(expected):
    observed = inventory()
    if expected != observed:
        raise ValueError(f'Source inventory mismatch: {observed}')
    print('Source blocks by verification:', observed)


if __name__=='__main__':
    print(yaml.safe_dump(inventory(),sort_keys=True),end='')
