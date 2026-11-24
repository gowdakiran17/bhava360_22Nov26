"""Fresh Swiss positions and an independent arithmetic interpretation of the exported methods."""
import json
from importlib.metadata import version
from pathlib import Path

import swisseph as swe
from generate_vedic import BODIES, FIXTURES, FLAGS, benchmark

HERE = Path(__file__).resolve().parent
RESOURCE = 'vedic/vargas/methods.yaml'


def sign(lon, n):
    natal, degree = divmod(lon % 360, 30)
    s = int(natal)
    i = int(degree * n / 30)
    even = s % 2  # even-numbered sign
    if n == 2:
        return ((4, 3), (3, 4))[even][i] + 1
    if n == 30:
        limits, targets = (([5, 10, 18, 25], [1, 11, 9, 3, 7]),
                           ([5, 12, 20, 25], [2, 6, 12, 10, 8]))[even]
        return targets[sum(degree >= edge for edge in limits)]
    if n in (3, 4):
        return (s + (12 // n) * i) % 12 + 1
    seed = {1: s, 7: s + 6 * even, 9: s + (0, 8, 4)[s % 3], 10: s + 8 * even,
            12: s, 16: (0, 4, 8)[s % 3], 20: (0, 8, 4)[s % 3], 24: (4, 3)[even],
            27: (s % 4) * 3, 40: even * 6, 45: (s % 3) * 4, 60: s}[n]
    return (seed + i) % 12 + 1


def sample(jd, fixture):
    points = {}
    for name, code in BODIES.items():
        values, flags = swe.calc_ut(jd, code, FLAGS)
        assert flags & FLAGS == FLAGS
        points[name] = values[0]
    points['ketu'] = (points['rahu'] + 180) % 360
    if fixture['precision'] != 'unknown':
        points['lagna'] = swe.houses_ex(jd, fixture['latitude'], fixture['longitude'], b'W', swe.FLG_SIDEREAL)[1][0]
    return points


def generate():
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    kb = json.loads((HERE.parents[1] / 'kb/dist-json/admin/vedic.json').read_text())
    methods = kb['resources'][RESOURCE]['methods']
    rows = []
    for fixture, precision in [*((f, 'known') for f in FIXTURES), (FIXTURES[-1], 'unknown')]:
        f = benchmark(*fixture, precision)
        window = [sample(f['julianDay'] + sec / 86400, f) for sec in range(-300, 301, 5)]
        center = window[len(window) // 2]
        charts = {}
        for method in methods:
            chart = method['chart']
            n = int(chart[1:])
            signs = {p: sign(lon, n) for p, lon in center.items()}
            unstable = [p for p in signs if any(sign(obs[p], n) != signs[p] for obs in window)]
            charts[chart] = dict(signs=signs, unstable=unstable)
        rows.append(dict(name=f['name'], precision=precision, charts=charts))
    return dict(provenance=dict(binding=version('pyswisseph'), library=swe.version, flag='SEFLG_MOSEPH',
                                siderealMode=1, node='mean', methodResource=RESOURCE,
                                methodIds={m['chart']: m['id'] for m in methods}, source='generate_vargas.py'),
                fixtures=rows)


if __name__ == '__main__':
    HERE.joinpath('vargas.json').write_text(json.dumps(generate(), indent=2) + '\n')
