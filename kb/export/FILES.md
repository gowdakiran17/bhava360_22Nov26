# KB-31 export inventory

Source commit `a8780e456cdb16ceff4dc7ec9fd1145b186ed9cf`. The 32 JSON files total **9,764,385 bytes**.

| File | Bytes | Schema |
|---|---:|---|
| [admin/catalog.json](../dist-json/admin/catalog.json) | 1,819,385 | [admin-catalog](schema/admin-catalog.json) |
| [admin/face-reading.json](../dist-json/admin/face-reading.json) | 1,694 | [admin-system](schema/admin-system.json) |
| [admin/jaimini.json](../dist-json/admin/jaimini.json) | 65,306 | [admin-system](schema/admin-system.json) |
| [admin/kp.json](../dist-json/admin/kp.json) | 71,444 | [admin-system](schema/admin-system.json) |
| [admin/lal-kitab.json](../dist-json/admin/lal-kitab.json) | 15,666 | [admin-system](schema/admin-system.json) |
| [admin/numerology.json](../dist-json/admin/numerology.json) | 119,270 | [admin-system](schema/admin-system.json) |
| [admin/palmistry.json](../dist-json/admin/palmistry.json) | 246,274 | [admin-system](schema/admin-system.json) |
| [admin/routing.json](../dist-json/admin/routing.json) | 456,332 | [routing](schema/routing.json) |
| [admin/tarot.json](../dist-json/admin/tarot.json) | 369,801 | [admin-system](schema/admin-system.json) |
| [admin/vastu.json](../dist-json/admin/vastu.json) | 204,917 | [admin-system](schema/admin-system.json) |
| [admin/vedic.json](../dist-json/admin/vedic.json) | 2,148,043 | [admin-system](schema/admin-system.json) |
| [admin/western.json](../dist-json/admin/western.json) | 558,000 | [admin-system](schema/admin-system.json) |
| [manifest.json](../dist-json/manifest.json) | 6,442 | [manifest](schema/manifest.json) |
| [public/catalog.json](../dist-json/public/catalog.json) | 86,741 | [public-catalog](schema/public-catalog.json) |
| [public/face-reading.json](../dist-json/public/face-reading.json) | 137 | [public-system](schema/public-system.json) |
| [public/jaimini.json](../dist-json/public/jaimini.json) | 3,170 | [public-system](schema/public-system.json) |
| [public/kp.json](../dist-json/public/kp.json) | 1,891 | [public-system](schema/public-system.json) |
| [public/lal-kitab.json](../dist-json/public/lal-kitab.json) | 1,408 | [public-system](schema/public-system.json) |
| [public/locales/en.json](../dist-json/public/locales/en.json) | 344,110 | [locale](schema/locale.json) |
| [public/locales/es.json](../dist-json/public/locales/es.json) | 344,110 | [locale](schema/locale.json) |
| [public/locales/fr.json](../dist-json/public/locales/fr.json) | 344,110 | [locale](schema/locale.json) |
| [public/locales/hi.json](../dist-json/public/locales/hi.json) | 648,807 | [locale](schema/locale.json) |
| [public/locales/kn.json](../dist-json/public/locales/kn.json) | 672,271 | [locale](schema/locale.json) |
| [public/locales/ml.json](../dist-json/public/locales/ml.json) | 344,110 | [locale](schema/locale.json) |
| [public/locales/ta.json](../dist-json/public/locales/ta.json) | 344,110 | [locale](schema/locale.json) |
| [public/locales/te.json](../dist-json/public/locales/te.json) | 344,110 | [locale](schema/locale.json) |
| [public/numerology.json](../dist-json/public/numerology.json) | 9,935 | [public-system](schema/public-system.json) |
| [public/palmistry.json](../dist-json/public/palmistry.json) | 8,512 | [public-system](schema/public-system.json) |
| [public/tarot.json](../dist-json/public/tarot.json) | 16,025 | [public-system](schema/public-system.json) |
| [public/vastu.json](../dist-json/public/vastu.json) | 10,102 | [public-system](schema/public-system.json) |
| [public/vedic.json](../dist-json/public/vedic.json) | 127,483 | [public-system](schema/public-system.json) |
| [public/western.json](../dist-json/public/western.json) | 30,669 | [public-system](schema/public-system.json) |

## Coverage

The 77 routes reach all 1,699 canonical rules through non-admin reading screens or tools. All 1,812 source IDs resolve, including 113 evidence aliases. The 26 copy aliases share localized wording and retain separate predicates. All 1,202 rules identified by KB-30 as having only glossary backlinks have a reading route. Each of the eight locale bundles contains 3,702 message keys.

The manifest inventories each payload with its SHA-256 digest. The export test suite checks those bytes and schema assignments, public field isolation, exact source coverage, routing, and per-field English fallback.
