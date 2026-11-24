"""Rebuild synthetic chart references with pyswisseph and locally installed Swiss files."""
import hashlib
import os
import sys
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

import swisseph as swe
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'governance/validation'))
from functional import SIGNS
from vimshottari import active_path, instant, stamp, divide

PEOPLE = [
    ('Asha','1992-03-12','05:40','Bengaluru',12.97,77.59),
    ('Ravi','1985-08-03','14:10','Mysuru',12.30,76.64),
    ('Meera','2001-12-21','22:30','Delhi',28.61,77.21),
    ('Kabir','1978-06-09','07:15','Mumbai',19.08,72.88),
    ('Dev','1995-01-05','12:00','Chennai',13.08,80.27),
]
CODES = dict(sun=swe.SUN,moon=swe.MOON,mars=swe.MARS,mercury=swe.MERCURY,
             jupiter=swe.JUPITER,venus=swe.VENUS,saturn=swe.SATURN,rahu=swe.MEAN_NODE)
FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
ZONE = ZoneInfo('Asia/Kolkata')
AT = datetime(2026,11,24,12,tzinfo=ZONE)

@lru_cache(None)
def read(path):
    return yaml.safe_load((ROOT / path).read_text())

def jd(dt):
    return dt.timestamp()/86400 + 2440587.5

def chart(dt):
    bodies = {}
    for g,code in CODES.items():
        values,flags = swe.calc_ut(jd(dt),code,FLAGS)
        if flags & FLAGS != FLAGS:
            raise ValueError(f'Swiss file calculation unavailable for {g}')
        bodies[g] = (values[0],values[3])
    longitude,speed = bodies['rahu']
    bodies['ketu'] = ((longitude+180)%360,speed)
    return bodies

