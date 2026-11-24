"""Full graha aspects and distinct same-sign pairs on the whole-sign D1 chart."""
from itertools import combinations


def reaches(source, target, distances):
    if source is None or target is None:
        return None
    return 1+(target-source)%12 in distances


def validate_aspects(rules, read, evaluate, require):
    table=read('vedic/aspects/full-graha.yaml')['inclusive_distances']
    for graha, offsets in table.items():
        for h in range(1,13):
            row=rules[f'vedic.aspects.{graha}-aspects-house-{h}']
            key=f'd1.aspect.{graha}.house_{h}'
            for source in [None,*range(12)]:
                v=reaches(source,h-1,offsets)
                require(evaluate(row['conditions'],{key:v}) is v, row['id'])
            require(row['exceptions'][0]['when']['fact']=='d1.aspect.source_impaired',row['id'])
    for body in ('mars','jupiter','saturn'):
        for target in ('moon','venus','seventh-lord','tenth-lord'):
            require(f'vedic.aspects.{body}-aspects-{target}' in rules,target)
    for a,b in combinations(table,2):
        row=rules[f'vedic.conjunctions.{a}-{b}']
        key=f'd1.conjunction.{a}_{b}'
        if row.get('retired'):
            require((a,b)==('rahu','ketu') and row['visibility']=='admin-only', 'retired node-axis guard')
            continue
        for x,y,want in [(29.99,29.999,True),(29.99,30,False),(0,180,False),(None,0,None)]:
            actual=None if x is None else int(x//30)==int(y//30)
            require(evaluate(row['conditions'],{key:actual}) is want,key)
    require(reaches(2,6,table['jupiter']) and not reaches(2,6,table['rahu']),'H7 full fifth aspect')

    h7=read('examples/transits-vargas-elections.yaml')['H7']
    signs=read('vedic/signs/catalog.yaml')['signs']
    order=[row['id'] for row in signs]
    origin=order.index(h7['lagna'].lower())
    occupied={body:order.index(value.split()[0].lower()) for body,value in h7['placements'].items()}
    partner=(origin+6)%12
    require(occupied['mars']==partner and reaches(occupied['jupiter'],partner,table['jupiter'])
            and 1+(occupied[signs[partner]['lord']]-origin)%12==11,'H7 lord, occupant and aspect')
    chart=next(row for row in read('vedic/vargas/methods.yaml')['methods'] if row['chart']=='D9')
    require(chart['sign_lookup']['virgo'][4]=='taurus','H7 Venus at fifteen degrees in Virgo')
