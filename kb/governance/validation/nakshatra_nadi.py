"""Offline, review-only comparison with the 60 supplied synthetic Nadi cases."""
from collections import Counter
from bisect import bisect_right
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import re

import swisseph as swe
from kp import RULERS
from public_copy import check_text
from vimshottari import active_path, instant

SIGNS = 'Aries Taurus Gemini Cancer Leo Virgo Libra Scorpio Sagittarius Capricorn Aquarius Pisces'.split()
PLANETS = dict(Sun=swe.SUN, Moon=swe.MOON, Mars=swe.MARS, Mercury=swe.MERCURY,
               Jupiter=swe.JUPITER, Venus=swe.VENUS, Saturn=swe.SATURN)
ASPECTS = {'Mars': (4, 7, 8), 'Jupiter': (5, 7, 9), 'Saturn': (3, 7, 10)}
LEVELS = ('maha', 'antar', 'pratyantar')


def positions(jd):
    swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
    bodies = dict(PLANETS, Rahu=swe.TRUE_NODE)
    pos = {g: swe.calc_ut(jd, n, swe.FLG_MOSEPH | swe.FLG_SIDEREAL)[0][0] for g, n in bodies.items()}
    pos['Ketu'] = (pos['Rahu'] + 180) % 360
    return pos


def stable_sub_identity(lon, fields, tolerance):
    lower = fields((lon - tolerance) % 360)
    upper = fields((lon + tolerance) % 360)
    return lower[2:] == upper[2:]