def labels(x):
    sign = int(x//30)
    star = read('vedic/nakshatras/catalog.yaml')['nakshatras'][int(x*27/360)]
    return dict(sign=SIGNS[sign],degree=x%30,nakshatra=star['id'],pada=int(x*108/360)%4+1,
                d9=SIGNS[int(x*9/30)%12],d10=SIGNS[(sign+8*(sign%2)+int((x%30)//3))%12])

def record(person,provenance):
    name,date,time,city,lat,lon = person
    birth = datetime.fromisoformat(date+'T'+time).replace(tzinfo=ZONE)
    tier = 'C' if name=='Dev' else 'A'
    half = timedelta(hours=12) if tier=='C' else timedelta(minutes=2)
    # Sample the full interval including both edges. These are reference values at the
    # working instant; named readings consume only the stable categorical fields.
    samples = [chart(birth+half*(i/30-1)) for i in range(61)]
    bodies = chart(birth)
    grahas = {}
    for g,(x,speed) in bodies.items():
        row = labels(x)
        orb = read('vedic/states/combustion.yaml')['state']['orbs']['retrograde' if speed<0 else 'direct'].get(g)
        row.update(longitude=x,speed=speed,retrograde=speed<0,
                   combust=orb is not None and abs((x-bodies['sun'][0]+180)%360-180)<=orb)
        row['unstable']=[k for k in ('sign','nakshatra','pada','d9','d10')
                         if any(labels(sample[g][0])[k]!=row[k] for sample in samples)]
        code = CODES['rahu'] if g=='ketu' else CODES[g]
        row['latitude'] = swe.calc_ut(jd(birth),code,FLAGS)[0][1] * (-1 if g=='ketu' else 1)
        grahas[g]=row
    lagna=None
    if tier=='A':
        asc=lambda dt:swe.houses_ex(jd(dt),lat,lon,b'W',swe.FLG_SIDEREAL)[1][0]
        lagna=dict(longitude=asc(birth),**labels(asc(birth)))
        lagna['unstable']=[k for k in ('sign','nakshatra','pada','d9','d10')
                           if any(labels(asc(birth+half*i))[k]!=lagna[k] for i in (-1,1))]
    # PRD requires the additional five-minute varga stability test even at exact precision.
    if lagna:
        for key in ('d9','d10'):
            if any(labels(asc(birth+timedelta(minutes=i)))[key]!=lagna[key] for i in (-5,5)) and key not in lagna['unstable']:
                lagna['unstable'].append(key)
    query=AT.isoformat()
    periods={}
    if 'nakshatra' not in grahas['moon']['unstable']:
        for title,when in [('birth',birth.isoformat()),('reading',query)]:
            path=active_path(read('vedic/dashas/vimshottari/periods.yaml'),birth.isoformat(),
                             Fraction(str(bodies['moon'][0]))*3600,'julian-365.25',instant(when))
            periods[title]={k:dict(lord=g,start=stamp(a),end=stamp(b)) for k,(g,a,b) in path.items() if k in ('maha','antar','pratyantar')}
    def rise(local_day):
        start = local_day.replace(hour=0,minute=0)
        result,times=swe.rise_trans(jd(start),swe.SUN,swe.CALC_RISE,(lon,lat,0),1013.25,15,swe.FLG_SWIEPH)
        if result!=0:return None
        return datetime.fromtimestamp((times[0]-2440587.5)*86400,tz=ZONE)
    sunrise=rise(birth)
    prev_rise=rise(birth-timedelta(days=1))
    next_rise=rise(birth+timedelta(days=1))
    def birth_limbs(sample,at):
        sun,moon=(sample[g][0] for g in ('sun','moon'))
        delta=(moon-sun)%360
        last=max(t for t in (prev_rise,sunrise,next_rise) if t and t<=at)
        return dict(vara=last.strftime('%A'),tithi=int(delta//12)+1,nakshatra=labels(moon)['nakshatra'],
                    yoga=int((moon+sun)%360*27/360)+1,karana_half=int(delta//6))
    all_limbs=[birth_limbs(sample,birth+half*(i/30-1)) for i,sample in enumerate(samples)]
    stable_limbs={k:v if all(sample[k]==v for sample in all_limbs) else None for k,v in all_limbs[30].items()}
    pair_examples = {}
    if periods:
        maha = periods['reading']['maha']
        signs = {g:int(x//30) for g,(x,speed) in bodies.items()}
        for antar,a,b in divide(read('vedic/dashas/vimshottari/periods.yaml'),maha['lord'],instant(maha['start']),instant(maha['end'])):
            distance = (signs[antar]-signs[maha['lord']])%12+1
            group = ('six-eight' if distance in (6,8) else 'two-twelve' if distance in (2,12) else
                     'angle-trine' if distance in (1,4,5,7,9,10) else 'other')
            if group not in pair_examples:
                pair_examples[group]=dict(maha=maha['lord'],antar=antar,distance=distance,start=stamp(a),end=stamp(b))
    saturn=int(chart(AT)['saturn'][0]//30)
    distance=(saturn-int(bodies['moon'][0]//30))%12+1
    return dict(synthetic=True,approval='draft',fixture=name,local=birth.isoformat(),city=city,
                latitude=lat,longitude=lon,utc=birth.astimezone(timezone.utc).isoformat(),julian_day=jd(birth),
                stable_birth_panchanga=stable_limbs,sunrise_local=sunrise.isoformat(),precision='unknown' if tier=='C' else 'exact',tier=tier,rectified=False,reading_at=query,
                provenance=provenance,lagna=lagna,grahas=grahas,working_instant_periods=periods,
                pair_relationship_examples=pair_examples,sade_sati={12:'entering',1:'middle',2:'leaving'}.get(distance,'outside'))

def main():
    folder=Path(os.environ['SWEPH_PATH'])
    files={f:hashlib.sha256((folder/f).read_bytes()).hexdigest() for f in ('sepl_18.se1','semo_18.se1')}
    swe.set_ephe_path(str(folder))
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    provenance=dict(binding=version('pyswisseph'),swiss_version=swe.version,files_sha256=files,
                    package='@kuntay/swisseph-data@0.2.2',flags=FLAGS,actual_backend='SEFLG_SWIEPH',
                    sidereal_mode=1,node='mean',houses='whole-sign',dasha_year_days=365.25,
                    command='Set SWEPH_PATH to the extracted ephe directory; run python kb/examples/fixtures/generate.py then python kb/examples/fixtures/workflow.py')
    for person in PEOPLE:
        r=record(person,provenance)
        (Path(__file__).parent/(person[0].lower()+'.yaml')).write_text(yaml.safe_dump(r,sort_keys=False))
        if person[0]=='Asha':
            path=ROOT/'examples/asha-convention-record.yaml'
            convention=yaml.safe_load(path.read_text())
            convention.update(engine_version='pyswisseph-'+provenance['binding'],birth_local=r['local'][:19],
                              birth_place=r['city'],actual_backend=provenance['actual_backend'],
                              julian_day=r['julian_day'],birth_utc=r['utc'],reference_chart='examples/fixtures/asha.yaml')
            path.write_text(yaml.safe_dump(convention,sort_keys=False))
if __name__=='__main__':
    main()
