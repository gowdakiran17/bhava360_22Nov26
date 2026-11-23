# Glossary

Each file in `entries/` defines one concept. Its dotted ID stays stable across languages. The three user meanings are short definitions. Technical distinctions and school-specific details belong in `admin_note`. The English, Kannada and Hindi indexes in `locales/` use the same keys. For each missing field in Telugu, Tamil, Malayalam, Spanish or French, display that field in English.

The Sanskrit field gives a form in Devanagari and Kannada script. Its usage label distinguishes a traditional term, a modern transliteration and a descriptive rendering. For example, Porutham is Tamil. Its Sanskrit description is a translation. Historic spellings in the earlier core, translation and alias tables remain accessible. Kannada, Hindi and Sanskrit wording is draft pending language review.

## Coverage and lookup

The validator reads the text and paths of the KB's YAML, Markdown, CSV, Python, SVG and extensionless files. It excludes the glossary's own generated vocabulary and Python bytecode. The scan records the normalized words in `scan-vocabulary.txt`. A new word needs classification as a domain concept, spelling variant or ordinary text. The word list includes ordinary prose and implementation vocabulary and is not a list of definitions.

`inventory.txt` is the editable list of glossary headwords. The validator also discovers members directly from domain catalogs, including named calendar intervals, the Tarot deck, illustrated palm choices and divisional charts. This catches a new named catalog member even when its name uses familiar words. Identifying a new technical sense in ordinary prose still requires reading the passage.

For lookup, normalize the search text using the validator's `normalized` function and match a term label, spelling alias or qualified Sanskrit form. English case and Latin transliteration marks fold together. Spaces and hyphens divide words. Kannada and Devanagari vowel signs remain significant. Distinct senses can use qualified names, such as the Moon card and the Moon in a birth chart.

`used_by` lists unique existing KB document IDs where a label occurs, plus explicit conceptual links in `reference_rules`. An optional system scope limits ambiguous names. A document mention can be in a technical note or source citation. For a method described in an ID-less table, `used_in_files` points directly to that table.

Run `python kb/governance/validation/check.py` from the repository root to validate the terminology alongside the reading rules. Glossary records are counted separately from rules that fire on a reading.

## Public glossary copy

An entry marked `visibility: admin-only` is available for staff lookup. The public exporter skips it before creating any message or lookup key. For other entries, `public_label` can supply a localized display name while `term`, Sanskrit forms, and aliases remain available for staff lookup. The required-locale indexes mirror the public labels. The five planned locales can use English fallback. Editorial rewrites carry draft approval and pending Kannada and Hindi review.
