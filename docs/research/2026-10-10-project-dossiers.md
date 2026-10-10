# Project dossier evidence review — 10 October 2026

All 79 archived projects were investigated against operator, utility, government,
regulator and counterparty disclosures. The curated publication grows from 27 to
230 primary source records and adds 703 claims: 530 about established projects
and 173 explicitly contextual claims. There are now 799 current observations,
facts and relationships. The eight research leads remain candidates.

68 projects have project-specific primary claims, up from 14. All 79 have cited
research and an explicit review record. Outcomes are 57 enriched, 14 partial and
eight unresolved identities. These describe this research pass; they are not
completeness scores. Publisher counts use the registered publisher labels and
do not claim independent corroboration for every fact.

The new claims cover identity/location (75), technical design (154), power/energy
(120), development/milestones (175), commercial relationships (70), and
investment/financing (109). Quantities retain their disclosed scope and native
units. No archived power estimate, comparison model, map anchor, original report
or workbook has been rewritten.

## What changed materially

- Microsoft's first Wisconsin Fairwater facility is operational as of its June
  23, 2026 disclosure. Regional spending and the adjacent second facility remain
  separate. [Microsoft announcement](https://news.microsoft.com/source/2026/06/23/microsoft-completes-construction-on-first-datacenter-facility-in-mount-pleasant-wisconsin/).
- Google's 2026 environmental report adds 2025 annual PUE and water balances by
  reported campus/location. Withdrawal, discharge and consumption remain
  separate; location aggregates cannot resolve internal North/East aliases.
  [Google report, pp. 95 and 97](https://sustainability.google/files/1699a2e19277e478b38a659f00cb38398a836e8c/download-1699a2e1.pdf).
- Meta's dated announcements establish Temple serving traffic and Kuna operating
  in 2026. Closed-loop cooling and water use for the majority of the year do not
  establish zero annual water consumption.
  [Temple](https://datacenters.atmeta.com/2026/07/temple-we-are-online/),
  [Kuna](https://datacenters.atmeta.com/2026/09/kuna-we-are-online/).
- Lordstown council minutes reproduce SoftBank's clarification that the Ohio
  site is a small proof-of-concept and manufacturing location. A combined program
  headline cannot be assigned as its campus load.
  [Council minutes, p. 5](https://www.lordstown.com/wp-content/uploads/Council-10-6-25.docx.pdf).
- Project Jupiter's newer power plan uses fuel cells; its microgrid permit and
  data-center building permits are separate processes.
  [Oracle power-plan update](https://www.oracle.com/news/announcement/public-review-opens-for-updated-project-jupiter-power-plan-2026-06-03/),
  [construction-permitting statement](https://www.oracle.com/news/announcement/project-jupiter-statement-on-construction-permitting-2026-09-14/).
- Tesla's Q2 2026 deck reports Cortex compute capacity in MW. The archive's
  undisclosed aggregate is not a verified physical match to either Cortex
  facility. [SEC-filed deck, slide 7](https://www.sec.gov/Archives/edgar/data/1318605/000162828026049213/exhibit991.htm).

Chinese projects retain PFLOPS precision, server/rack counts, heat recovery in
GJ, solar generation capacity, and design PUE. Qianhai's 500 PFLOPS figure is a
planned first phase at FP16. Yangquan's later city-wide 7,000P combines Baidu and
Yunfeng and remains contextual. These are not converted into IT MW or H100
equivalents. The [Chinese project memo](2026-10-10-china-projects.md) links the
corresponding primary disclosures and documents indexed-only report access.

## Research records and reproduction

The detailed memos cite each claim and give source locations, search queries,
identity decisions and missing fields:

- [Google and Microsoft: 27 projects](2026-10-10-google-microsoft-projects.md)
- [Meta, Amazon, xAI and Tesla: 23 projects](2026-10-10-meta-amazon-projects.md)
- [Partners and Stargate: 22 projects](2026-10-10-partners-stargate-projects.md)
- [Chinese operators: seven projects](2026-10-10-china-projects.md)

Their machine bundles are retained in `data/research/`. The explicitly reviewed
claims are integrated into `data/evidence.json` and the SQLite ledger. An exact
URL match reuses the original source identity; older claims remain immutable.
Reimport preserves existing editorial decisions and revision history. New source
captures continue to enter review independently; they do not accept new facts.

The app's **Project research** index searches all reviewed facts. Project and
campus dossiers show six categories, citation buttons, source locators, dates,
context and open questions. Cited exports include those same review records and
separate contextual claim IDs.

## Project-by-project coverage

Counts below include current accepted claims from the original primary layer.
Sources may support either project claims or relevant context. Zero project
claims means the reviewed evidence does not establish the archived physical
identity, not zero installed capacity.

| Project | Outcome | Project claims | Context | Sources | Main remaining gap |
|---|---|---:|---:|---:|---|
| Crusoe — Abilene expansion | enriched | 15 | 3 | 3 | TDLR Buildings 9/10 are plausible adjacent-development candidates but filings do not name Microsoft; context only. |
| Tesla — AI clusters — location not reconciled | unresolved | 0 | 9 | 2 | Archive aggregate-to-cluster mapping unresolved; preserve non-geolocated status |
| Meta — Aiken | enriched | 9 | 0 | 2 | Construction phase and actual opening |
| Google — Arcola | partial | 1 | 6 | 4 | Campus parcel/area |
| Anthropic — Barber Lake | enriched | 11 | 0 | 4 | September 24 amendment supersedes old September 2026 delivery target with Q4 2026–Q1 2027 hall delivery. |
| Oracle — Batam | partial | 0 | 10 | 5 | Oracle region and DayOne NDP physical campus are separately confirmed, but named tenancy linkage is not in reviewed primary pages. |
| Amazon — Berwick | enriched | 9 | 2 | 5 | No confirmed current IT MW or campus chip inventory found |
| Google — Bristow | partial | 0 | 3 | 3 | Exact parcel/campus bridge |
| Google — Cedar Rapids | enriched | 13 | 0 | 3 | Operational phase and date |
| QTS — Cedar Rapids | enriched | 9 | 0 | 2 | No site-specific critical IT capacity or tenant/hardware count verified. |
| CoreWeave — Chester | unresolved | 0 | 7 | 2 | Archive Chester alias not conclusively matched to the Chesterfield development. |
| Meta — Cheyenne | enriched | 11 | 0 | 3 | Operating milestone and actual IT load |
| xAI / SpaceXAI — Colossus 2 | enriched | 8 | 3 | 5 | No operator-confirmed current Colossus 2 IT MW or exact delivered GPU inventory found |
| Google — Columbus | enriched | 11 | 1 | 4 | Current IT MW |
| Google — Council Bluffs East | unresolved | 0 | 6 | 3 | East parcel/campus bridge |
| CoreWeave — Dalton 1 & 2 | unresolved | 0 | 5 | 1 | Archive Dalton 1 & 2 does not match issuer Dalton 1 and Dalton 4 terminology. |
| CoreWeave — Denton | enriched | 8 | 0 | 2 | April issuer property area and November 2024 enlarged city lease area differ; retain both scopes. |
| Meta — Eagle Mountain | enriched | 13 | 0 | 4 | Expanded campus building/floor count |
| CoreWeave — Ellendale | enriched | 12 | 3 | 4 | ELN-04 is called fourth building in financing release and third HPC building later; retain both labels. |
| Microsoft — Fairwater Atlanta | enriched | 7 | 0 | 1 | Exact surveyed parcel and Fayetteville identity bridge |
| Microsoft — Fairwater Wisconsin | enriched | 9 | 1 | 3 | Critical IT MW |
| Google — Fort Wayne | enriched | 9 | 1 | 4 | IT MW |
| Meta — Gallatin | enriched | 12 | 0 | 3 | Current as-built area and building count |
| Microsoft — Goodyear | partial | 1 | 5 | 4 | Archive campus-to-PHX building code mapping |
| Huawei — Gui’an cloud data center | enriched | 7 | 0 | 2 | Reconcile later A4 and high-end AI phases with this original campus. |
| CoreWeave — Helios | enriched | 29 | 0 | 5 | Phase II delivery and rental forecasts remain forward-looking. |
| Meta / QTS — Hillsboro 2 | unresolved | 0 | 9 | 3 | Primary source mapping Meta to Hillsboro 2 or specific Huffman buildings absent |
| Huawei — Horinger | partial | 3 | 2 | 2 | Resolve parcel/building identity against the archive’s modeled project. |
| Meta — Huntsville | enriched | 12 | 0 | 3 | Current building count and site-wide IT load |
| Meta — Hyperion | enriched | 14 | 4 | 7 | Actual energization/IT commissioning |
| Meta — Jeffersonville | enriched | 13 | 0 | 3 | Verified opening and energized IT MW |
| Google — Kansas City East | unresolved | 0 | 8 | 2 | East parcel/phase bridge |
| Meta — Kuna | enriched | 16 | 0 | 4 | Current campus building area after AI redesign |
| Anthropic / Fluidstack — Lake Mariner | partial | 14 | 2 | 3 | No direct Anthropic Lake Mariner lease or equipment allocation verified in reviewed primary sources. |
| Google — Lancaster | partial | 3 | 8 | 3 | Google leased MW and floor-area allocation |
| Google — Lincoln | enriched | 8 | 0 | 4 | Critical IT MW |
| SenseTime — Lingang AIDC | enriched | 10 | 1 | 4 | Resolve the latest site-versus-SenseCore network compute scope. |
| OpenAI — Lordstown | enriched | 5 | 1 | 3 | Proof-of-concept has unspecified small IT load; no site MW figure verified. |
| Meta — Los Lunas | enriched | 10 | 1 | 3 | Current as-built building/floor count |
| Amazon — Madison | partial | 0 | 8 | 4 | Exact archive-to-parcel or campus identity unresolved |
| CoreWeave — Marble | enriched | 5 | 1 | 2 | Historical 2019 renovation area and 2026 IT white space are different measures. |
| Google — Mesa | enriched | 6 | 0 | 2 | Current operating status |
| Google — Midlothian | enriched | 6 | 1 | 3 | IT MW |
| Meta — Montgomery | enriched | 12 | 0 | 3 | Reconcile expanded PDF employment and directory values |
| CoreWeave — Muskogee | enriched | 12 | 0 | 3 | Original 70 MW IT/100 MW grid building versus gigawatt-scale future expansion are separate phases. |
| Microsoft — Narvik | enriched | 11 | 0 | 3 | Delivered Microsoft GPU count |
| Amazon — New Albany | partial | 1 | 10 | 4 | Exact archive campus/parcels unresolved |
| Google — New Albany | enriched | 13 | 0 | 4 | Critical IT MW |
| Amazon / Anthropic — New Carlisle | enriched | 14 | 3 | 3 | No primary building-by-building commissioned IT load or exact chip allocation found |
| Microsoft / Nebius — New Jersey | enriched | 10 | 0 | 2 | Exact Microsoft allocation in MW |
| CoreWeave — Norway | enriched | 5 | 5 | 4 | Primary partnership names Bulk N01 but does not disclose CoreWeave's leased MW or installed chip count. |
| Google — Omaha | enriched | 5 | 2 | 3 | IT MW |
| Google — Papillion | partial | 3 | 2 | 3 | Municipal primary archive access |
| Microsoft — Project Osmium | enriched | 7 | 0 | 2 | Current installed IT capacity |
| Meta — Prometheus | enriched | 13 | 2 | 4 | Actual full-cluster operating milestone |
| Google — Pryor North | unresolved | 0 | 5 | 2 | North parcel/phase bridge |
| SenseTime — Qianhai intelligent computing center | enriched | 7 | 0 | 1 | Find current deployed compute, electrical capacity and commissioning updates. |
| Tencent — Qingyuan | partial | 6 | 2 | 3 | Separate Qingxin and Qingcheng campuses and their individual buildings. |
| xAI — QTS Atlanta | unresolved | 0 | 7 | 1 | No primary xAI–QTS Atlanta tenancy, contract or precise building mapping found |
| Google — Red Oak | partial | 4 | 1 | 3 | Site-specific capex |
| Amazon — Ridgeland | enriched | 3 | 7 | 6 | No primary campus IT MW, chips, gross capacity or verified all-building opening date found |
| Hut 8 — River Bend | enriched | 20 | 0 | 6 | Initial Q2 2027 delivery remains target. |
| Meta — Rosemount | enriched | 11 | 0 | 2 | Reconcile 725,000 plan versus 715,000 subsequent descriptions |
| Meta — Sarpy | enriched | 11 | 1 | 4 | Current as-built commissioning status of nine-building program |
| Microsoft — SAT14 | enriched | 7 | 0 | 2 | Critical IT capacity |
| Microsoft — SAT40 | enriched | 6 | 0 | 1 | Commissioning date |
| Oracle / OpenAI — Stargate Abilene | enriched | 16 | 0 | 5 | TDLR accessibility inspection is not compute commissioning. |
| OpenAI — Stargate Michigan | enriched | 9 | 0 | 3 | GW disclosure lacks explicit IT/gross definition. |
| OpenAI — Stargate Milam | enriched | 8 | 0 | 3 | OpenAI January 2026 1.2 GW lease versus undated SB Energy approximately 750 MW total capacity unresolved. |
| OpenAI — Stargate New Mexico | enriched | 10 | 0 | 4 | Capacity is announced AI scope without explicit IT/gross boundary. |
| OpenAI — Stargate Shackelford | enriched | 9 | 0 | 3 | 1.4 GW GPU compute figure lacks explicit critical IT definition. |
| OpenAI — Stargate UAE | enriched | 9 | 1 | 2 | First 200 MW launch target for 2026 not confirmed operational. |
| OpenAI — Stargate Wisconsin | enriched | 9 | 1 | 3 | H2 2027 first customer delivery versus 2028 full completion are different scopes. |
| Google — Storey | enriched | 4 | 3 | 3 | IT MW |
| Meta — Temple | enriched | 14 | 0 | 3 | Current as-built floor area |
| Google — The Dalles | partial | 6 | 5 | 4 | Exact archive campus boundary |
| Google — Waltham Cross | enriched | 13 | 1 | 3 | Critical IT MW |
| Baidu — Yangquan cloud center | enriched | 4 | 2 | 2 | Find current Baidu-only compute, arithmetic precision and electrical MW. |
| Alibaba — Zhangbei | partial | 5 | 2 | 4 | Resolve the precise campus and building identifiers. |
