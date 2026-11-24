"""Assign or refresh internal rule metadata on a KB checkout. Run from any directory."""
from collections import defaultdict
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[2]
SYSTEMS = 'face-reading jaimini kp lal-kitab numerology palmistry tarot vastu vedic western'.split()
SUPPORT = dict(sun=[3,6,10,11],moon=[1,3,6,7,10,11],mars=[3,6,11],mercury=[2,4,6,8,10,11],
               jupiter=[2,5,7,9,11],venus=[1,2,3,4,5,8,9,11,12],saturn=[3,6,11],rahu=[3,6,11],ketu=[3,6,11])
TONE = {'Supportive':'support','Steady':'neutral','Take care':'caution'}


def load(path):
    return yaml.load(path.read_text(), Loader=getattr(yaml,'CSafeLoader',yaml.SafeLoader))


def classify(r, recipes, slow):
    system,topic,slug = r['system'],r['topic'],r['id'].split('.')[-1]
    direction, weight, scope, ref = 'context','context','static','none'
    note = reason = None
    areas = r['life_areas']
    relevance = {key:'core' if len(areas)==1 else 'related' for key in areas}
    if system in ('vedic','western','kp','jaimini','lal-kitab'):
        scope = 'natal'
    if topic in ('transits','returns','solar-arc','progressions','annual-chart','varshphal'):
        scope = 'transit'
    if topic in ('panchang','festivals'):
        scope = 'day'
    if topic in ('muhurta','prashna','number-horary','matching','synastry','composite','relocation'):
        scope = 'event'
    if topic in ('nakshatras','padas') and slug in ('born-pada','born-star'):
        ref='moon'
    if 'dasha' in topic:
        scope = 'dasha'
    if topic.startswith('dashas/') and slug.startswith('check-'):
        # Checker linkage must never turn a period rule into an independent vote.
        return dict(direction='context',weight_class='context',time_scope='dasha',reference=ref,
                    area_strength=relevance),None,None
    if system in ('tarot','palmistry','face-reading'):
        scope = 'event' if system=='tarot' else 'static'
    elif r['id'] in recipes:
        scope = 'event'
        direction = recipes[r['id']]
        if direction=='ruler-matrix':
            direction='context'
            reason='Resolve the candidate and birth roots against the directed compatibility table.'
        weight = 'context' if direction=='context' and not reason else 'secondary'
    elif system=='vastu' and r.get('vastu',{}).get('tone') in TONE:
        direction = TONE[r['vastu']['tone']]
        weight = 'secondary'
    elif topic=='transits' and ('-moon-house-' in slug or slug=='saturn-moon'):
        planet, house = ('saturn','1') if slug=='saturn-moon' else slug.split('-moon-house-')
        direction = 'support' if int(house) in SUPPORT[planet] else 'caution'
        weight = 'primary' if planet in slow else 'secondary'
        ref='moon'
        if slug in ('venus-moon-house-8','venus-moon-house-12'):
            note='KB-35 selects support before modifiers; the source documents mixed indications.'
        if slug=='jupiter-moon-house-5':
            relevance['learning']='core'
    elif topic=='planets-in-signs':
        kind = r['placement']['dignity']['sign_class']
        ref = 'none'
        if kind in ('debilitated','own','exalted','moolatrikona'):
            direction='caution' if kind=='debilitated' else 'support'
            weight='secondary'
        else:
            reason=('Node sign dignity is disputed and unassigned.' if kind=='disputed' else
                    'Compound friendship requires the D1 sign of the occupied sign lord.')
            if kind!='disputed':
                weight='secondary'  # eligible once compound friendship resolves
        if slug=='saturn-aries':
            relevance['career']='core'
    elif topic=='house-lords':
        h=r['house_pair']['occupied_house']
        ref,weight='lagna','primary'
        direction='support' if h in (1,4,5,7,9,10) else 'caution' if h in (6,8,12) else 'neutral'
        if h in (6,8,12) and r['house_pair']['source_house'] in (6,8,12):
            yoga={6:'harsha',8:'sarala',12:'vimala'}[r['house_pair']['source_house']]
            note='Test vedic.yogas.'+yoga+' before synthesizing this dusthana placement.'
    elif topic in ('yogas','raja-yogas','doshas'):
        caution=topic=='doshas' or slug in ('sakata','kemadruma','parivartana-dainya')
        direction,weight=('caution' if caution else 'support'),'primary'
        if slug in ('sade-sati','ashtama-shani'):
            scope='transit'
        if slug in ('bhakoot','nadi'):
            scope='event'
        ref='moon' if slug in ('kemadruma','sakata','sade-sati','ashtama-shani','bhakoot','nadi','sunapha','anapha','durudhara','gaja-kesari','adhi') else 'none'
        if slug=='kemadruma':
            relevance['family-home']='core'
    elif topic=='planets-in-houses' or topic=='lordships':
        ref='lagna'
    elif topic=='states' and slug in ('combustion','vargottama'):
        direction,weight=('caution' if slug=='combustion' else 'support'),'modifier'
    elif topic=='prashna' and slug in ('leans-toward','leans-against','mixed'):
        direction={'leans-toward':'support','leans-against':'caution','mixed':'neutral'}[slug]
        weight='secondary'
    elif topic=='muhurta' and slug.startswith('window-'):
        direction={'window-take-care':'caution','window-steady':'neutral','window-supportive':'support'}[slug]
        weight='primary'
    elif system=='western' and (topic=='aspects' or topic in ('transits','progressions') and '-contact-' in slug) and (slug=='saturn-square-sun' or slug.split('-')[-1] in ('square','opposition','trine','sextile')):
        direction='support' if slug.split('-')[-1] in ('trine','sextile') else 'caution'
        weight='secondary'
    elif topic=='transits' and slug in ('vedha-obstruction','ashtama-shani','kantaka-shani','sade-sati-rising','sade-sati-middle','sade-sati-closing'):
        direction,weight,ref='caution','modifier','moon'
    if direction=='context' and scope=='natal' and topic in ('natal','planets-in-houses','placements'):
        reason='Chart placement supplies a theme; a single direction requires chart-specific corroboration.'
    if system=='vedic' and ref=='none':
        if topic=='yogas' and slug in ('vesi','vosi','ubhayachari'):
            ref='sun'
        elif topic=='yogas' and slug in ('hamsa','bhadra','ruchaka','shasha','malavya','harsha','sarala','vimala','vasumati'):
            # Vasumati permits either the Lagna or Moon; there is no single fixed origin.
            ref='none' if slug=='vasumati' else 'lagna'
        elif topic=='houses' and re.fullmatch(r'(?:house-\d+|\w+-house-\d+)',slug):
            ref='lagna'
    # An area named by the rule itself is the direct target of this observation.
    for area in areas:
        if slug == area or slug.startswith(area+'-'):
            relevance[area]='core'
    if system=='vastu' and topic=='rooms' and 'property-vehicles' in areas:
        relevance['property-vehicles']='core'
    if reason:
        note=reason+' Retain context pending resolution.'
    return dict(direction=direction,weight_class=weight,time_scope=scope,reference=ref,area_strength=relevance),note,reason


