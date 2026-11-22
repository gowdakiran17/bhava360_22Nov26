# Bhava360 knowledge base

Open the [edition 1 coverage guide](COVERAGE.md) for authored content, validation results and release status.

A rule lives once under its system and topic. Checkers, life areas and reports reference approved rule IDs. A business-start reading can therefore explain which facts came from the chart, name calculation and choice of date. Each reason keeps its system, convention and evidence.

## Foundation registers

Authors allocate rule IDs using [identifiers](governance/review/identifiers.yaml), select tags from the [area catalogue](life-areas/catalog.yaml), and bind predicates to the [fact dictionary](shared/fact-dictionary/catalog.yaml) and [convention profiles](shared/conventions/profiles.yaml). Citations resolve through the [edition register](shared/source-editions/catalog.yaml). Use the [core glossary](glossary/terms/core.yaml) and [privacy and copy policy](shared/boundaries/policy.yaml) when drafting. Registry version 1 covers the existing examples. Add typed facts and verified editions as later topics need them.

## Folder map

Each space-separated name on the right is a child directory. The Vedic root owns shared Jyotish vocabulary and Parashari rules. Jaimini and KP have their own doctrine profiles. The topic is the path relative to the system root, for example houses or dashas/vimshottari.

```text
vedic/                 planets signs houses nakshatras padas lordships karakas aspects dignity strength vargas yogas doshas dashas transits panchang matching muhurta prashna relocation annual-chart rectification festivals
vedic/strength/        shadbala bhava-bala ashtakavarga
vedic/dashas/          vimshottari yogini
jaimini/               chara-karakas karakamsa arudha-padas rashi-drishti argala chara-dasha
kp/                    cusps star-sub-lords significators ruling-planets number-horary
western/               natal houses aspects transits synastry personal-horoscopes progressions solar-arc composite
numerology/            ank-jyotish chaldean pythagorean lo-shu kua
vastu/                 directions entrances rooms layouts chart-fit
tarot/                 major-arcana minor-arcana orientations spreads positions draws journal lessons
palmistry/             hands fingers mounts lines guided-observations
lal-kitab/             fixed-houses placements varshphal
face-reading/          consent confirmed-observations reflection
glossary/              terms aliases translations
shared/                conventions fact-dictionary source-editions boundaries traditional-practices explain localization
checkers/              business-name mobile-number personal-baby-name house-relocation vehicle-number big-decision-muhurta
life-areas/            career love-marriage money health family-home learning travel-relocation property-vehicles children business spirituality
modules/               first-look home timeline ask reports matching planning notifications family-together
governance/            review release-flags validation
on-hold/               nakshatra-nadi gift-purchase
templates/             # authoring contract
examples/              # synthetic documentation fixtures, excluded from publishing
```

## How entries work

Use one YAML document per rule or meaning. Keep IDs stable across title or translation edits. The template is a draft to copy. A fact-dictionary record declares its key, type, units, reference point, input dependencies and producing engine. Convention records pin the doctrine and calculation settings, including engine version, zodiac/ayanamsa, node, house system, sunrise method and dasha year where applicable. Keep proposed defaults versioned until the owner confirms them. A source-edition record identifies translator/editor, publisher and edition. Cite the locator in that edition. Record page, section or card identifier where verse numbering does not apply.

Conditions use recursive all/any/not nodes and typed leaves with fact, op and value. eq compares like types, in tests membership in a literal list. Chart D1, house origin and counted-from body are explicit in the fact key. An absent or time-unstable required fact yields unknown. An all group fails on any false and an any group succeeds on any true. Otherwise an unknown propagates, including through not. An empty condition group is invalid. Render a personal interpretation only on a true match with a compatible convention and approved rule. Unknown birth time suppresses Lagna-dependent facts. Flag approximate times and varga changes within the PRD's ±5 minute window. Hold D60 readings pending convention approval.

