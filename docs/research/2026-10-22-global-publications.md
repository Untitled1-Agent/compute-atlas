# Complete Epoch AI public publications — 22 October 2026

Two independent CC BY 4.0 publications add global hardware and dated data-center
research. Every captured row and source field is preserved. This is complete
coverage of these downloaded publications, not a claim to have enumerated all
compute infrastructure in the world.

## GPU clusters

Source: [Epoch AI GPU clusters](https://epoch.ai/data/gpu-clusters),
[public CSV](https://epoch.ai/data/gpu_clusters.csv),
[documentation](https://epoch.ai/data/gpu-clusters-documentation).
The publisher page labels its download **13 March 2026**. Capture date is
**22 October 2026**; those dates have different meanings.

The complete CSV contains **482 records and 57 columns**, spanning **36 named
countries/territories**. **447** rows have published coordinate pairs; **35** do
not. **190** rows are named “Anonymized Chinese System”, including mainland China
and Hong Kong source groups. Names and individual links remain withheld, and
publisher-rounded values retain their original precision. No attempt is made to
identify these records. **30** rows name a successor; predecessor phases remain
searchable and are never automatically added to successors as current capacity.

The source page explicitly licenses the public dataset under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Its public-data
boundary includes anonymized Chinese/Hong Kong records; private underlying
source details are outside this capture. Raw CSV bytes are preserved at
`data/catalog/epoch-gpu-clusters.csv`; the normalized publication retains every
cell verbatim in `fields`, source row number and content hash. Named records use
a name-derived identifier. Anonymous record IDs derive from row content and
occurrence, and do not imply stable identity across changed publications.

Reported power, calculated power, the selected power field, H100 equivalents,
chip quantities, costs and source notes remain separate. Epoch's calculated
power includes assumptions about other hardware and facility overhead; it is
not substituted for reviewed critical IT load. Source coordinates retain their
published precision without a claim of independent survey verification.

## AI data centers and all supporting tables

Source: [Epoch AI AI data centers](https://epoch.ai/data/ai-data-centers),
[complete source ZIP](https://epoch.ai/data/data_centers/data_centers.zip).
The publisher page labels its download **20 October 2026**. Capture date is
**22 October 2026**. The archive's `README.md` explicitly permits reuse under
CC BY 4.0 and supplies the Epoch AI citation.

| Source table | Rows | Columns |
| --- | ---: | ---: |
| AI data centers | 95 | 16 |
| Development timelines | 567 | 14 |
| Chip deployments | 239 | 11 |
| Chillers | 143 | 12 |
| Cooling towers | 527 | 17 |
| Accelerator reference | 32 | 14 |
| **All source rows** | **1,603** | |

The exact ZIP is embedded in `data/catalog/epoch-data-centers.json`, alongside
its SHA-256, per-file hashes, source README, parsed tables and source row numbers.
The standalone app downloads these original ZIP bytes without network access.
Every timeline/deployment parent name resolves to a unique source data-center
record. All original names, dates, confidence tags, role associations, source
links, quotations and estimation notes remain present. The source's “Current”
column names describe the dated publication, not live telemetry.

Timeline plots distinguish IT power from facility power, theoretical performance,
capital cost in 2025 USD billions and water use in MGD. Observations after the
publisher date are shown as future projections. Missing values have no plotted
point and remain explicit in the source rows; no interpolation or cross-campus
sum is introduced. Cooling references and accelerator specifications do not
establish equipment installation at any campus. The center CSV has addresses
but no coordinates; no coordinates are inferred from those addresses or copied
from similarly named archive projects.

## Review and reproducibility

`tests/test_global_publications.py` compares all normalized cells to independent
raw CSV/ZIP bytes, verifies uniqueness, parent references, hashes, missingness
and anonymity, and rejects incomplete schemas and invalid coordinates.
`tools/capture_gpu_clusters.py` and `tools/capture_data_centers.py` generate
candidate publications from fixed official endpoints or a local raw capture.
The latter requires the observed publisher date as an explicit argument.
Capture tools do not alter the accepted evidence ledger or automatically publish.

The two publisher pages read during acquisition had these SHA-256 fingerprints:

- GPU-cluster page: `f981ae5d774d4a15671e71950bf287e5452c2592076e26e2a6958922ae7f5137`
- Data-center page: `337ff47a9aa3e24655a7e351b37bf29ffd978f3e834e4c9a79546272a9f51d93`

Original research dossiers, community geometry, Equinix and Digital Realty remain
independent publications. No name similarity or proximity automatically assigns
ownership, source geometry, IT power, or a facility-to-cluster relationship.
