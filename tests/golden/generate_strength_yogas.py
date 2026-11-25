"""Reproduce synthetic numerical references using PySwissEph and the KB's Python arithmetic."""
from pathlib import Path
import json
import math
import sys
from importlib.metadata import version

import swisseph as swe
from generate_vedic import FIXTURES, benchmark, FLAGS

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'kb/governance/validation'))
from shadbala import recompute, GRAHAS
from ashtakavarga import prastara_for, reduce_row, pindas
from bhava_bala import houses, benefic
from yoga_charts import fixture_facts
from yoga_formation import participants
from itertools import combinations
from check import evaluate

def generate():
    export = json.loads((ROOT / 'kb/dist-json/admin/vedic.json').read_bytes())
    resources = export['resources']
    rules = {k: v['rule'] for k, v in export['rules'].items()}
    tables = {k.split('.')[-1]: r['calculation'] for k,r in rules.items()
              if k.startswith('vedic.strength-shadbala.') and 'calculation' in r}
    tables.update(natural=resources['vedic/planets/benefic-profile.yaml'],
                  relationships=resources['vedic/dignity/relationships.yaml'])
    signs = resources['vedic/signs/catalog.yaml']['signs']
    def read(path):
        if path in resources:
            return resources[path]
        assert path == 'vedic/strength/shadbala/drik.yaml'
        return rules['vedic.strength-shadbala.drik']
    result = []
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    for fixture in FIXTURES:
        natal = benchmark(*fixture, 'known')
        jd = natal['julianDay']
        lat,lon = fixture[-2:]
        place = (lon,lat,0)
        def event(at, flag):
            return swe.rise_trans(at,swe.SUN,flag,place,1013.25,15,swe.FLG_MOSEPH)[1][0]
        rises = [event(jd-2+i/2,swe.CALC_RISE) for i in range(5)]
        rise = max(v for v in rises if v <= jd)
        setting = event(rise,swe.CALC_SET)
        sun = swe.calc_ut(jd,swe.SUN,swe.FLG_MOSEPH)[0]
        chart = dict(instant=jd, longitude={g:v['longitude'] for g,v in natal['positions'].items()},
                     asc=natal['lagna'],mc=swe.houses_ex(jd,lat,lon,b'W',swe.FLG_SIDEREAL)[1][1],
                     latitude={},declination={},mean={},sunrise_sunset_next=[rise,setting,event(setting,swe.CALC_RISE)],
                     solar_hour=24*((jd+.5+lon/360+swe.time_equ(jd))%1),epoch_weekday=6,
                     completed_days=math.floor(rise+.5+lon/360)-2451545,
                     solar_altitude_deg=swe.azalt(jd,swe.ECL2HOR,place,1013.25,15,sun[:3])[1],
                     sun_above_apparent_horizon=jd<setting)
        for g in GRAHAS:
            code=getattr(swe,g.upper())
            chart['latitude'][g]=swe.calc_ut(jd,code,FLAGS)[0][1]
            chart['declination'][g]=swe.calc_ut(jd,code,swe.FLG_MOSEPH|swe.FLG_EQUATORIAL)[0][1]
            if g!='moon':
                obj=swe.EARTH if g=='sun' else code
                chart['mean'][g]=(swe.get_orbital_elements(jd+swe.deltat(jd),obj,swe.FLG_MOSEPH)[9]
                                  -natal['ayanamsa']+(180 if g=='sun' else 0))%360
        rows=recompute(chart,tables,rules,signs)
        totals={g:v['totals'] for g,v in rows.items()}
        natal_sign={g:int(v//30) for g,v in chart['longitude'].items()}
        natal_sign['lagna']=int(chart['asc']//30)
        offsets=resources['vedic/strength/ashtakavarga/bindu.yaml']['offsets']
        weights=resources['vedic/strength/ashtakavarga/reductions.yaml']
        sign_ids=[s['id'] for s in signs]
        pairs=[[sign_ids.index(s.lower()) for s in pair.split('/')] for pair in weights['same_owner_pairs']]
        sav=[0]*12
        pinda={}
        for g in GRAHAS:
            marks=prastara_for(offsets[g],natal_sign)
            raw=list(map(sum,zip(*marks.values())))
            sav=[a+b for a,b in zip(sav,raw)]
            _, reduced=reduce_row(raw,[[i,i+4,i+8] for i in range(4)],pairs,{natal_sign[p] for p in GRAHAS})
            pinda[g]=pindas(reduced,natal_sign,weights['rashi_weights']['alternative'],weights['graha_weights_sun_through_saturn'])
        coords={g:chart['longitude'][g] for g in GRAHAS}
        coords['lagna']=chart['asc']
        aspects=resources['vedic/aspects/full-graha.yaml']['inclusive_distances']
        planet_rows={g:rules['vedic.planets.'+g]['graha'] for g in GRAHAS}
        yoga_tables=(signs,planet_rows,aspects,tables['totals']['minimum_rupas'])
        # Evaluate each potentially contributing lord pair and each debility witness.
        bound=[fixture_facts(dict(longitude=coords,house_pair=pair,selected_graha=g,
                                  jupiter_shadbala_rupas=rows['jupiter']['rupas']),yoga_tables)
               for pair in combinations(range(1,13),2) for g in GRAHAS]
        benefics={g for g in GRAHAS if benefic(g,chart['longitude'],tables['natural'])}
        formation_chart=dict(signs=natal_sign,lagna=natal_sign['lagna'],benefics=benefics,full_aspects=aspects,
                             exaltation={g:sign_ids.index(next(iter(planet_rows[g]['dignity']['exaltation_peak_degrees'])))
                                         for g in GRAHAS}, day_birth=jd<setting,d9={g:int(v*9//30)%12 for g,v in coords.items()})
        formed={}
        for rid in resources['vedic/yogas/activation.yaml']['members']:
            row=rules[rid]
            slug=rid.split('.')[-1]
            if 'formation' in row:
                if slug in ('bheri','shankha','kahala'):
                    continue  # Require the separate practitioner strength grade.
                match=participants(slug,row['formation'],formation_chart)
                formed[rid]=None if match is None else bool(match)
            else:
                formed[rid]=any(evaluate(row['conditions'],f) for f in bound)
        result.append(dict(name=fixture[0],birthInstantUtc=natal['utc'].replace('+00:00','Z'),timeZone=natal['timeZone'],
                           latitude=lat,longitude=lon,sav=sav,pinda=pinda,formed=formed,
                           shadbala={g:{k:r[k] for k in ('sthana','dig','kala','cheshta','naisargika','drik','ishta','kashta')} for g,r in rows.items()},
                           houses={method:[h['total'] for h in houses(chart,totals,read,method)] for method in ('whole-sign-middle','sripati')}))
    return dict(source='pyswisseph '+version('pyswisseph')+'; Moshier; KB Python reference arithmetic',published_raman='unverified',fixtures=result)

if __name__=='__main__':
    Path(__file__).with_name('strength_yogas.json').write_text(json.dumps(generate(),indent=2)+'\n')
