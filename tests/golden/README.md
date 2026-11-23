# Vedic position benchmarks

The six rows in [vedic.json](vedic.json) cover Asha, Ravi, Meera, Kabir and Dev (known noon and unknown time). Coordinates are copied from the development city's gazetteer seed. The independent Python generator resolves civil time with zoneinfo, computes Gregorian JD with swe.julday, and calls native pyswisseph separately from the TypeScript WASM adapter. Both bindings implement Swiss Ephemeris; this cross-check exercises bindings, inputs, time handling and result assembly against the same astronomical model.

To regenerate the checked-in expected values after setup, run `.venv/bin/python tests/golden/generate_vedic.py`. Review numerical changes and the embedded library/version, mode, node and backend provenance before committing them. The ordinary test suite reads the committed file and runs offline after installation.

```bash
TZ=UTC pnpm exec vitest run tests/golden/vedic.test.ts
TZ=America/Los_Angeles pnpm exec vitest run tests/golden/vedic.test.ts
```

Each run prints fixture, quantity, runtime value, independent reference, absolute delta and provenance. Longitude deltas use circular distance. The budgets are 0.002° for graha/node longitude, 0.001° for ayanamsa and 0.01° for Lagna. Speed is tested in degrees per day. Unknown-time Lagna is withheld and is tested as null.
