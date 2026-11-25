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

## Panchang

The server-side Vedic engine exposes `computePanchang` for a UTC instant, an IANA zone and a geographic observer. Sunrise and sunset belong to the observer’s civil date. Vara is Sunday-zero and changes at sunrise. Before sunrise it uses the preceding local sunrise. When the required sunrise is unavailable, vara is null. A polar no-event leaves the corresponding event null; lunar limbs remain available. Calendar boundaries follow the zone’s actual offset transitions.

The Swiss adapter calls `swe_rise_trans` with Moshier, 1013.25 hPa, 15 °C and the supplied elevation (default zero metres). The default uses the apparent upper limb. The traditional option changes sunrise only to the disc centre without refraction (769). Both retain the calculated UTC instant.

Tithi and karana divide lunar elongation, nakshatra divides the Moon’s longitude, and yoga divides the sum of the solar and lunar longitudes. Each uses apparent geocentric Lahiri positions. Bracketing and bisecting the actual unwrapped angle gives inclusive starts and exclusive ends. Widths, names, paksha and stellar lords come from the admin Vedic export. Tithi number is one-based and index0 is zero-based.

### Local day, lunar month and observances

Moonrise and moonset report the first apparent-upper-limb event inside the query location’s civil date. Either may be null independently. The location, IANA zone, elevation and solar sunrise method travel with the result. Unknown birth time has no bearing on a Panchang query.

`sunriseTithis` compares the current civil date’s sunrise with the next local sunrise. Equal labels mark an adhika tithi. A forward jump over one or more labels marks kshaya and records the skipped labels, including across new moon. Either missing sunrise leaves the comparison null.

`windows` describes the day beginning at the requested civil date’s sunrise, even for a query before dawn. Every slot includes its start and excludes its end. The sunrise weekday selects the daytime eighth for Rahu Kaal, Yamaganda and Gulika. Abhijit is the eighth of fifteen daylight slots. Brahma is the fourteenth of fifteen slots from the previous sunset to sunrise. Hora divides daylight and the following night into twelve slots each, continuing the planetary sequence at sunset. Choghadiya uses eight slots on each side of sunset and a separate starting label and cycle for each. Missing or unordered solar anchors leave the complete window set null. Durations use elapsed UTC time across daylight-saving transitions.

`masa` describes the lunation containing the query instant. New moon opens the interval and the following new moon closes it. One sidereal solar sign ingress names an ordinary month. Zero ingresses mark adhika and use the next ingress name. Two ingresses mark kshaya and retain both names for review, with a null display name. The convention records `calendarProfile`, defaulting to `amanta`. Under `purnimanta` the dark fortnight takes the next bright fortnight’s name. The lunation boundaries, ingress evidence and intercalary status still describe the underlying new-moon interval.

| Festival | Local dating rule |
|---|---|
| Ugadi | First Chaitra, including adhika. Use the earlier sunrise in Pratipada if two qualify, or the immediately preceding sunrise if Pratipada falls between them. |
| Deepavali (Lakshmi Puja) | Ordinary Ashvina Amavasya (Kartika Krishna under purnimanta). The tithi must overlap the first fifth of the night for a positive duration. Two qualifying evenings select the later date. |
| Sankranti | Assign the ingress instant to the sunrise-to-sunrise interval containing it. |
| Ekadashi, Purnima, Amavasya | Match the exported tithi numbers at sunrise. |
| Pradosh | Intersect either fortnight’s Trayodashi with the first fifth of the night. |

Festival results carry the local date and the qualifying UTC interval or ingress instant. An unresolved month or unqualified window yields no dated observance for that rule. The catalogue, timing evidence and partitions are internal engine data. The offline reference uses pyswisseph Moshier, relative-speed refinement of lunar crossings, Swiss solar crossing times and independent partition and festival calculations. Regenerate with `python tests/golden/generate_panchang_extras.py` in the development venv.

## Vimshottari

`computeVimshottari` returns the birth balance and one full nine-Maha cycle from the actual start of the birth Maha. The Moon’s arc through its 48,000-arcsecond star determines the elapsed fraction of the first lord’s years. Each parent begins with its own lord, then follows the exported sequence. Children receive their lord’s years divided by 120 of the full parent span. Antar and Pratyantar are included; request Sookshma explicitly. A display can clip these half-open intervals after calculation.

The convention identifies one UTC clock for every level: Julian 365.25 days by default, Savana 360 or mean Gregorian 365.2425. Each day is 86,400 elapsed seconds. Known or exact time uses the two-minute confidence assessment. The coarse approximate input uses fifteen minutes; callers can specify ±5 min, ±15 min or ±1 h directly. Unknown time uses local noon as the working instant and assesses the entire civil date. If the Moon crosses a nakshatra boundary in the interval, the balance and timeline are null. The angular, timing and convention records are internal facts.

The offline reference generator is `tests/golden/generate_panchang_dasha.py`. It computes Moshier reference events, angular intervals and the four active birth periods with PySwissEph. The golden suite compares UTC instants directly, including pre-sunrise and polar dates, both sides of a repeated civil hour and the traditional sunrise variant.

## Natal strength and formations

`createVedicEngine(port).computeStrength(input)` uses the same resolved birth instant, Lahiri chart, node selection and varga methods as the positions engine. Its `admin` result holds the worksheet and selected conventions. The `public` result projects only the English, Kannada and Hindi labels and corresponding tone from the KB strength wording table. A missing grade or incomplete house ranking withholds its label.

**Shadbala.** The seven classical grahas receive Sthana, Dig, Kala, Cheshta, Naisargika and Drik in virupas. One rupa equals sixty virupas. Positional strength uses the D1, D2, D3, D7, D9, D12 and D30 tables. Directed natural friendship combines with the temporary relationship in D1. Venus uses Libra from zero to fifteen degrees for moolatrikona; the five-degree alternative is selectable. The exaltation peak wins the shared Moon and Mercury label endpoints. The divisional strength award independently uses the half-open moolatrikona interval.

