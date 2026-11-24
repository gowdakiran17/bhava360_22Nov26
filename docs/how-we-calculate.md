# Vedic core positions

The calculation entry point is the typed EngineModule returned by `createVedicEngine(port)`. Create the port once with `await createSwissEphemeris()` from the Node-only adapter. Constructing the module reads the committed admin Vedic JSON export. Each subsequent `computeFacts(input)` uses only its arguments, the injected ephemeris and the catalogue. Supply the resolved birthInstantUtc, latitude (north positive), longitude (east positive), IANA timeZone and timePrecision. The time-dependent inputs are explicit; a natal result does not depend on the current clock or a database.

**Working instant.** At intake, core's resolveBirth resolves the local date and time using the place's IANA history. An ambiguous time requires a choice. Known and approximate times use the stored UTC instant. For unknown time we use noon on that local calendar date, keep the unknown precision, omit the ascendant calculation and return null for Lagna and every house. Known noon retains the ascendant. Coordinates at the geographic poles are rejected because Lagna is undefined there.

**Time scale and frame.** Use the proleptic Gregorian calendar. Julian day UT is 2440587.5 plus UTC epoch seconds divided by 86400. This slice treats UTC as UT1 and makes no external Earth-orientation lookup. Swiss handles its internal time-scale conversion in swe_calc_ut. Longitudes are apparent geocentric ecliptic degrees of date, normalized to [0, 360). Swiss sidereal mode 1 and SEFLG_SIDEREAL perform the conversion to Lahiri. The accompanying apparent ayanamsa uses swe_get_ayanamsa_ex_ut with the same ephemeris (including nutation). Applying the ayanamsa a second time would shift the chart twice.

**Grahas and Lagna.** Request SEFLG_SPEED and read longitude and degrees/day from components 0 and 3 of each Swiss result. Negative sidereal speed means retrograde. The mean ascending lunar node is Rahu by default. Request nodeType=true as the string `'true'` to use the oscillating true node. Ketu is the opposite longitude with the same speed. The ascendant comes directly from element 0 of the Swiss houses_ex ascendant/MC array, using sidereal mode and whole-sign house code W.

**Divisions.** Sign 1 is Aries. House 1 is the entire rising sign. Count signs forward modulo twelve to obtain each house. The zodiac has 108 half-open quarters of 3°20′, starting at 0° sidereal Aries. Every four quarters form one nakshatra. An exact boundary belongs to the segment that begins there. For each segment, the Vedic JSON catalogue supplies its slug, number and Vimshottari lord. Its dotted rule ID resolves the title and confirms the number and lord. [Export](../kb/dist-json/admin/vedic.json)

**Provenance.** Results include the working instant, Julian day UT, ayanamsa and the convention record. The adapter requests built-in Moshier and checks the returned calculation flags before accepting each result. The factory keeps one isolated WASM instance. Development requires only workspace dependencies from npm. SWEPH_PATH remains reserved for local file-backed operation in a later release. No ephemeris data files, network requests, Python subprocess or public projection are needed at runtime. See the [independent golden harness](../tests/golden/README.md) and [licence decision](adr/13-sweph.md).

## Divisional signs

The internal `vargas` record maps each D-number to its placements and convention. The engine reads the twelve sign lookup rows, cell boundaries, method ID and release access from the exported `vedic/vargas/methods.yaml` resource in `kb/dist-json/admin/vedic.json`. Signs are numbered Aries 1 through Pisces 12. The engine uses the unrounded Lahiri longitude. At an exact lower edge the new cell owns the point, including Aries at the zodiac wrap.

| Chart | How the lookup assigns signs |
|---|---|
| D1 | Natal sign |
| D2 | Leo then Cancer for odd-numbered signs, reversed for even signs |
| D3, D4 | From the natal sign, advance four signs per third or three signs per quarter |
| D7, D10 | Start at the natal sign for odd signs. For even signs start at its seventh (D7) or ninth (D10) |
| D9 | Start at the natal sign, its ninth or its fifth for movable, fixed or dual signs respectively |
| D12 | Start at the natal sign |
| D16, D45 | Start at Aries, Leo or Sagittarius for movable, fixed or dual signs |
| D20 | Start at Aries, Sagittarius or Leo for movable, fixed or dual signs |
| D24 | Start at Leo for odd signs or Cancer for even signs |
| D27 | Start at Aries, Cancer, Libra or Capricorn for fire, earth, air or water signs |
| D30 | Odd signs start new bands at 0°, 5°, 10°, 18° and 25°, mapping to Aries, Aquarius, Sagittarius, Gemini and Libra. Even signs start at 0°, 5°, 12°, 20° and 25°, mapping to Taurus, Virgo, Pisces, Capricorn and Scorpio |
| D40 | Start at Aries for odd signs and Libra for even signs |
| D60 | Candidate only. Start at the natal sign and advance one sign for each half degree |

Each chart records its method ID, Lahiri frame, whole-sign house system, actual ephemeris flag and time precision. D1, D9 and D10 have MVP access. Twelve charts have R2 access. The KB currently labels the D60 method stability-gated. This engine release explicitly holds it as a candidate and always suppresses its interpretation and houses.

The engine recalculates positions over five minutes on either side of the working instant, including both endpoints and the centre. It samples every thirty seconds, checks the intervening zodiac cells and refines graha speed reversals to a millisecond interval. A changed divisional sign keeps its central `sign` for inspection, sets `unstable` and clears `interpretationSign`. A whole-sign house requires both an eligible body sign and an eligible divisional Lagna. For unknown time, noon supplies working graha signs, all interpretation fields and houses are null, and the divisional Lagna is null. The five-minute check measures local sensitivity only. These records are internal engine facts.

The independent generator uses fresh pyswisseph Moshier positions and separately coded seed arithmetic. It samples every five seconds for stability and records the Swiss versions and exported method IDs. Run the generator from the development venv and run the golden tests to print a row for every available chart and body. [Reference generator](../tests/golden/generate_vargas.py) · [Golden tests](../tests/golden/vargas.test.ts)
