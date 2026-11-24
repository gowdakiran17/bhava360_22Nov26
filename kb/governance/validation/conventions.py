"""Reference checks for KB-32 calculation metadata. No production inputs."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
import re

BACKENDS = {'SEFLG_SWIEPH', 'SEFLG_MOSEPH'}
TABLE_PROFILES = {'western/aspects/orbs.yaml', 'checks/house-relocation/profile.yaml',
                  'vastu/profile.yaml'}


def profile_refs(doc, registry, root, path):
    """Visit nested calculation.profile and traditions_differ records as well as rule headers."""
    if isinstance(doc, list):
        for i, item in enumerate(doc):
            profile_refs(item, registry, root, f'{path}[{i}]')
    elif isinstance(doc, dict):
        for key, value in doc.items():
            field = f'{path}.{key}'
            if key in ('profile', 'doctrine_profile', 'calculation_profile', 'calculation.profile'):
                if not isinstance(value, str) or not (
                    value in registry or (value in TABLE_PROFILES and (root / value).is_file())
                ):
                    raise ValueError(f'{field}: unresolved profile {value!r}')
            else:
                profile_refs(value, registry, root, field)


def backend_ok(policy, record):
    actual = record.get('actual_backend')
    return (policy.get('ephemeris_flag') == record.get('ephemeris_flag') == 'runtime-backend'
            and set(policy['allowed_backends']) == set(record['allowed_backends']) == BACKENDS
            and actual in BACKENDS and set(record['position_flags']) ==
            {actual, 'SEFLG_SIDEREAL', 'SEFLG_SPEED'})


def civil_candidates(local, zone):
    """Round trip to remove gap candidates and deduplicate ordinary instants."""
    tz = ZoneInfo(zone)
    candidates = {local.replace(tzinfo=tz, fold=i).astimezone(timezone.utc) for i in (0, 1)}
    return sorted(u for u in candidates if u.astimezone(tz).replace(tzinfo=None) == local)


def display_minute(seconds, unit):
    if seconds is None:
        return None
    floor, remainder = divmod(seconds, unit)
    return floor + int(remainder * 2 > unit)


def stable_fact(precision, key, fact, values_at_all_segments):
    settings = precision[key]
    if fact in settings.get('withhold', []) or not values_at_all_segments:
        return None
    first = values_at_all_segments[0]
    return first if all(value == first for value in values_at_all_segments) else None


def moonrise_on(date, zone, events):
    matches = [instant for instant in events if instant.astimezone(zone).date() == date]
    return min(matches, default=None)


def validate_conventions(read, require, root):
    profiles = read('shared/conventions/profiles.yaml')
    frame = profiles['calculation_profiles']['vedic-lahiri-v1']
    rise = read(frame['rise_set_parameters'])
    time = read(frame['time_policy'])
    example = read('examples/asha-convention-record.yaml')
    require(frame['frame'] == example['position_frame'] == 'apparent-geocentric'
            and frame['sidereal_mode_name'] == example['ayanamsa_mode'] == 'SE_SIDM_LAHIRI'
            and frame['sidereal_mode'] == example['ayanamsa_mode_number'] == 1
            and frame['ayanamsa_definition'] == example['ayanamsa_definition'] == 'true ayanamsa, Swiss default'
            and frame['lagna'] == dict(routine='swe_houses_ex', flag='SEFLG_SIDEREAL', house_code='W', result='ascmc[0]')
            and frame['houses'] == example['house_system'] == 'whole-sign', 'Lahiri frame')
    require(frame['node'] == dict(default='mean', alternative='true-node', mixing='forbidden',
                                  owner_confirmation='confirmed-by-PRD-v1.2')
            and example['node'] == 'mean' and frame['ketu'] == '(rahu_longitude_deg + 180) modulo 360',
            'node convention')
    require(example['actual_backend'] == 'SEFLG_MOSEPH', 'Asha development backend')
    for policy in (rise, frame):
        require(backend_ok(policy, example), 'Asha provenance')
        for flag in BACKENDS:
            record = dict(example, actual_backend=flag, position_flags=[flag, 'SEFLG_SIDEREAL', 'SEFLG_SPEED'])
            require(backend_ok(policy, record), 'valid effective backend')
        for flag in (None, 'runtime-backend', 'SEFLG_SWIEPH'):
            require(not backend_ok(policy, dict(example, actual_backend=flag)), 'unknown or conflicting backend')
    limits = frame['tolerances_inclusive']
    require(limits == dict(longitude_deg=.002, ayanamsa_deg=.001, lagna_deg=.01, sunrise_seconds=60),
            'PRD acceptance limits')
    for value in limits.values():
        limit = Decimal(str(value))
        def accepts(delta):
            return delta is not None and abs(delta) <= limit
        require(accepts(0) and accepts(-limit) and not accepts(limit + Decimal('.000001'))
                and not accepts(None), 'inclusive tolerance')

    require(rise['routine'] == 'swe_rise_trans' and rise['observer']['frame'] == 'topocentric'
            and rise['observer']['refraction_model'] == 'swiss-default'
            and set(rise['excluded_bits']) == {'SE_BIT_DISC_CENTER', 'SE_BIT_NO_REFRACTION'}, 'rise routine')
    for name, body, code in [('sunrise','SE_SUN',1), ('sunset','SE_SUN',2), ('moonrise','SE_MOON',1)]:
        event = rise['events'][name]
        require(event['body'] == body and event['limb'] == 'upper' and event['rsmi'] == code
                and event['flags'] == [['SE_CALC_RISE'], ['SE_CALC_SET']][code-1], name)
    for key, value in [('pressure_hpa',1013.25), ('temperature_c',15), ('elevation_default_m',0)]:
        require(rise['observer'][key] == value, key)
    day = rise['day_boundary']
    require(day['start'] == 'local-sunrise-inclusive' and day['end'] == 'following-local-sunrise-exclusive'
            and day['polar_day'] == day['polar_night'] == day['missing_required_sunrise'] == 'unknown',
            'polar sunrise policy')
    moon = rise['events']['moonrise']
    require(moon['selection'] == 'first-rise-in-local-civil-date' and moon['absent_in_date'] == 'unknown',
            'moonrise date bounds')
    unit = rise['instants']['display_unit_seconds']
    require(unit == 60 and rise['instants']['display_rounding'] == 'nearest-minute-ties-earlier'
            and [display_minute(t,unit) for t in [29,30,30.001,60,None]] == [0,0,1,1,None],
            'display minute boundaries')
    require(time['zone_rules'] == 'IANA-tzdb' and set(time['record_required']) <= example.keys()
            and re.fullmatch(r'\d{4}[a-z]+', example['tzdb_version']), 'versioned time provenance')
    for wall, expected in [('2024-11-03T01:30',['05:30','06:30']), ('2024-03-10T02:30',[])]:
        candidates = civil_candidates(datetime.fromisoformat(wall), 'America/New_York')
        require([u.strftime('%H:%M') for u in candidates] == expected, 'DST gap/fold')
    for year, offset in [(1941,330), (1943,390), (1946,330)]:
        wall = datetime(year, 6, 1, 12)
        candidates = civil_candidates(wall, 'Asia/Kolkata')
        require(len(candidates) == 1 and wall - candidates[0].replace(tzinfo=None) == timedelta(minutes=offset),
                'Kolkata historical offset')
    require(time['pre_standard']['default'] == 'tzdb-lmt'
            and time['pre_standard']['explicit_alternative'] == 'user-supplied-offset', 'historical origin')
    require(read(time['confidence_policy'])['precision_source']==frame['time_policy'],
            'KB-32 civil precision and KB-48 assessment policy must point to each other')
    precision = time['precision']
    require({k:v.get('radius_seconds') for k,v in precision.items()} ==
            {'exact':0,'±5 min':300,'±15 min':900,'±1 h':3600,'unknown':None}, 'uncertainty windows')
    for key in ('±5 min','±15 min','±1 h'):
        require(precision[key]['retain'] == 'stable-throughout-interval', 'finite precision policy')
    require(precision['unknown']['working_time'] == 'local-noon' and
            {'lagna','houses-from-lagna','lagna-derived-facts','exact-birth-dependent-times'} ==
            set(precision['unknown']['withhold']), 'unknown-time withholding')
    for key in ('±5 min', '±15 min', '±1 h'):
        require(stable_fact(precision, key, 'sign', [1, 1]) == 1
                and stable_fact(precision, key, 'sign', [1, 2]) is None
                and stable_fact(precision, key, 'sign', [1, 2, 1]) is None
                and stable_fact(precision, key, 'sign', []) is None, 'uncertain sign boundaries')
    require(stable_fact(precision, 'exact', 'lagna', ['known']) == 'known'
            and stable_fact(precision, 'unknown', 'lagna', ['known']) is None, 'Dev noon modes')
    zone = ZoneInfo(example['iana_zone'])
    local = datetime.fromisoformat(example['birth_local'])
    require(civil_candidates(local, example['iana_zone']) ==
            [datetime.fromisoformat('1992-03-12T00:10:00+00:00')], 'Asha unique instant')
    midnight = local.replace(hour=0, minute=0, tzinfo=zone)
    tomorrow = midnight + timedelta(days=1)
    require(moonrise_on(local.date(), zone, [tomorrow]) is None
            and moonrise_on(local.date(), zone, [tomorrow, midnight]) == midnight
            and moonrise_on(local.date(), zone, []) is None, 'moonrise civil date')
    require(profiles['doctrine_profiles']['bhava-chalit']['method'] == 'outside-mvp'
            and not profiles['open_decisions'] and len(profiles['owner_defaults']) == 4, 'optional methods')
    defaults = profiles['owner_defaults']
    require(defaults == {'kp-polar-fallback':'withhold-cusps','jaimini-karaka-scheme':'seven',
                         'chara-dasha-variant':'pyjhora-kn-rao-candidate-v1','d60-method':'parashari-d60-v1'},
            'KB-33 owner defaults')
    kp = profiles['calculation_profiles']['kp-placidus-v1']
    def signature(p):
        return p['sidereal_mode'], p['node']['default'], p['houses']
    require(signature(frame)==(1,'mean','whole-sign') and signature(kp)==(5,'true-node','placidus'),
            'mixed Parashari or KP default frame')
    def accepts_frame(p, record, node_override=None):
        if node_override is not None and node_override != p['node'].get('alternative'):
            return False
        return record == (p['sidereal_mode'], node_override or p['node']['default'], p['houses'])
    for p in (frame,kp):
        expected = signature(p)
        require(accepts_frame(p,expected),'consistent frame')
        other = signature(kp if p is frame else frame)
        for i in range(3):
            mixed = list(expected)
            mixed[i] = other[i]
            require(not accepts_frame(p,tuple(mixed)), 'mixed frame must fail')
    require(accepts_frame(frame,(1,'true-node','whole-sign'),'true-node')
            and not accepts_frame(kp,(5,'mean','placidus'),'mean'),'explicit node alternatives')
    require(kp['polar_fallback']=='unknown' and kp['on_cusp_failure']['withhold']==
            ['cuspal-sub-lords','house-significators','kp-prashna'] and kp['on_cusp_failure']['retain']==
            ['planet-star-lords','planet-sub-lords','independent-parashari'], 'KP polar scope')
    variant = rise['sunrise_variants']['sunrise.traditional-disc-centre']
    require(variant['rsmi']==1|256|512 and variant['refraction'] is False and variant['limb']=='centre'
            and set(variant['flags'])=={'SE_CALC_RISE','SE_BIT_DISC_CENTER','SE_BIT_NO_REFRACTION'}
            and rise['default_sunrise']==frame['sunrise'], 'separate solar event settings')
    for bad in (None, '', '../SCHEMA.yaml', 'unknown-v1'):
        try:
            profile_refs({'calculation': {'profile': bad}}, set(), root, 'negative fixture')
        except ValueError:
            continue
        raise ValueError('Invalid profile passed resolution')
    print('KB-32 conventions passed: Swiss frame, 2 backends, 4 tolerances, rise/set, civil time and profile references.')