Strength notes pair a predicate with a stronger/weaker effect and its explanation. Exceptions pair a predicate with an effect (soften or cancel) and a reason. Apply exceptions before composing the reading and preserve the formation and cancellation evidence. Show approved cancelled yogas as “present but softened” with the reason. If a material qualifier is unknown, withhold the unqualified conclusion. An empty list in a draft means unresearched until review. Record doctrinal variants as separate profiles and link their IDs. Never execute one school's exception against another school's formation.

A match at runtime binds rule ID, profile, convention, evidence facts, any real effective dates and confirmed observation or draw IDs as applicable. The public explain sheet resolves definition, personal implication, timing where available and “Based on” chips. Rule IDs, sources, raw strengths, bindus, prompts and confidence stay in admin/tester responses. AI receives only permitted facts and each generated sentence carries ✦ AI. Deterministic text is the fallback. Keep Western tropical readings separate. Report mixed signals when KP and Vedic evidence differ. Tarot uses drawn cards and positions, palmistry uses confirmed features. Neither needs an invented chart placement.

## Life areas and module coverage

The six MVP keys are career (Career & work), love-marriage (Love & marriage), money (Money & wealth), health (Health & energy), family-home (Family & home) and learning (Learning & growth). Display names await owner confirmation. R2 adds travel-relocation (Travel & abroad), property-vehicles, children, business and spirituality. Enable tags independently of area screens. Every area has four slots for present situation, dated upcoming periods, concerns to watch and practical actions. Each slot references matched evidence or explains the input limitation. Health covers everyday wellbeing.

| PRD | KB responsibility |
|---|---|
| 8.1–8.3 | First look selects three computed insights. Bind the active profile, birth-time precision, language and consent. Maintain fixed glossary translations and native review flags. Accounts, OTP, deletion and human-approved legal text belong to the app. |
| 8.4 | Vedic, Jaimini and KP folders own D1 through horary, including all 16 vargas, distinct Moon/Lagna transit evidence, Panchang, matching and muhurta. Planning uses the selected timing city and zone. Relocation preserves the natal instant and chart. |
| 8.5–8.8 | Western, numerology, palmistry and tarot own their respective facts and meanings. Any later general Western sign text has its own labelled surface outside personalized retrieval. |
| 8.9–8.10 | Home composes Today/Week/Month, dasha chapter, area summaries and upcoming personal changes. Timeline, local timing windows and area detail reuse dated facts. |
| 8.11 | Ask routes relocation, job change, business start, marriage timing, purchases and studies to the corresponding area, timing and checker evidence. Sensitive questions use approved fixed responses. |
| 8.12–8.13 | Reports map Career, Yogas, Year ahead, Marriage, Money, Full life, Matching and later area books to approved sections. Gate annual placements on the annual engine. Exclude health books. Pricing, entitlements and payment stay in commerce configuration. |
| 8.14–8.15 | Notification templates reuse approved dated facts in the current zone. Admin owns source review, doctrine variants, fixture checks, approval history and module flags. |
| 8.16–8.17 | Six checker recipes below. Reserve later Lal Kitab, guided Vastu, face reflection, full Tajika/Varshaphal, rectification, festivals calendar and Together. Keep Nakshatra Nadi and gifting on hold. |

## Checker recipes

Each recipe declares required inputs, allowed fact keys per system, eligibility, explanation slots and practical next actions. Compare up to three options. For a complete verdict require three distinct traceable reasons and one engine-selected tone (Supportive / Steady / Take care). If evidence is insufficient, explain the missing input. Keep reasons labelled by system. Save only by choice.

