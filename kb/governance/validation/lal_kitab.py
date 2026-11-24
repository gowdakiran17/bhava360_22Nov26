"""Check edition-specific page references and the scope of the gated 1952 study."""
from collections import Counter


def validate(read,require):
    bodies = 'sun moon mars mercury jupiter venus saturn rahu ketu'.split()
    placement = 'lal-kitab/placements/'
    paths = [placement+f'{b}-house-{h}.yaml' for b in bodies for h in range(1,13)]
    paths += [placement+f'house-{h}.yaml' for h in range(1,13)]
    paths += ['lal-kitab/fixed-houses/house-reference.yaml','lal-kitab/varshphal/year-house.yaml',
              placement+'evidence.yaml','lal-kitab/varshphal/annual.yaml']
    registry = read('shared/source-editions/catalog.yaml')['editions']
    primary = 'lal-kitab-joshi-1952-nagpal-2016'
    translation = 'lal-kitab-goswami-vashisth-english'
    totals = Counter()
    for path in paths:
        row = read(path)
        first,second = row['sources']
        for citation,edition in ((first,primary),(second,translation)):
            require(citation['edition']==edition and registry[edition]['work_id']==citation['work_id']
                    and citation['pdf_page'] and citation['verse'] is None,path+' edition page')
        require(row['approval']=='draft' and row['native_review_needed'] is True and
                row['native_review']==dict(kn='pending',hi='pending'),path+' draft review')
        expected = 'locator_medium' if path.endswith('/year-house.yaml') else 'verified_locator'
        require(first['verification']==expected and first['printed_page'],path+' primary locator status')
        approx = second['locator_note'].startswith('approx')
        require(second['verification']==('pending' if approx else 'verified_locator') and
                bool(second.get('to_verify'))==approx,path+' secondary status')
        totals['approximate'] += approx
        totals['disputed'] += any(n['note'].startswith('Expert comparison') for n in row.get('traditions_differ',[]))
    require(totals=={'approximate':36,'disputed':49},'1952 locator review coverage')
    evidence = read(placement+'evidence.yaml')
    require(evidence['pakka_ghar']['jupiter']==[2,5,9,11,12] and evidence['pakka_status']=='edition-located'
            and evidence['pakka_ghar']['ketu']==[6] and evidence['pakka_ghar']['mercury']==[7],
            '1952 pakka chart and alternate shared sixth house')
    conduct = read(placement+'saturn-house-3.yaml')['remedy']
    require([conduct]==evidence['accepted_conduct'] and conduct['attribution']=='editorial' and
            conduct['optional'] and conduct['free'] and conduct['label']=='traditional-practice','listening practice')
    annual = read('lal-kitab/varshphal/annual.yaml')
    require(annual['edition']==primary and annual['edition_rows']=={} and annual['verification']=='pending-double-entry',
            'untranscribed annual rows')
    print('Lal Kitab passed: 124 primary and secondary locators, 36 approximate English pages, 49 review differences.')
