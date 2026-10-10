# Additional European operator sources — 9 October 2026

**Research result:** atNorth provides useful primary-source Nordic site identities and unusually explicit distinctions between planned gross power and IT capacity. It is a candidate for reviewed research, not an accepted or openly licensed directory publication. No app/data records changed in this investigation.

## Existing collection and rights audit

The checked-in Equinix and Digital Realty publications already preserve separate source identities, null IT load and editorial receipts. Their `rights` strings describe factual extraction; neither string nor receipt records a publisher permission grant. The catalog README's statement that no commercial directory is scraped predates the HTML-extraction pipelines and needs qualification. These observations come from `data/catalog/README.md`, both directory JSON files, their review receipts and `tools/capture_*directory.py` / `tools/capture_digital_realty.py`.

Digital Realty's published terms restrict copying, republishing and distributing website material; they also restrict linking beyond its home page without consent. This is an unresolved permission concern for the existing bulk directory, exports and facility links. A public JSON array, source hash, attribution or authenticated hosting does not demonstrate publisher permission. [Digital Realty terms](https://www.digitalrealty.com/about/legal/terms).

Equinix's terms include data among protected material and restrict reproduction, distribution and copying to another server without express authorization. They state their scope includes other Equinix-maintained websites; the source directory itself links corporate Terms of Use in its footer. The repository audit found no corresponding grant. [Equinix terms](https://www.equinix.com/about/legal/terms), [directory footer](https://docs.equinix.com/colocation/availability/).

Recommended implementation decision: keep this rights question explicit; do not label publisher extracts as open data or approve additional bulk redistribution merely because the source is accessible. Separately licensed OSM records retain their own provenance and ODbL treatment.

## atNorth directory facts

The official index lists these **13 site codes**, including developments. Its locality and site-type labels are publisher categories, not surveyed coordinates or a count of operating buildings. All rows below are supported by the [official location index](https://www.atnorth.com/nordic-data-centers/).

| Code | Publisher locality | Country | Publisher type |
| --- | --- | --- | --- |
| FIN01 | Helsinki | Finland | Metro Site |
| FIN02 | Helsinki | Finland | Metro Site |
| FIN04 | Myllykoski | Finland | Mega Site |
| FIN05 | Salo | Finland | Mega Site |
| ICE01 | Reykjavik | Iceland | Metro Site |
| ICE02 | Keflavik | Iceland | Mega Site |
| ICE03 | Akureyri | Iceland | Mega Site |
| DEN01 | Copenhagen | Denmark | Metro Site |
| DEN02 | Varde | Denmark | Mega Site |
| SWE01 | Stockholm | Sweden | Metro Site |
| SWE02 | Stockholm | Sweden | Metro Site |
| SWE04 | Solleftea | Sweden | Mega Site |
| NOR01 | Haugaland | Norway | Mega Site |

Minimal proposed factual fields are operator, source code, source locality/country, source type, directly observed official URL and observation date. Leave coordinates, geometry, building count and operating IT load unknown unless separate evidence establishes them. Preserve source spelling and do not synthesize individual buildings from these entries.

## Concrete facility evidence for typed observations

- **FIN05, Salo:** the facility page distinguishes **230 MW gross campus power**, **up to 160 MW IT capacity**, and **60 MW IT capacity for phase one**, with power availability planned for **Q3 2028**. These are development targets, not commissioned load. [FIN05 facility page](https://www.atnorth.com/nordic-data-centers/finland-data-centers/salo-fin05/).
- **FIN05 announcement, 5 October 2026:** first-phase power of **75 MW** is described as secured, with a path to **230 MW** for the wider development and a Fingrid substation connection. Retain the 75 MW claim's native scope rather than converting it to IT load. Expected operator investment is approximately **€2 billion**, excluding customer-owned servers and installation; the separate **up to €10 billion** estimate concerns those possible customer costs. [Dated announcement](https://www.atnorth.com/news/atnorth-to-develop-new-data-center-in-salo-finland/).
- **DEN01:** the page places it in **Ballerup, greater Copenhagen**, labels **30 MW** as campus power capacity and says the first phase went live in **Q4 2025**. Do not interpret this as 30 MW of operational IT load. [DEN01 facility page](https://www.atnorth.com/nordic-data-centers/denmark-data-centers/copenhagen-metro-site/). The June 2026 report instead says DEN01 became operational in **Q1 2026**; keep both milestone claims with their source and scope rather than silently selecting a date. [2025 sustainability report, printed page 6](https://www.atnorth.com/wp-content/uploads/2026/06/Sustainability-Report-2025.pdf).
- **NOR01:** the page describes a future campus in **Haugaland Business Park**, a **36-hectare plot**, initial phases of **120 MW** and a ramp to **350 MW site power**. The reviewed text does not establish those numbers as commissioned IT load. [NOR01 facility page](https://www.atnorth.com/nordic-data-centers/norway-data-centers/haugaland-nor01/).

## Access, reuse and implementation limits

The reviewed atNorth pages are publicly readable and carry an all-rights-reserved notice. No open-data license or bulk directory reuse grant was found in the reviewed index, linked privacy policy or communications disclaimer. Its supplier purchase terms are unrelated to directory redistribution. [Location index](https://www.atnorth.com/nordic-data-centers/), [privacy policy](https://www.atnorth.com/privacy-policy/), [communications disclaimer](https://www.atnorth.com/communications-disclaimer/), [supplier portal](https://www.atnorth.com/supplier-portal/).

This research used the web reader. A bounded local request for `https://www.atnorth.com/robots.txt` failed at DNS resolution; the web reader could not retrieve it either. Robots directives, raw HTML structure, response hashes and an automated capture were **not verified**. No alternate endpoint, credentials, challenge bypass or crawl was attempted. Reuse/access approval therefore remains unresolved; this note is not a new accepted publication or a determination of legal rights.

For a later permitted capture, use a registered official URL and the existing robots-aware, bounded monitor; quarantine parser drift and unexpected disappearance, then require a separate editorial acceptance. Keep identity proposals separate from OSM geometry. Store scoped capacity claims independently from directory rows: FIN05's phase IT target, secured power claim and campus maximum cannot be added together. The 13 directory entries must never enter operating-facility or operational-MW totals by default.
## Implementation follow-up

The continuation added FIN05, DEN01 and NOR01 as three searchable, cited leads
with null coordinates and operating IT power. Sources P23–P27 register the four
operator pages and June 2026 sustainability report for bounded monitoring.
The source-native MW values retain separate scope, planned/disclosed state,
inequality and reporting date. Accepting a discovery keeps it in the candidate
lane; it does not establish a site identity or add capacity to accepted totals.
No publisher images, full prose, PDFs or inferred footprints were copied into
the application. The original archive, 79 project records and current accepted
observation, fact and relationship counts are unchanged.