| Checker | Inputs → evidence and output |
|---|---|
| Business name | Latin spellings, owner, optional business type/date → separate name numbers, opening syllable against nakshatra, Moon/Lagna lords and houses 10/7/11. Link launch muhurta. India brand-list filter defaults on. |
| Mobile number | Ten digits and profile → total, compound, repeated/missing digits, Moolank/Bhagyank fit. Process transiently. Only derived facts enter AI. Raw numbers never enter logs and require explicit save for storage. |
| Personal/baby name | Candidate spellings, correct adult/baby profile, chosen system → curated name meaning, number and namakshar lookup across all 108 padas. Link syllable suggestions. |
| House/relocation | Candidate city or entrance/facing, layout and house number, profile and moving month → relocated chart at the same instant, houses 4/9/12/10, dasha and transit evidence for city. For a dwelling use labelled Vastu, number, Moon and fourth-house reasons. Link moving windows. Full form is R2. |
| Vehicle number | Registration, profile, optional purchase date → derived total, Moolank/Bhagyank and fourth-house evidence. Link purchase/delivery windows. Apply mobile-number privacy rules. Exclude accident predictions. |
| Big-decision muhurta | Activity, place, date range and participants → hard exclusions first, split at exact boundaries, then order eligible windows. Explain each person's Tara/Chandra bala. Marriage needs both profiles. Cover marriage, business launch, property/vehicle purchase, moving and job start. |

Use a shared activity catalogue for everyday travel, starting work, purchase, signing, puja, important talks, family visits, focused work and later naming. Sections 8.4.11 and 8.16 give different release signals for marriage, moving and vehicle activities. Reserve them now and gate each on validated exclusions and an owner-confirmed release.

## Writing and publication

- Write the rule and meaning independently in plain language after consulting the source. Cite book, edition, chapter and verse or equivalent locator. Never copy a translation, another app's copy or card artwork. Link sources to the claims they support.
- Mark uncertain drafts with a review note. Confidence (high, medium, disputed) describes support within the named tradition. It is separate from approval. Record competing readings and verify exact references before advancing draft → validated → approved.
- Use gentle may/can equivalents in English, Kannada and Hindi. Have native reviewers check terminology, tone and meaning in context. Preserve the PRD reading footer and the additional reflection line for tarot, palmistry and face reading in all locales.
- Avoid fear, guarantees, urgency, scores, lucky/unlucky labels and medical, financial, legal, pregnancy or lifespan verdicts. Use approved sensitive-topic responses. Matching alone may show traditional points as text. Keep palm and face observations within the PRD's consent and inference limits.
- Offer practical actions first. A remedy may be null. Allowed practices are optional, free mantra, charity or conduct, labelled “Traditional practice.” Exclude gems, crystals, lucky colours, paid rituals and sales.
- Publish approved entries with verified sources, language review and compatible evidence only. Check positive, negative, missing-input and relevant cancellation cases. Examples stay outside ingestion. No synthetic person or placeholder dates in production output.

## Original authoring sequence

1. Freeze IDs, life-area keys, edition register, convention profiles, fact types, glossary translations, privacy and copy boundaries.
2. Build Parashari D1 vocabulary, nakshatra/pada and namakshar tables, house lords, aspects, dignity and birth-time limits.
3. Cover all 16 varga views, then D1/D9/D10 readings, Shadbala, Bhava bala and Ashtakavarga including reductions and Pinda.
4. Add verified yoga/dosha formation, modifiers and cancellations, then Vimshottari, transits, Vedha and dated Saturn phases.
5. Add location-aware Panchang, matching with exceptions, and activity-specific muhurta exclusions and windows.
6. Fill checker dependencies first (system-labelled name/digit calculations, curated names, relocated charts), then validate all six checker recipes.
7. Compose the six launch life areas, four-part details, Home, timeline, first look, Ask, explain sheets, reports and notification inbox from those entries.
8. Add R2 deep vargas, Yogini, Jaimini/Chara, Prashna, KP, Dashakoota and full house Vastu form. Extend the five additional life areas, reports and notifications.
9. Fill Western natal/transit/synastry, full numerology schools and tarot's 78 cards, orientations, spreads and journal.
10. Fill R3 palmistry, Western progressions/solar arc/composite, custom tarot and lessons. Stage Lal Kitab, full Vastu, face reflection, annual charts, rectification, festivals and family Together under their release flags. On-hold subjects require a new product decision.

The [Parashari D1 guide](vedic/D1.md) explains how to combine the registers, identify house lords and handle uncertain birth times.
