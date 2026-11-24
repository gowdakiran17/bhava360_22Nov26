"""KB-48 reference resolver. A trace certifies all transitions, not periodic samples."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

GRADES = ('Weak', 'Moderate', 'Strong')


@dataclass(frozen=True)
class Interval:
    start: datetime
    end: datetime
    include_end: bool = True


def assessment_interval(instant, precision, tiers, civil, varga=False):
    """Finite times arrive resolved under KB-32. An unknown time supplies a zoned date."""
    if instant is None or instant.tzinfo is None or precision not in tiers['declared_precision']:
        return None
    if precision == 'unknown':
        zone = instant.tzinfo
        day = instant.date()
        start = datetime.combine(day, time.min, zone).astimezone(timezone.utc)
        end = datetime.combine(day + timedelta(days=1), time.min, zone).astimezone(timezone.utc)
        return Interval(start, end, False)
    settings = tiers['declared_precision'][precision]
    radius = settings.get('assessment_radius_seconds', civil['precision'][precision]['radius_seconds'])
    if varga:
        radius = max(radius, tiers['interval']['varga_minimum_radius_seconds'])
    utc = instant.astimezone(timezone.utc)
    delta = timedelta(seconds=radius)
    return Interval(utc-delta, utc+delta)


@dataclass(frozen=True)
class Trace:
    """Value at start plus every transition through end, certified by the fact producer."""
    start: datetime
    end: datetime
    initial: object
    changes: tuple = ()
    complete: bool = True

    def values(self, interval):
        if interval is None or not self.complete or self.start > interval.start or self.end < interval.end:
            return []
        before = self.initial
        result = []
        last = self.start
        for at, value in self.changes:
            if not last < at <= self.end:
                raise ValueError('Transitions must be ordered within the certified interval')
            last = at
            if at <= interval.start:
                before = value
            elif at < interval.end or at == interval.end and interval.include_end:
                result.append(value)
        return [before, *result]


def stable(trace, interval, transform=lambda value: value):
    values = trace.values(interval) if trace else []
    if not values or any(v is None for v in values):
        return None
    projected = [transform(v) for v in values]
    first = projected[0]
    return first if all(v == first for v in projected) else None


def date_bounds(value, month):
    """Calendar dates in the reporting zone, already resolved by the period producer."""
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    try:
        start, end = (date.fromisoformat(s) for s in value)
    except (TypeError, ValueError):
        return None
    if start > end:
        return None
    return tuple(d.isoformat()[:7] if month else d.isoformat() for d in (start, end))


def resolve(precision, instant, traces, bound_varga, tiers, civil, matrix):
    """Evaluate one bound reading. Each dependency uses the same chart and query.

    Independent query-day inputs can be supplied even when birth evidence is unavailable.
    Values and withheld IDs in this reference worksheet belong to staff/testers.
    """
    if precision not in tiers['declared_precision']:
        raise ValueError('Unrecognized birth-time precision')
    settings = tiers['declared_precision'][precision]
    tier = settings['tier']
    assessments = {}
    def assess(key):
        if key in assessments:
            return assessments[key]
        row = matrix['rows'][key]
        action = row[tier]
        window = assessment_interval(instant, precision, tiers, civil, row.get('varga', False))
        deps = list(row['requires'])
        result = {}
        if row.get('birth_independent'):
            # Query-day facts are certified on the query window, independently of a birth instant.
            query = traces.get('query-day-and-place')
            window = Interval(query.start, query.end) if query else None
        if 'reference_by_tier' in row:
            ref = row['reference_by_tier'][tier]
            if ref == 'lagna' and assess('lagna')['action'] == 'hide':
                ref = row['withheld_lagna_reference']
            deps += [ref+'-sign', ref+'-house-term']
            result['reference'] = ref
        if row.get('inherits_bound_varga'):
            varga_row = matrix['rows'].get(bound_varga, {})
            if not varga_row.get('varga') or assess(bound_varga)['action'] == 'hide':
                action = 'hide'
            deps += ['varga-promise-condition']
            window = assessment_interval(instant, precision, tiers, civil, True)
        if any(stable(traces.get(dep), window) is None for dep in deps):
            action = 'hide'
        if 'dates' in row and action != 'hide':
            month = action == 'month-resolution'
            dep = row.get('month_dates', row['dates']) if month else row['dates']
            bounds = stable(traces.get(dep), window, lambda v: date_bounds(v, month))
            if bounds is None:
                action = 'hide'
            else:
                result['bounds'] = bounds
        if key == 'final-card-grade' and action != 'hide':
            grade = stable(traces.get('post-ladder-grade'), window)
            if grade not in GRADES:
                action = 'hide'
            else:
                result['grade'] = 'Moderate' if action == 'cap-moderate' and grade == 'Strong' else grade
        result = {'action':'hide'} if action == 'hide' else dict(action=action, **result)
        assessments[key] = result
        return result
    for key in matrix['rows']:
        assess(key)
    return {'tier':tier, 'rectified':False, 'message':settings['message'], 'outputs':assessments,
            'withheld':sorted(key for key, value in assessments.items() if value['action']=='hide')}


def validate(read, require):
    from zoneinfo import ZoneInfo

    tiers = read('shared/confidence/birth-time-tiers.yaml')
    matrix = read(tiers['output_matrix'])
    rows = matrix['rows']
    civil = read(tiers['precision_source'])
    copy = read(tiers['copy_source'])
    examples = read('examples/birth-time-confidence.yaml')
    mapping = tiers['declared_precision']
    require(set(mapping)==set(civil['precision']) and
            {k:v['tier'] for k,v in mapping.items()}==
            {'exact':'A','±5 min':'B','±15 min':'B','±1 h':'C','unknown':'C'},'declared tier mapping')
    require(tiers['rectification']['record_default'] is False and copy['approval']=='draft' and
            copy['native_review']=={'hi':'pending','kn':'pending'},'MVP confidence metadata')
    require(all(set(copy['messages'][v['message']])=={'en','kn','hi'} for v in mapping.values()),
            'required confidence explanations')
    for key,row in rows.items():
        require(all(row[t] in matrix['actions'] for t in 'ABC'), key+' invalid matrix cell')
    vargas = [key for key,v in rows.items() if v.get('varga') and v.get('scope')=='Lagna/houses']
    require(set(vargas)=={'d'+str(n) for n in (2,3,4,7,9,10,12,16,20,24,27,30,40,45,60)},'divisional coverage')
    require(all(rows[k]['B']=='hide' and rows[k]['C']=='hide' for k in
                ('d24','d60','kp-cuspal-sub-lords','kp-house-significators','kp-cuspal-prashna',
                 'pratyantar-windows','sookshma-windows','peak-month','peak-day')), 'hard tier limits')

    dev = examples['dev']
    center = datetime.fromisoformat(dev['local']).replace(tzinfo=ZoneInfo(dev['zone']))
    utc = center.astimezone(timezone.utc)
    before, after = utc-timedelta(days=1), utc+timedelta(days=1)
    def trace(value, *changes):
        return Trace(before, after, value, tuple((utc+timedelta(seconds=sec),v) for sec,v in changes))
    def run(precision, traces, varga='d10'):
        return resolve(precision,center,traces,varga,tiers,civil,matrix)
    def check_example(record, example):
        require(record['rectified'] is example['rectified'] is False,'stored MVP flag')
        expected = dict.fromkeys(rows, example['expected_default'])
        for action, keys in example['expected_changes'].items():
            for key in keys:
                require(key in rows,key)
                expected[key]=action
        require({k:v['action'] for k,v in record['outputs'].items()}==expected,'full example matrix '+record['message'])
        require(sorted(k for k,v in expected.items() if v=='hide')==record['withheld'],'withheld IDs')

    # B1 is a fully specified series of test classifications, not an inferred chart.
    b1 = examples['b1']
    traces = {dep:trace('stable') for row in rows.values() for dep in row['requires']}
    for dep in ('lagna-house-term','moon-house-term','varga-promise-condition'):
        traces[dep]=trace('stable')
    traces['post-ladder-grade']=trace('Strong')
    for row in rows.values():
        if 'dates' in row:
            traces[row['dates']] = trace(b1['antar_bounds_before'])
    traces['antar-bounds'] = trace(b1['antar_bounds_before'], (60,b1['antar_bounds_after']))
    traces['d10-lagna']=trace('aries',(b1['d10_crossing_seconds_after_working_instant'],'taurus'))
    b=run(b1['precision'],traces,b1['bound_varga'])
    check_example(b,b1)
    require(b['outputs']['event-window']['bounds']==('2026-11','2027-02')
            and b['outputs']['final-card-grade']['grade']=='Moderate','Antar months and final clamp')
    require(run('±15 min',traces,'d24')['outputs']['promise-varga-lagna']['action']=='hide','tier-hidden bound varga')
    crossed=dict(traces, **{'antar-bounds':trace(b1['antar_bounds_before'],(60,['2026-12-01','2027-02-16']))})
    require('event-window' in run('±15 min',crossed)['withheld'],'month disagreement')
    for grade in GRADES:
        data=dict(traces, **{'post-ladder-grade':trace(grade)})
        for precision in ('exact','±15 min','±1 h','unknown'):
            r=run(precision,data)
            want='Moderate' if precision!='exact' and grade=='Strong' else grade
            require(r['outputs']['final-card-grade']['grade']==want,'after-ladder ceiling')

    normal=assessment_interval(center,'exact',tiers,civil)
    require((normal.end-normal.start).total_seconds()==240 and run('exact',traces)['outputs']['lagna']['action']=='show',
            'exact mid-sign and two-minute assessment')
    require('d10' in run('exact',traces)['withheld'],'varga crossing outside two but inside five minutes')
    # Scenario geometry: local linear motion with a half-degree left to the boundary.
    start_deg, boundary_deg = 29.5, 30
    crossing_seconds = lambda rate: round((boundary_deg-start_deg)/rate)
    require(crossing_seconds(0.5/299)==299,'half-degree edge fixture')
    for offset, action in ((299,'hide'),(300,'hide'),(301,'show')):
        near=dict(traces,**{'lagna-sign':trace('aries',(crossing_seconds(.5/offset),'taurus'))})
        require(run('±5 min',near)['outputs']['lagna-transits']['action']==action,'Lagna crossing boundary')
    edge = run('±5 min',dict(traces, **{'lagna-sign':trace('aries',(100,'taurus'))}))
    require(edge['outputs']['strength-house-term']['reference']=='moon' and 'lagna' in edge['withheld'],
            'Moon substitute is a separately proved house term')
    missing_birth = resolve('unknown',None,traces,'d10',tiers,civil,matrix)
    require([k for k,v in missing_birth['outputs'].items() if v['action']!='hide']==['daily-panchang'],
            'unresolved birth inputs do not suppress a proved independent query day')
    for t in (Trace(before,after,'aries',complete=False),Trace(utc,after,'aries'),
              trace('aries',(-40,'taurus'),(40,'aries')),trace(None)):
        require(stable(t,normal) is None,'partial proof, unknown or interior transition')
    require('lagna' in run('±1 h',traces)['withheld'] and
            run('±1 h',traces)['message']!=run('unknown',traces)['message'],'Moon-only approximate time')
    whole=assessment_interval(center,'unknown',tiers,civil)
    dev_traces={dep:Trace(whole.start,whole.end,v) for dep,v in dev['stable'].items()}
    lunar = dev['moon_provenance']['longitude_start_noon_end_deg']
    # The prograde arc stays within one sign and traverses exactly one nakshatra boundary.
    require(lunar == sorted(lunar) and [int(x//30) for x in lunar] == [10,10,10] and
            [1+int(x/(360/27)) for x in lunar] == [23,24,24], 'Dev Lahiri lunar arc')
    star_edge=whole.start+timedelta(seconds=dev['moon_provenance']['nakshatra_crossing_bracket_seconds'][1])
    star=Trace(whole.start,whole.end,23,((star_edge,24),))
    dev_traces.update({'moon-nakshatra':star,'bound-planet-star':star})
    result=run('unknown',dev_traces)
    check_example(result,dev)
    require(result['outputs']['strength-house-term']['reference']=='moon' and b['outputs']['strength-house-term']['reference']=='lagna','house term origin')
    # Isolate the nakshatra gate from missing period data and test the independent planet-only KP path.
    for precision in ('unknown','±1 h','exact'):
        data=dict(traces, **{'moon-nakshatra':trace(23,(0,24))})
        require(all(key in run(precision,data)['withheld'] for key in ('maha-name','antar-name','maha-dates','antar-dates')),'dasha boundary')
    c=run('unknown',traces)
    require(all(c['outputs'][key]['action']=='show' for key in ('maha-name','antar-name','kp-planet-star-lord','kp-planet-sub-lord'))
            and c['outputs']['kp-cuspal-prashna']['action']=='hide','stable dasha and independent KP planet results')
    require('antar-name' in run('unknown',dict(traces,**{'antar-lord':trace('venus',(0,'sun'))}))['withheld'],
            'stable starting star alone cannot establish active period')
    sub=run('unknown',dict(traces,**{'bound-planet-sub':trace('sun',(1,'moon'))}))['outputs']
    require(sub['kp-planet-star-lord']['action']=='show' and sub['kp-planet-sub-lord']['action']=='hide','independent KP sub lord')
    require(stable(Trace(whole.start,whole.end,'same',((whole.end,'next date'),)),whole)=='same','next midnight excluded')
    for d,hours in [('2024-03-10',23),('2024-11-03',25)]:
        dt=datetime.fromisoformat(d+'T12:00').replace(tzinfo=ZoneInfo('America/New_York'))
        w=assessment_interval(dt,'unknown',tiers,civil)
        require((w.end-w.start).total_seconds()==hours*3600,'entire civil date across offset changes')
    print(f'Birth-time confidence passed: {len(rows)} outputs, three tiers, five precisions, Dev and Scenario B1.')
