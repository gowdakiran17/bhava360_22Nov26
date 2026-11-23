"""Vimshottari reference calculation using exact elapsed seconds on a UTC timeline."""
from datetime import datetime, timedelta, timezone
from fractions import Fraction

PREFIX = 'vedic.dashas-vimshottari.'
FACT = 'dasha.vimshottari.'
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def instant(value):
    delta = datetime.fromisoformat(value.replace('Z', '+00:00')) - EPOCH
    return Fraction(delta // timedelta(microseconds=1), 1000000)


def stamp(seconds):
    date = EPOCH + timedelta(microseconds=round(seconds * 1000000))
    return date.isoformat().replace('+00:00', 'Z')


def birth_period(table, birth, arcseconds, convention):
    width = table['star_width_arcseconds']
    star, used = divmod(Fraction(arcseconds) % (360*3600), width)
    lord = table['lord_order'][star % 9]
    year = Fraction(table['year_days'][convention]) * 86400
    duration = year * table['sequence'][lord]
    start = instant(birth) - duration * used / width
    return lord, start, start + duration


def divide(table, first_lord, start, end):
    order = table['lord_order']
    first = order.index(first_lord)
    cursor = start
    for lord in order[first:] + order[:first]:
        stop = cursor + (end-start)*table['sequence'][lord]/table['cycle_years']
        yield lord,cursor,stop
        cursor = stop


def active_path(table, birth, moon, convention, at):
    lord,start,_ = birth_period(table,birth,moon,convention)
    cycle = Fraction(table['year_days'][convention])*86400*table['cycle_years']
    start += ((at-start)//cycle)*cycle
    end = start+cycle
    path = {}
    for level in table['levels']:
        lord,start,end = next(row for row in divide(table,lord,start,end) if row[1]<=at<row[2])
        path[level] = (lord,start,end)
    return path


def validate_vimshottari(rules, read, evaluate, require):
    table = read('vedic/dashas/vimshottari/periods.yaml')
    seq = table['sequence']
    order = table['lord_order']
    require(list(seq)==order=='ketu venus sun moon mars rahu jupiter saturn mercury'.split()
            and list(seq.values())==[7,20,6,10,7,18,16,19,17]
            and sum(seq.values())==table['cycle_years']==120,'Vimshottari cycle')
    cal = read('shared/conventions/profiles.yaml')['calculation_profiles']['vedic-lahiri-v1']['vimshottari_year_days']
    years = table['year_days']
    require(float(years[table['default_year']])==cal['proposed_default']==365.2425
            and int(years['savana'])==cal['alternative']==360,'Vimshottari clocks')
    require(table['levels']==['maha','antar','pratyantar','sookshma'],'Vimshottari levels')
    stars = read('vedic/nakshatras/catalog.yaml')
    width = table['star_width_arcseconds']
    require(width==stars['width_arcseconds']==48000,'star width')
    fixture = read('examples/vimshottari-reference.yaml')
    require(fixture['synthetic'] is True and set(fixture['fixtures'])=={'Asha','Ravi'},'synthetic dates')
    for name,case in fixture['fixtures'].items():
        birth = case['birth']
        moon = case['moon_arcseconds']
        require(set(case['expected'])==set(years),name+' year coverage')
        for convention,expected in case['expected'].items():
            first,start,end = birth_period(table,birth,moon,convention)
            require([stamp(start),stamp(end)]==[expected['birth_maha_start'],expected['birth_maha_end']],name+' birth balance')
            at = instant(expected['query'])
            path = active_path(table,birth,moon,convention,at)
            require(list(expected['path'])==table['levels'],name+' complete path')
            for level,(lord,left,right) in path.items():
                row = expected['path'][level]
                require([lord,stamp(left),stamp(right)]==[row['lord'],row['start'],row['end']],name+' '+convention+' '+level)
                require(active_path(table,birth,moon,convention,left)[level]==(lord,left,right)
                        and active_path(table,birth,moon,convention,right)[level][1]==right,name+' interval ownership')
            # The full parent governs subdivision even if only the post-birth portion is displayed.
            at_birth = active_path(table,birth,moon,convention,instant(birth))
            require(at_birth['maha']==(first,start,end) and at_birth['antar'][0]==('venus' if name=='Asha' else first),name+' birth Antar')
    # Resolve the selected sample against actual KB-06/07/08 IDs, including the node's ruler.
    ctx = fixture['fixtures']['Asha']['sample_context']
    signs = read('vedic/signs/catalog.yaml')['signs']
    names = [s['id'] for s in signs]
    rulers = [s['lord'] for s in signs]
    patterns = table['lookup_patterns']
    lagna = names.index(ctx['lagna'])
    for lord,expected in ctx['expected'].items():
        sign = ctx['natal_signs'][lord]
        occupied = (names.index(sign)-lagna)%12+1
        refs = [patterns['occupied_house'].format(lord=lord,occupied_house=occupied),
                patterns['sign'].format(lord=lord,sign=sign)]
        for house in range(1,13):
            if rulers[(lagna+house-1)%12]==lord:
                refs.append(patterns['ruled_house'].format(owned_house=house,occupied_house=occupied))
        if lord in ('rahu','ketu'):
            dispositor = rulers[names.index(sign)]
            refs.append(patterns['node_dispositor'].format(dispositor=dispositor,
                         dispositor_sign=ctx['natal_signs'][dispositor]))
        require(refs==expected and all(ref in rules for ref in refs),'sample natal context '+lord)
    for i,star in enumerate(stars['nakshatras']):
        birth = fixture['fixtures']['Asha']['birth']
        at_edge = birth_period(table,birth,i*width,table['default_year'])
        before = birth_period(table,birth,i*width-Fraction(1,1000),table['default_year'])
        require(at_edge[0]==star['vimshottari_lord'] and at_edge[1]==instant(birth)
                and before[0]==stars['nakshatras'][i-1]['vimshottari_lord'],'nakshatra boundary '+star['id'])
    antar = {rid:r for rid,r in rules.items() if rid.startswith(PREFIX) and rid.endswith('-antar')}
    require(len(antar)==81,'ordered Antar pair coverage')
    for maha in order:
        require(PREFIX+maha+'-maha' in rules,'missing major lord')
        for child in order:
            facts = {FACT+'maha_lord':maha, FACT+'antar_lord':child, FACT+'pair_context_ready':True}
            selected = [r['id'] for r in antar.values() if evaluate(r['conditions'],facts) is True]
            require(selected==[PREFIX+maha+'-'+child+'-antar'],'bound pair')
            del facts[FACT+'pair_context_ready']
            require(evaluate(rules[selected[0]]['conditions'],facts) is None,'unbound natal context')
    print('Vimshottari passed: 4 reference timelines, 16 nested intervals, 27 star boundaries and 81 ordered lord pairs.')
