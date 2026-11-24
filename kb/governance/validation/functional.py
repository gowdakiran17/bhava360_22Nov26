"""Reconcile the functional table with the twelve whole-sign ownership rows."""
SIGNS = 'aries taurus gemini cancer leo virgo libra scorpio sagittarius capricorn aquarius pisces'.split()
GRAHAS = 'sun moon mars mercury jupiter venus saturn rahu ketu'.split()
OWNERS = 'mars venus mercury moon sun mercury venus mars jupiter saturn saturn jupiter'.split()
MT_DISPUTES = {
    ('virgo','saturn'): 'Sixth ownership can receive more weight than fifth ownership.',
    ('leo','jupiter'): 'The fifth can receive more weight than the eighth.',
    ('gemini','saturn'): 'The ninth can receive more weight than the eighth.',
    ('aquarius','mercury'): 'The eighth can receive more weight than the fifth.',
    ('sagittarius','mars'): 'Prioritising the fifth reinforces the default despite twelfth ownership.',
}


def cell(lagna, graha, dignity):
    houses = {(i-SIGNS.index(lagna)) % 12 + 1 for i, owner in enumerate(OWNERS) if owner == graha}
    yoga = bool(houses & {4,7,10} and houses & {5,9})
    exempt = 8 in houses and graha in ('sun','moon')
    kendra = bool(houses & {4,7,10}) and houses <= {2,4,7,10,12}
    benefic = graha in ('jupiter','venus','mercury','moon')
    data = dict(houses_ruled=sorted(houses), yogakaraka=yoga,
                kendradhipati=kendra and benefic,
                strong=kendra and graha in ('jupiter','venus') and lagna in SIGNS[2::3],
                eighth_lord_exempt=exempt, eleventh_least_malefic_for_wealth=11 in houses,
                maraka=bool(houses & {2,7}), mt_tiebreak=len(houses)==2)
    if not houses:
        return dict(data, polarity=None, rule='dispositor')
    if 1 in houses:
        nature = 'Benefic'
    elif yoga:
        nature = 'Yogakaraka'
    elif exempt:
        nature = 'Neutral'
    elif houses & {5,9}:
        nature = 'Neutral' if 8 in houses else 'Benefic'
    elif houses & {3,6,8,11}:
        nature = 'Malefic'
    else:
        nature = 'Neutral'
    data['polarity'] = nature
    if len(houses)==2:
        data['mt_house'] = (SIGNS.index(dignity[graha]['moolatrikona_sign'])-SIGNS.index(lagna))%12+1
    if (lagna,graha) in MT_DISPUTES:
        data['traditions_differ'] = MT_DISPUTES[lagna,graha]
    return data


def resolve(table, lagna, graha, node_sign=None):
    if lagna not in table or graha not in table[lagna]:
        return None
    row = table[lagna][graha]
    if row.get('rule') == 'dispositor':
        if node_sign not in SIGNS:
            return None
        nature = table[lagna][OWNERS[SIGNS.index(node_sign)]]['polarity']
        return 'Benefic' if nature == 'Yogakaraka' else nature
    return row['polarity']


def validate(read, require):
    table = read('vedic/lordships/functional.yaml')['cells']
    dignity = read('vedic/dignity/sign-dignities.yaml')['grahas']
    # Independent expected rows from the reviewed first-match worksheet.
    expected = ('BNBMBNM NMNBMBY MNMBNBN NBYMBMM BNYMNMM NMMBNBB '
                'MNNBMBY NBBMBNM BNBNBMM NNMBMYB NMMNMYB MBBNBMM').split()
    require(list(table)==SIGNS,'functional Lagna rows')
    for lagna, letters in zip(SIGNS, expected, strict=True):
        row = table[lagna]
        require(list(row)==GRAHAS and ''.join(row[g]['polarity'][0] for g in GRAHAS[:7])==letters,lagna)
        for g in GRAHAS:
            require(row[g]==cell(lagna,g,dignity), f'{lagna}/{g} flags and MT ownership')
            owned=read(f'vedic/planets/{g}.yaml')['graha']['nature']['functional_nature'][lagna]
            require(all(row[g][k]==v for k,v in owned.items()), f'{lagna}/{g} ownership mismatch')
    require(table['gemini']['jupiter']['strong'] and table['virgo']['jupiter']['strong']
            and table['pisces']['mercury']['kendradhipati'] and not table['pisces']['mercury']['strong']
            and table['libra']['mars']['maraka'] and table['capricorn']['sun']['eighth_lord_exempt']
            and table['sagittarius']['moon']['eighth_lord_exempt'] and table['aries']['saturn']['eleventh_least_malefic_for_wealth'],
            'reviewed functional flag spots')
    require(sum(c['yogakaraka'] for r in table.values() for c in r.values())==6,'six Yogakarakas')
    require(resolve(table,'cancer','rahu','aries')=='Benefic' and resolve(table,'aries','ketu') is None
            and resolve(table,None,'sun') is None,'dispositor and unknowns')
    print('Functional nature: 108 cells, six Yogakarakas, five disputed MT cells passed.')
