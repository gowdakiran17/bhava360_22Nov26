# Bhava360 knowledge base edition 1

This is a reviewable authoring edition. It contains 574 individually addressable YAML rules across ten systems, plus calculation tables and product recipes. All 574 rules have English, Kannada and Hindi user text and retain draft status.

## Where to start

| Reading or tool | Records to inspect |
|---|---|
| Natal chart, placements and strengths | [D1 guide](vedic/D1.md), [108 graha/house readings](vedic/houses/), [16 divisional sign mappings](vedic/vargas/methods.yaml), [six-component strength record](vedic/strength/shadbala/components.yaml), [Ashtakavarga contributions](vedic/strength/ashtakavarga/bindu.yaml) |
| Chapters, dates and matching | [Vimshottari](vedic/dashas/vimshottari/periods.yaml), [Yogini](vedic/dashas/yogini/periods.yaml), [26 yoga entries](vedic/yogas/), [transits](vedic/transits/evidence.yaml), [Panchang](vedic/panchang/limbs.yaml), [matching profile](vedic/matching/north-profile.yaml), [muhurta](vedic/muhurta/selection.yaml) |
| Jaimini and KP | [Jaimini](jaimini/), [Chara variant](jaimini/chara-dasha/kn-rao-candidate.yaml), [KP significators](kp/significators/bhava360.yaml), [249 exact KP intervals](kp/number-horary/249-divisions.yaml) |
| Western and numerology | [Tropical natal readings](western/natal/), [aspects and orbs](western/aspects/orbs.yaml), [Western timing and relationship methods](western/), [three numerology schools](numerology/), [compound numbers 10–52](numerology/chaldean/compounds.yaml) |
| Reflective and later systems | [78 tarot cards in both orientations](tarot/), [palmistry](palmistry/), [Vastu](vastu/), [Lal Kitab](lal-kitab/), [face reflection](face-reading/) |
| App composition | [All eleven life areas](life-areas/catalog.yaml), [all six checkers](checkers/), [Ask, reports, timelines and family views](modules/), [public and admin explanation fields](shared/explain/payload.yaml) |
| Evidence and editorial review | [Source and edition register](shared/source-editions/catalog.yaml), [typed facts](shared/fact-dictionary/catalog.yaml), [convention profiles](shared/conventions/profiles.yaml), [release flags](governance/release-flags/phases.yaml), [validation](governance/validation/check.py) |

## How a result is assembled

For a vehicle purchase, the checker can explain the registration's derived digit total, its comparison to the person's birth root, an active fourth-house lord and the proposed delivery window. Each explanation links to its own predicate and source. The recipe deduplicates evidence. If a user with unknown birth time supplies a registration, the calculation can still provide its digit details. The missing fourth-house fact limits the personalized reading. A missing fact never supplies a reason for a verdict. [Vehicle recipe](checkers/vehicle-number/recipe.yaml)

For a career question, the present slot binds the active period lord and natal house. The upcoming slot needs the next dated period and its lord. The concerns slot requires a qualifying transit with its origin and dates. The action is a practical prompt in the user's language. Real dates, profile identity and place are bound by the consuming app. [Career recipe](life-areas/career/reading.yaml)

## Checks and remaining release work

The included Python checker requires PyYAML. Run `python kb/governance/validation/check.py` from the repository root. It checks rule shapes, ID uniqueness, location, source references, languages, predicates, unknown-fact behavior, area and checker references, tarot orientation coverage, numerical tables and representative yoga cases.

The raw Ashtakavarga distribution was checked against the published worked values transcribed in the pinned PyJHora test suite. A second calculation using the alternate Rashi multipliers reproduced all seven Rashi and Graha Pindas for the recorded chart. The Shadbala check covers the Sun’s 198-virupa Sthana subtotal. [Raw BAV/SAV example](vedic/strength/ashtakavarga/worked-reference.yaml) · [Reduction comparison](vedic/strength/ashtakavarga/pinda-comparison.yaml) · [Shadbala reference](vedic/strength/shadbala/worked-reference.yaml)

A verified citation supports the claim named in its `supports` field. The 1950 Sastri edition of *Phaladeepika*, for example, supports the Sakata formation and its angular-Moon cancellation. The practical prompts are original editorial adaptations. Many historical passages and regional variants still need edition-level review. The curated personal-name lexicon starts with five meanings and returns an unavailable meaning for unlisted names.

Production release requires native Kannada/Hindi review, approval of rule interpretations and doctrine variants, and integration tests against the actual chart and timing engines. The KB does not contain the Swiss Ephemeris engine, the app UI, licensed card artwork or a production support directory. The selected conventions for D60, the node and dasha-year defaults, KP variants and regional activity rules remain subject to product review. Nakshatra Nadi and gift purchase retain their PRD hold.