Latitude and declination come from ecliptic and equatorial Swiss calculations. Mean longitude uses Swiss orbital elements at terrestrial time, reduced to Lahiri; the mean Sun uses the opposing mean Earth. Angular diameter comes from Swiss planetary phenomena in arcminutes. Dig uses the actual meridian and horizon axes. Kala uses local apparent solar time and seasonal daylight or night divisions measured between apparent rise and set events. The arithmetic savana epoch is the local sunrise day of January 1, 2000 (Saturday); abda and masa count 360- and 30-day blocks from that epoch. The Sun’s ayana and Moon’s paksha also supply their Cheshta terms. Ishta and Kashta use the unrounded uchcha and Cheshta.

**Selected methods.** Graha Drik defaults to interpolated special peaks and signed quarters. The fixed-segment alternative applies the KB bonuses and counts Mercury and Jupiter in full. War requires an eligible pair strictly less than one degree apart. The northern body wins. The modern comparison transfers the absolute pre-war Kala difference; the classical comparison includes Sthana and Dig and divides by the absolute diameter difference. Unresolved latitude ties, multiple overlapping contestants or unavailable required diameters withhold the affected totals. Moon nature defaults to Shukla and Mercury to predominance; the convention can select Raman Ashtami, bright-72 or strict Mercury association.

**Bhava Bala and Ashtakavarga.** The default bhava midpoint is the centre of its whole sign. Sripati trisects the Asc–IC–Desc–MC quadrants, assigns each house its midpoint sign lord and measures directional strength from the opposing cardinal point in degrees divided by three. Both methods add the lord’s Shadbala, directional and aspect terms, signed occupant awards and the day, night or twilight award. The seven BAV rows each use eight contributors, including Lagna. Their raw SAV adds to 337. Shodhana operates on a separate copy, subtracting the elemental-trine minima before co-owned sign reductions. Rashi and Graha Pinda use that reduced copy. The PVR Moon contributor table is available as a separate edition. Unknown birth time withholds the Lagna-dependent calculations.

**Yogas and doshas.** Each of the activation catalogue’s 82 formations binds the grahas that actually form it. For each witness the engine evaluates cancellation and softening, checks the participants’ strength grades, then checks their participation in the selected Maha or Antar. The default period instant is birth; callers can supply `periodInstantUtc`. Mahabhagya requires an explicitly chosen branch. Optional mutual full aspects and the close Mercury combustion orb have explicit variant names. The natal Manglik default uses the inclusive six-house list from Lagna. The Raman, Rath, SGS and regional alternatives bind their own lists, origins and exceptions. Natal nodal-axis and same-sign node contacts are technical evidence.

All calculation tables come from the admin Vedic JSON export. The fixture generator uses PySwissEph Moshier and the independent Python KB worksheet arithmetic. The convention records `published_raman: unverified`; the published comparison is pending a verifiable worksheet.

## Yogini and Chara dashas

The internal engine methods `computeYogini` and `computeChara` return a timeline with one convention record for the whole tree. The record identifies the seed, variant and fixed number of elapsed UTC days per year. Majors and Antars use half-open intervals. An end instant belongs to the next period. Both methods read their calculation tables from the admin Vedic export. [Method catalogue](../kb/dist-json/admin/vedic.json)

**Yogini.** The convention uses the exported balance-rule ID `vedic.dashas-yogini.balance-calculation`. Add three to the one-based birth Moon nakshatra and take the remainder modulo eight, with zero selecting Sankata. The elapsed fraction of the 48,000-arcsecond mansion determines how much of the opening major preceded birth. The tree starts at that major’s full start and spans one 36-year cycle. Each major’s eight Antars start with its own Yogini and receive shares in proportion to their years. The default year is mean Gregorian (365.2425 days), with savana (360 days) selectable. A change of mansion across the declared precision interval withholds both the balance and the timeline. Unknown time uses local noon as the working instant and tests the whole civil date.

**Chara.** The K.N. Rao candidate variant is `pyjhora-kn-rao-candidate-v1`. The natal Lagna seeds the first major at birth. A ninth sign in Cancer through Virgo or Capricorn through Pisces makes the major sequence run backward. For each duration, the period sign’s own foot group determines the direction to its lord. Count steps, treating zero as twelve, then add one for exaltation or subtract one for debilitation of a classical planet. Nodes carry zero dignity adjustment. Cap each first-pass duration at twelve. Repeat the sign order using its complement to twelve and omit zero spans. The complete tree spans 144 fixed years. Julian (365.25 days) is the default, with mean Gregorian and savana available.

Scorpio compares Mars and Ketu. Aquarius compares Saturn and Rahu. If exactly one candidate occupies the owned sign, use the other. If both occupy it, use the classical lord. Otherwise compare companion count, support by occupation or sign aspect from Jupiter, Mercury and the classical dispositor (one count per role), exaltation, modality (dual, fixed, movable), then uncapped candidate duration. An unresolved tie withholds the timeline. A missing or unstable Lagna also withholds it. The Moon-chart tier (unknown or ±1 hour) supplies no Lagna seed.

Each Chara major has twelve equal Antars ending on the parent sign. The exported forward-sign list selects the direction, beginning one step from the parent. These candidate subdivisions carry `verification: unverified` and `visibility: admin-only`. The golden harness checks the implementation against independently calculated Swiss/Moshier charts and interval arithmetic. Source-edition verification of the Antar method remains pending. [Reference generator](../tests/golden/generate_yogini_chara.py) · [Golden tests](../tests/golden/yogini_chara.test.ts)
