# Synthetic birth and consultation references

The five named charts use the development seed coordinates, Asia/Kolkata and the Gregorian calendar. The consultation instant is local noon on 24 November 2026. The six area worksheets ask about that local day. The monthly reading covers November from local midnight to local midnight, splitting the month at transit sign changes. [Worked readings](../worked-readings/)

Each graha row records its central longitude, speed, combustion, nakshatra, pada, D9 and D10. Dev’s central values describe a working noon. The unstable fields, Moon-relative strength worksheet and confidence projection determine what the reading can use. Sampled intervals include both ends. Exact-time varga lagnas also receive the five-minute stability screen. Dasha timestamps in the admin worksheet are arithmetic reference instants at the supplied working time. Missing periods indicate that the lunar star changes within the declared interval.

## Reproduction

Obtain the data package during package installation. Keep its contents outside the repository. In a temporary directory, run the following commands.

```sh
npm pack @kuntay/swisseph-data@0.2.2
tar -xf kuntay-swisseph-data-0.2.2.tgz
export SWEPH_PATH="$PWD/package/ephe"
```

From the repository root with the dev venv active, run both authoring commands.

```sh
python kb/examples/fixtures/generate.py
python kb/examples/fixtures/workflow.py
```

The generator checks the effective Swiss flags for each body and records SHA-256 hashes for the planetary and lunar files. The ordinary regression validator reads the committed records offline. Its predicate snapshots tie the worked readings to the authored rule conditions. Run the authoring commands intentionally when reviewing a changed convention.

## Reading the same date

Asha’s Taurus Moon places the transiting Moon in the same sign. Her daily and monthly readings both resolve to Supportive. Ravi’s Aquarius Moon gives a different relative placement and star count. Both of his readings resolve to Take care. Each worksheet records the supporting transit IDs and the actual period pair. [Asha](../worked-readings/asha.md) · [Ravi](../worked-readings/ravi.md)

## Review scope

The named charts are synthetic. The classical chapter references remain subject to the verification status in their source entries. The three-degree Mercury threshold, signed phase scale and display gates are editorial conventions. The KB-55 second-cycle Chara case awaits its rule. Older arithmetic scenarios retain file-scoped lookup aliases. [Scenario aliases](../scenario-aliases.yaml)
