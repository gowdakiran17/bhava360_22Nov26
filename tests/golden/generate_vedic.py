"""Regenerate vedic.json with the development venv. Uses only built-in Moshier."""
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import swisseph as swe

FIXTURES = [
    ("Asha", "1992-03-12", "05:40", "Bengaluru", 12.97, 77.59),
    ("Ravi", "1985-08-03", "14:10", "Mysuru", 12.30, 76.64),
    ("Meera", "2001-12-21", "22:30", "Delhi", 28.61, 77.21),
    ("Kabir", "1978-06-09", "07:15", "Mumbai", 19.08, 72.88),
    ("Dev", "1995-01-05", "12:00", "Chennai", 13.08, 80.27),
]
BODIES = {"sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY,
          "venus": swe.VENUS, "mars": swe.MARS, "jupiter": swe.JUPITER,
          "saturn": swe.SATURN, "rahu": swe.MEAN_NODE}
FLAGS = swe.FLG_MOSEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED


def benchmark(name, date, time, city, lat, lon, precision):
    zone = "Asia/Kolkata"
    utc = datetime.fromisoformat(f"{date}T{time}").replace(tzinfo=ZoneInfo(zone)).astimezone(timezone.utc)
    jd = swe.julday(utc.year, utc.month, utc.day, utc.hour + utc.minute / 60, swe.GREG_CAL)
    ayan_flag, ayan = swe.get_ayanamsa_ex_ut(jd, swe.FLG_MOSEPH)
    assert ayan_flag & swe.FLG_MOSEPH
    positions = {}
    for body, code in BODIES.items():
        values, flags = swe.calc_ut(jd, code, FLAGS)
        assert flags & FLAGS == FLAGS
        positions[body] = {"longitude": values[0], "speed": values[3]}
    node = positions["rahu"]
    positions["ketu"] = {"longitude": (node["longitude"] + 180) % 360, "speed": node["speed"]}
    lagna = None if precision == "unknown" else swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)[1][0]
    return dict(name=name, date=date, time=time, city=city, latitude=lat, longitude=lon,
                timeZone=zone, precision=precision, utc=utc.isoformat(), julianDay=jd,
                ayanamsa=ayan, lagna=lagna, positions=positions)


if __name__ == "__main__":
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    rows = [benchmark(*fixture, "known") for fixture in FIXTURES]
    rows.append(benchmark(*FIXTURES[-1], "unknown"))
    result = {"provenance": {"binding": "pyswisseph " + version("pyswisseph"),
              "library": swe.version, "flag": "SEFLG_MOSEPH", "mode": 1,
              "node": "mean", "calendar": "Gregorian", "source": "generate_vedic.py"}, "fixtures": rows}
    Path(__file__).with_name("vedic.json").write_text(json.dumps(result, indent=2) + "\n")