def stable_lagna_sign(fixture, radius_seconds):
    """Require the same rising sign at the instant and both precision limits."""
    jd = fixture['julian_day']
    radius = radius_seconds / 86400
    try:
        signs = {int(swe.houses_ex(at, fixture['latitude'], fixture['longitude'],
                                   b'W', swe.FLG_SIDEREAL)[1][0] // 30)
                 for at in (jd - radius, jd, jd + radius)}
    except swe.Error:
        return None
    return signs.pop() if len(signs) == 1 else None


def chart(fixture, kp_rows, stars, periods, tolerance, radius_seconds):
    pos = positions(fixture['julian_day'])
    starts = [row['start_arcsec'] for row in kp_rows]

    def fields(lon):
        row = kp_rows[bisect_right(starts, lon * 3600) - 1]
        return (SIGNS[row['sign'] - 1], stars[row['nakshatra'] - 1]['id'].replace('-', ' ').title(),
                row['star_lord'].title(), row['sub_lord'].title())

    details = {g: fields(lon) for g, lon in pos.items()}
    result = dict(pos=pos, details=details, periods={}, lines={}, combination={}, power={}, houses_ready=None)
    if fixture['precision'] == 'unknown':
        # Local noon is the centre of this particular synthetic civil date.
        samples = [positions(fixture['julian_day'] - .5 + minute / 1440) for minute in range(1441)]
        result['stable'] = {g: [set(col) for col in zip(*(fields(s[g]) for s in samples))] for g in pos}
        return result
    if fixture['precision'] != 'exact':
        return result
    for clock in ('julian-365.25', 'savana'):
        path = active_path(periods, fixture['utc'], pos['Moon']*3600, clock, instant(fixture['reading_at']))
        result['periods'][clock] = {level: path[level][0].title() for level in LEVELS}
        if clock == 'julian-365.25':
            for level in LEVELS:
                _, start, end = path[level]
                result[level+'_span_ist'] = [datetime.fromtimestamp(float(t), ZoneInfo('Asia/Kolkata')).date().isoformat()
                                              for t in (start, end)]
    lagna = stable_lagna_sign(fixture, radius_seconds)
    if lagna is None:
        return result
    result['houses_ready'] = True
    signs = [(lagna + offset) % 12 for offset in range(12)]
    occupied_by = {g: (int(lon // 30) - lagna) % 12 + 1 for g, lon in pos.items()}
    owned = {g: [h for h, sign in enumerate(signs, 1) if RULERS[sign].title() == g] for g in PLANETS}
    combo = {g: sorted({occupied_by[g], *owned[g]}) for g in PLANETS}
    basis = {}
    for node in ('Rahu', 'Ketu'):
        sign = int(pos[node] // 30)
        lord = RULERS[sign].title()
        distances = {g: (sign - int(pos[g] // 30)) % 12 + 1 for g in PLANETS}
        joined = [g for g, d in distances.items() if d == 1]
        aspect = [g for g, d in distances.items() if d in ASPECTS.get(g, (7,))]
        basis[node] = dict(dispositor=lord, conjoined=joined, aspected_by=aspect)
        combo[node] = sorted({occupied_by[node]}.union(*(combo[g] for g in [lord, *joined, *aspect])))
    result.update(house_signs=[SIGNS[s] for s in signs], occupied=occupied_by, owned=owned,
                  combination=combo, node_basis=basis)
    for name, lon in pos.items():
        # Compare identities, since a KP interval can also split at a sign edge.
        if stable_sub_identity(lon, fields, tolerance):
            nl, sl = details[name][2:]
            result['power'][name] = power_facts([name, nl, sl], occupied_by, combo)
    for level, name in result['periods']['julian-365.25'].items():
        nl, sl = details[name][2:]
        result['lines'][level] = dict(lord=name, PL=combo[name], NL=combo[nl], SL=combo[sl])
    return result


def power_facts(actors, occupied_by, combinations):
    circles = dict(zip(('pl', 'nl', 'sl'), (occupied_by[g] for g in actors), strict=True))
    nl, sl = circles['nl'], circles['sl']
    counts = Counter(h for g in actors for h in set(combinations[g]))
    return dict(circle=circles['pl'], line_circles=circles, power_position=sorted({nl, sl}),
                full_power=nl == sl, hit_pair=dict(row_sl=sl, col_nl=nl), hit_count=dict(counts))


def select_ladder(entries, facts):
    """Test editorial candidates without storing private ladders or grid cells."""
    if not facts:
        return None
    power = set(facts['power_position'])
    circles = set(facts['line_circles'].values())
    eligible = []
    for order, (rank, kind, houses) in enumerate(entries):
        witnesses = set(houses)
        gate = power if kind == 'challenging' else circles
        if witnesses <= facts['hit_count'].keys() and witnesses & gate:
            eligible.append((rank, -len(witnesses & power), order))
    return min(eligible)[2] if eligible else None


def description(fields):
    sign, star, nl, sl = fields
    return f'{sign}, {star}, NL {nl}, SL {sl}'


def review_outlook(chart_data, area):
    if not chart_data['lines']:
        return {'result': 'withheld', 'copy_key': 'withheld'}
    lines = chart_data['lines']['antar']
    houses = set(lines['PL'] + lines['NL'] + lines['SL'])
    plus, minus = [sorted(houses.intersection(area[key])) for key in ('supportive', 'challenging')]
    label = ('mixed' if minus else 'supportive') if plus else ('challenging' if minus else 'quiet')
    return dict(houses_in_lines=sorted(houses), supportive_hits=plus, challenging_hits=minus, label=label, copy_key=label)


def allowed_bodies(names):
    return set(names).intersection([*PLANETS, 'Rahu', 'Ketu']), bool(set(names).intersection(['Uranus','Neptune','Pluto']))


def validate_nadi(rules, read, require):
    module = read('nadi/nakshatra-nadi/module.yaml')
    cases = read('examples/nakshatra-nadi.yaml')
    registered = set(module['rule_index'].values())
    require(len(registered)==22 and registered=={key for key,r in rules.items() if r['system']=='nadi'}, 'Nadi rule index')
    questions = set(module['open_questions'])
    blocked = module['blocked_by']
    require(questions == {'hit-grid-data', 'node-dignity'} and len(module['resolved_questions']) == 4
            and len(module['traditions_differ']) == 9, 'Nadi method decisions')
    require(blocked == {module['rule_index']['NN-M14']: ['hit-grid-data'],
                        module['rule_index']['NN-M20']: ['node-dignity']}
            and all(set(reasons) <= questions for reasons in blocked.values()), 'Nadi blocker references')
    registry = read('shared/conventions/profiles.yaml')['calculation_profiles']
    profile = registry['nakshatra-nadi']
    require((profile['enabled'], profile['approval'], profile['houses'], profile['node'], profile['sidereal_mode'])
            == (False, 'draft', 'whole-sign', 'true-node', 5) and 'review_variant' not in profile,
            'Held whole-sign Nadi frame')
    tolerance = registry['vedic-lahiri-v1']['tolerances_inclusive']['longitude_deg']
    require(module['internal_line_weights'] == {'sl': 0.5, 'nl': 0.3, 'pl': 0.2}, 'Owner line weights')
    for rid in registered:
        r=rules[rid]
        require((r['status']=='blocked')==(rid in module['blocked_by']) and r['native_review_needed'] is True
                and r['approval']=='draft' and r['visibility']=='admin-only' and r['feature_gate']=='nakshatra-nadi', rid)
    for localized in [*module['preview_copy'].values(),module['practice_label'],*[p['user_text'] for p in module['practices']]]:
        require(set(localized)=={'en','kn','hi'}, 'Nadi locales')
        for lang, text in localized.items():
            check_text(text,'held review preview',lang)
    radius_seconds = read('shared/confidence/birth-time-tiers.yaml')['declared_precision']['exact']['assessment_radius_seconds']
    kp_rows=read('kp/number-horary/249-divisions.yaml')['intervals']
    starts = [row['start_arcsec'] for row in kp_rows]
    def boundary_fields(lon):
        row = kp_rows[bisect_right(starts, lon * 3600) - 1]
        return row['sign'], row['nakshatra'], row['star_lord'], row['sub_lord']

    boundary = starts[1] / 3600
    require(not stable_sub_identity(boundary, boundary_fields, tolerance)
            and stable_sub_identity(boundary + 2 * tolerance, boundary_fields, tolerance),
            'Sub-lord boundary withholds the dependent circle; stable side retains it')
    stars=read('vedic/nakshatras/catalog.yaml')['nakshatras']
    periods=read('vedic/dashas/vimshottari/periods.yaml')
    require([c['id'] for c in cases['cases']]==[f'NN-T{i:02}' for i in range(1,61)], 'Nadi fixture inventory')
    try:
        charts={}
        for name in ('Asha','Ravi','Meera','Kabir','Dev'):
            f=read('examples/fixtures/'+name.lower()+'.yaml')
            charts[name] = chart(f, kp_rows, stars, periods, tolerance, radius_seconds)
        probe = power_facts(['A','B','B'], {'A':1,'B':4}, {'A':[1,2],'B':[2,4]})
        require(probe['hit_count']=={1:1,2:3,4:2} and probe['full_power'], 'Repeated lines and houses')
        require(select_ladder([(1,'supportive',[2]), (2,'challenging',[1])], probe) is None,
                'Uncircled supportive and non-power challenging witnesses')
        candidates = [(1,'supportive',[1]),(1,'supportive',[4]),(1,'challenging',[4])]
        require(select_ladder(candidates,probe)==1 and select_ladder(candidates,None) is None,
                'Power witness breaks a rank tie, then source order')
        polar = dict(read('examples/fixtures/asha.yaml'), latitude=89)
        polar_chart = chart(polar, kp_rows, stars, periods, tolerance, radius_seconds)
        require(polar_chart['houses_ready'] and polar_chart['power'], 'Whole-sign houses available at high latitude')
        with patch.object(swe, 'houses_ex', side_effect=swe.Error('Lagna unavailable')):
            failed = chart(polar, kp_rows, stars, periods, tolerance, radius_seconds)
        require(failed['houses_ready'] is None and not any(failed[k] for k in ('power','combination','lines'))
                and failed['periods'] == polar_chart['periods'], 'Lagna failure preserves both period clocks')
        with patch.object(swe, 'houses_ex', side_effect=[((), (359.99,)), ((), (0.0,)), ((), (0.01,))]):
            require(stable_lagna_sign(polar, radius_seconds) is None, 'Sign boundary inside exact-time interval')
        unstable = dict(polar,latitude=12.97,precision='approximate')
        require(not chart(unstable,kp_rows,stars,periods,tolerance,radius_seconds)['power'], 'Unstable time withholds circles')
        for i, case in enumerate(cases['cases'],1):
            data=charts.get(case['fixture'],charts['Asha'])
            e=case['expected']
            def same(actual, expected):
                require(actual==expected, f"{case['id']} {case['case']}: {actual!r} != {expected!r}")
            path=data['periods'].get('julian-365.25',{})
            if 'Sun' in e:
                for g, line in e.items():
                    match=re.search(r" (\d+)°(\d+)'",line)
                    minutes=int(match[1])*60+int(match[2])
                    require(abs(data['pos'][g]%30*60-minutes)<=1,case['id']+' '+g+' longitude')
                    same(description(data['details'][g]),line.replace(match[0],''))
            elif 'house_signs' in e or 'combination' in e:
                for key, value in e.items(): same(data[key],value)
            elif 'level' in e:
                name = path[e['level']]
                same(name, e['lord'])
                facts = data['power'][name]
                for key in ('line_circles', 'power_position', 'full_power', 'hit_pair'):
                    same(facts[key], e[key])
                lines = data['lines'][e['level']]
                for line, circle in facts['line_circles'].items():
                    require(circle in lines[line.upper()], 'circle belongs to its line')
            elif 'variant_360' in e and 'maha' in e:
                same(path,{lvl:e[lvl] for lvl in LEVELS})
                same(data['periods']['savana'],e['variant_360'])
                for lvl in ('antar','pratyantar'): same(data[lvl+'_span_ist'],e[lvl+'_span_ist'])
            elif 'maha' in e:
                same(data['lines'],e)
            elif 'houses_in_lines' in e or i in (51,52):
                preview=review_outlook(data,cases['area_sets'][case['case'].split(':')[0]])
                same(preview,{k:v for k,v in e.items() if k!='must_not_contain'})
                require(preview['copy_key'] in module['preview_copy'],case['id'])
            elif i==53:
                same(data['power'], {})
                for key in ('line_circles', 'power_position', 'hit_pair'):
                    same(data['power'].get('Moon', {}).get(key), e[key])
            elif i==48:
                stable=data['stable']
                same({g:description([next(iter(s)) for s in cols]) for g,cols in stable.items()
                      if all(len(s)==1 for s in cols)},e['shown'])
                same(stable['Moon'][:3],[{'Aquarius'},{'Dhanishta','Shatabhisha'},{'Mars','Rahu'}])
                same(stable['Mercury'],[{'Capricorn'},{'Uttara Ashadha'},{'Sun'},{'Jupiter','Saturn'}])
            elif i==49:
                same((data['combination'],data['lines']),({},{}))
            elif i==50:
                require(len(data['stable']['Moon'][2])>1 and not path,case['id'])
            elif i in (54,55,56):
                if i==54:
                    same(len(module['practices']),3)
                    require(all(p['label']==e['render_contains'] and p['optional'] and p['free'] for p in module['practices']),case['id'])
                    texts=[p['user_text']['en'] for p in module['practices']]
                elif i==55:
                    require('health' in module['held_topics'],case['id'])
                    texts=[module['preview_copy']['wellbeing']['en']]
                else:
                    key=review_outlook(data,cases['area_sets']['relationship_timing'])['copy_key']
                    texts=[module['preview_copy'][key]['en']]
                require(all(term not in text.lower() for text in texts for term in e['must_not_contain']),case['id'])
            elif i==57:
                same(path['antar']=='Venus',e['natural_deliverer']['property_vehicle'])
            elif i==58:
                same(description(data['details']['Mercury']),e['kp'])
                distance = data['pos']['Mercury'] % 30
                same(min(distance, 30 - distance) * 60 <= 5, e['within_five_arcminutes'])
            elif i==59:
                same([path['pratyantar'],data['periods']['savana']['pratyantar']],[e['default'],e['variant_360']])
            elif i==60:
                same(allowed_bodies([*PLANETS,'Uranus','Neptune','Pluto']),(set(PLANETS),True))
            else:
                raise ValueError('Unexercised scenario '+case['id'])
    finally:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    print('Nakshatra Nadi: 22 held rules and 60 synthetic cases passed.')
