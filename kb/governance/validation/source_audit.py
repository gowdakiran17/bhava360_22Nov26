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


def validate(expected):
    observed = inventory()
    if expected != observed:
        raise ValueError(f'Source inventory mismatch: {observed}')
    print('Source blocks by verification:', observed)


if __name__=='__main__':
    print(yaml.safe_dump(inventory(),sort_keys=True),end='')
