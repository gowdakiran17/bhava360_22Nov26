# Engine export

Run from the repository root with Python 3.10+, Git, PyYAML and jsonschema 4.18+.

```sh
python kb/export/build.py
python kb/export/test_export.py
python kb/export/build.py --check
```

The builder reads committed YAML and illustration assets through Git. The default revision is HEAD. Use `--revision <commit>` to build an earlier authoring snapshot. The manifest records the most recent commit affecting those inputs, along with the export format version, authoring schema version, chart conventions, counts, exact byte sizes and SHA-256 of each payload. It excludes timestamps. With the same exporter and source revision, the output is byte-identical. Changes to uncommitted authoring files are outside that snapshot.

The builder validates every serialized document against its Draft 2020-12 schema before replacing the distribution. Manifest schema paths resolve relative to `kb/export/`. The manifest itself uses `schema/manifest.json`. Shared schemas apply to all files of the same shape. `--check` rebuilds in memory and checks the exact file set and bytes on disk.

## Loading a reading

1. On the engine side, select a route from `admin/routing.json`. Keys under `area/`, `tool/` and `screen/` identify candidate sets. The six checker routes include their recipe evidence. Profile, language, privacy and payment screens have empty candidate lists because they perform no reading.
2. Load the relevant `admin/<system>.json` records. Evaluate only candidates applicable to the selected system, participants, input mode, local time and calculation settings. Apply fact predicates, exclusions, weights, consent, release and approval gates. Route membership alone supplies no evidence. The current rules are drafts for admin/tester use.
3. A canonical record carries its evidence alias IDs. Legacy references can be resolved by reversing these lists. The life-area tags include the original routes of the aliases. Copy aliases retain separate rule IDs and conditions under `copy_owner`, and reuse a single translation key. The administrative source and edition locators retain their historical identifiers.
4. Return a matched record’s opaque `public_key` to the rendering layer. In `public/<system>.json`, it selects the user text key, optional free remedy and any authored tone. A null tone delegates to the appropriate composition policy. The public view contains display data. The administrative view, routing file and manifest belong on the engine side.
5. Resolve each message key in `public/locales/<locale>.json`. All eight bundles have the complete key set. Each missing translation falls back independently to English. `admin/catalog.json` maps named resources, including glossary terms, remedy options, life-area summaries, palm choices and spread positions, to opaque entries in `public/catalog.json`. The health summary's footer is always appended.

The administrative system files also contain their named calculation tables and configuration documents, keyed by the original KB paths. Shared facts, conventions, governance, glossary metadata, checker recipes, summaries and remedies are in the administrative catalog. Guided palm diagrams are included as static SVG strings at their existing resource paths. Original Python implementations of the seeded Tarot draw and guided palm selection remain in their KB modules.