def main():
    recipes={}
    for path in sorted((ROOT/'checkers').glob('*/recipe.yaml')):
        for row in load(path)['explain_rules']:
            key=row['rule_id']
            if recipes.setdefault(key,row['direction'])!=row['direction']:
                raise ValueError('Conflicting checker directions: '+key)
    slow=load(ROOT/'vedic/transits/evidence.yaml')['groups']['long']
    pending=defaultdict(list)
    for system in SYSTEMS:
        for path in sorted((ROOT/system).rglob('*.yaml')):
            row=load(path)
            if not isinstance(row,dict) or 'rule' not in row or 'system' not in row:
                continue
            ev,note,reason=classify(row,recipes,slow)
            if reason:
                pending[reason].append(row['id'])
            source=path.read_text()
            # This migration owns the top-level evidence map only.
            source=re.sub(r'^evidence:\n(?:  [^\n]*\n)*','',source,flags=re.M)
            if note and note not in row['review_notes']:
                start=source.index('review_notes:')
                line_end=source.index('\n',start)+1
                end=re.search(r'^\w[\w-]*:',source[line_end:],re.M)
                stop=line_end+end.start() if end else len(source)
                source=source[:start]+yaml.safe_dump({'review_notes':row['review_notes']+' '+note},allow_unicode=True,width=120)+source[stop:]
            block=yaml.safe_dump({'evidence':ev},sort_keys=False,allow_unicode=True)
            updated=source.rstrip()+'\n'+block
            if path.read_text()!=updated:
                path.write_text(updated)
    (ROOT/'governance/review/evidence-direction-review.yaml').write_text(yaml.safe_dump(
        dict(approval='draft',unresolved={reason:sorted(ids) for reason,ids in sorted(pending.items())}),
        sort_keys=False,width=120))


if __name__=='__main__':
    main()
