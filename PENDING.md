# Pending Ideas

## PRODID-driven discovery strategy

`scripts/prodid.py` reports which ICS platforms appear across our cities (see `docs/prodid.md`). This suggests a two-pronged discovery strategy:

**1. Fill gaps in existing cities.** The PRODID report shows which platforms appear in which cities. Platforms found in some cities but not others are likely present but undiscovered. For example:

| Platform | Have it in | Missing from |
|----------|-----------|--------------|
| LibCal (Springshare) | raleighdurham | All other cities (every library system uses it) |
| Localist | bloomington, raleighdurham | davis, petaluma, santarosa, toronto |
| Tockify | bloomington, petaluma, toronto | davis, santarosa, raleighdurham |
| CivicPlus (ical.net) | santarosa, raleighdurham | bloomington, davis, petaluma |
| Bedework | raleighdurham | Any city with a university |
| Google Calendar | bloomington, petaluma, santarosa | davis, toronto, raleighdurham |
| GrowthZone | petaluma | All other cities (chambers of commerce) |

Search for each missing platform in each gap city. Many will turn up hits.

**2. Discover new platforms.** When a new city's feeds produce an unclassified PRODID (shown in the "Unclassified" section of `docs/prodid.md`), that's a platform we haven't seen before. Add it to `PLATFORM_MAP` in `prodid.py`, then search for it retroactively across all existing cities.

## Cache-busting for XMLUI components

Edge browser aggressively caches `.xmlui` component files, making it hard to see updates after deployment. Consider adding cache-control headers or version query params to component file loading.
