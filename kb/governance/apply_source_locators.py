"""Reapply Jyoti's locator decisions. Run from any directory inside a full checkout."""
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import Path
import subprocess
import tarfile

import yaml

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / 'kb/governance/source-locators.yaml'


def load(text):
    return yaml.load(text, Loader=yaml.CSafeLoader)


def assignments(mapping):
    for area in mapping['areas']:
        for row in area['entries']:
            if row.get('decision') == 'exclude from audit':
                continue
            if 'paths' in row:
                for name, rid in zip(row['paths'], row['rule_ids'], strict=True):
                    yield str(Path(row['path']) / name), rid, row
            else:
                yield row['path'], row.get('rule_id'), row
    for row in mapping['meta']['nested_pending_not_counted']:
        yield row['path'], None, row


WORKS = {'Brihat Jataka': 'brihat-jataka', 'Brihat Parashara': 'bphs',
         'Brihat Samhita': 'brihat-samhita', 'Phaladeepika': 'phaladeepika',
         'Laghu Parashari': 'laghu-parashari', 'Tetrabiblos': 'ptolemy-tetrabiblos',
         'KP Reader VI': 'kp-readers', 'Timing Events': 'rao-timing-events'}
EDITIONS = {'phaladeepika': 'phaladeepika-sastri-1950', 'brihat-jataka': 'brihat-jataka-iyer-brihatjataka00varaiala',
            'waite-pictorial-key': 'waite-1910', 'cheiro-palmistry': 'cheiro-pg20480',
            'prashna-marga': 'prashna-marga-raman', 'prasna-tantra': 'prasna-tantra-raman',
            'muhurta-chintamani': 'muhurta-chintamani-miu', 'rao-integrated': 'rao-integrated-online'}


def citation(row, old):
    editorial = row['tag'] == 'EDITORIAL' or row.get('decision') in ('re-tag editorial', 'retire rule')
    book = None if editorial else row['book']
    work = next((v for k,v in WORKS.items() if book and book.startswith(k)), row.get('current_work_id'))
    state = 'editorial' if editorial else {'high':'verified_locator','medium':'locator_medium',
                                           'to_verify':'pending'}[row['confidence']]
    chapter = None if editorial else row['chapter']
    result = dict(book=book, work_id=None if editorial else work,
                  edition=EDITIONS.get(work) if book and row['translator_edition'] else None,
                  chapter=chapter, verse=None, other_locator=None,
                  supports=('Bhava360 editorial convention.' if editorial else
                            row.get('note') or old.get('supports') or 'Named calculation or classification.'),
                  verification=state, tag='EDITORIAL' if editorial else row['tag'])
    if book:
        result['translator_edition'] = row['translator_edition']
        if not row['translator_edition']:
            result['edition_to_verify'] = True
        if 'locator' in old:
            result['locator'] = chapter
    if state == 'locator_medium':
        result['locator_note'] = 'Chapter or section numbering follows the named source and may differ by edition.'
    if state == 'pending':
        result['to_verify'] = True
    if row['path'].endswith('special-lagnas/calculations.yaml') or (
            'special-lagnas' in row['path'] and 'calculations.yaml' in row.get('paths', [])):
        result['locator_note'] = 'Compare chapter 3 with chapters 4–5 in Santhanam before accepting the locator.'
    return result


def child(node, key):
    return next(v for k,v in node.value if k.value == key)


def replace_block(text, node, record):
    start,end = node.start_mark.index,node.end_mark.index
    end = start + len(text[start:end].rstrip())
    formatted = yaml.safe_dump(record, allow_unicode=True, sort_keys=False,
                               default_flow_style=bool(node.flow_style), width=120 if not node.flow_style else 100000).strip()
    return start,end,formatted.replace('\n','\n'+' '*node.start_mark.column)


def apply():
    mapping = load(MAP.read_text())
    groups = defaultdict(list)
    for path, rid, row in assignments(mapping):
        groups[path].append((rid,row))
    archive = subprocess.check_output(['git','archive',mapping['meta']['base_sha'],'--',*sorted(groups)],cwd=ROOT)
    with tarfile.open(fileobj=BytesIO(archive)) as tar:
        bases = {path:load(tar.extractfile(path).read()) for path in groups}
    writes = {}
    counts = Counter()
    for name, rows in groups.items():
        path = ROOT / name
        if not path.is_file():
            ids = {rid for rid,row in rows if rid and not rid.startswith('(')}
            matches = [p for p in (ROOT/'kb').rglob('*.yaml') if load(p.read_text()).get('id') in ids]
            if len(matches)!=1:
                raise ValueError(f'Unmatched moved path: {name}')
            path = matches[0]
        text = path.read_text()
        document = load(text)
        tree = yaml.compose(text, Loader=yaml.CSafeLoader)
        changes = []
        claimed = set()
        for rid,row in rows:
            if rid and not rid.startswith('(') and document.get('id')!=rid:
                raise ValueError(f'{name}: mismatched rule {rid}')
            base, current, node = bases[name], document, tree
            keys = row.get('at','').strip('.').split('.') if row.get('at') else []
            for key in [*keys,'sources']:
                base,current,node = base[key],current[key],child(node,key)
            indices = [i for i,src in enumerate(base) if src.get('verification')=='pending' and
                       src.get('work_id')==row.get('current_work_id')]
            if len(indices)==2 and 'vimshottari/' in name and name.endswith('-house-lord.yaml'):
                house_topic = row['chapter'].startswith('ch.11')
                indices = [i for i in indices if ('Chapter 11' in str(base[i].get('other_locator'))) == house_topic]
            if len(indices)!=1:
                raise ValueError(f'{name}: ambiguous base locator {indices}')
            i, = indices
            record = citation(row,base[i])
            block = (tuple(keys),i)
            # Later review may have refined a pending locator on the same work.
            # Preserve that evidence separately from the map's edition-specific chapter.
            original = base[i]
            locator_keys = ('chapter','other_locator')
            if current[i].keys() == original.keys() and current[i].get('verification') == 'pending' and all(
                    current[i].get(k) == original.get(k) for k in original if k not in locator_keys):
                prior = {k:current[i][k] for k in locator_keys if current[i].get(k)!=original.get(k)}
                if prior:
                    record['prior_review_locator'] = prior
                    base[i] = current[i]
            elif 'prior_review_locator' in current[i]:
                record['prior_review_locator'] = current[i]['prior_review_locator']
            if block in claimed or current[i] not in (base[i],record):
                raise ValueError(f'{name} {block}: duplicate assignment or independently edited citation')
            claimed.add(block)
            counts[record['verification']]+=1
            if current[i]!=record:
                changes.append(replace_block(text,node.value[i],record))
                current[i] = record
        for start,end,value in sorted(changes,reverse=True):
            text = text[:start]+value+text[end:]
        if load(text)!=document:
            raise ValueError(f'{name}: YAML round-trip failed')
        if changes:
            writes[path] = text
    for path,text in writes.items():
        path.write_text(text)
    print(f'{len(writes)} files changed; mapped citations: {dict(sorted(counts.items()))}')


if __name__ == '__main__':
    apply()
