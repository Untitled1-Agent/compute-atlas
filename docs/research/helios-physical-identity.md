# Helios physical identities and phase links — 11 October 2026

Decision research for [issue #34](https://github.com/Untitled1-Agent/compute-atlas/issues/34).
This note recommends publication boundaries; it changes no application data,
accepted claims, geometry or operating status. Review distinguishes a primary
publisher's statement, a manually reviewed correspondence, an inference and an
unresolved question. Sources were accessed on 11 October 2026 unless stated.

## Decision

Publish the existing long roof as **historical, manually interpreted geometry**.
A separate, dated visual identity review can connect it to the operator's
data-center depiction. Publish the three station correspondences below as
**reviewed interpretations with original community tags preserved**. Do not
publish a complete campus inventory, exact current utility circuit, current
building status, surveyed boundary, height or roof-specific IT capacity from
this evidence set.

The source caption supports a relation to a **Phase I campus illustration**.
It does not establish an allocation of the phase's entire IT load to that roof.
Keep physical `phase_id`, `it_power_mw` and `operating_status` unset. A cited
`depicted_in_phase_update` relationship may record the narrower association,
provided it cannot be mistaken for a capacity, lease or serving relationship.
This is an editorial decision after reviewing the separately scoped disclosures
below, rather than a primary-source geospatial assertion.

## Dates and primary facts

| Evidence | Primary fact and exact locator | Date to retain |
|---|---|---|
| NAIP raster | [USGS image service query](https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/query?f=json&where=Category%3D1&geometry=%7B%22x%22%3A-100.8690495%2C%22y%22%3A33.7744161%2C%22spatialReference%22%3A%7B%22wkid%22%3A4326%7D%7D&geometryType=esriGeometryPoint&spatialRel=esriSpatialRelIntersects&outFields=OBJECTID%2CName%2CYear%2Cacquisition_date%2Cagency%2Cresolution_value%2Cdownload_url&returnGeometry=false&orderByFields=acquisition_date+DESC&resultRecordCount=10), feature `OBJECTID=190775`, `Name=m_3310010_sw_14_060_20220905`; USDA, 0.6 m native resolution, acquisition timestamp `1662336000000`. The bounded query at the roof returned this one raster. | Image observation **2022-09-05**; retrieval and interpretation **2026-10-11**. Native resolution is different from the resampled display crop's pixel size. No claim that this is the newest image anywhere. |
| Operator illustration | [Galaxy Q2 overview](https://www.sec.gov/Archives/edgar/data/1859392/000185939226000084/exhibit992-q22026overvie.htm), slide **17**, numbered callouts: one AI data-center building exceeding 125,000 ft²; chiller, electrical and water facilities; a Galaxy-owned 345 kV station with up-to-900 MW transformer scope; WETT's Cottonwood and Pitchfork stations at 345 kV. | Update/caption month **2026-07**; exact photographic day and independently verified acquisition date unknown. |
| Filing | [SEC filing index](https://www.sec.gov/Archives/edgar/data/1859392/000185939226000084/0001859392-26-000084-index.htm), accession **0001859392-26-000084**, filing date and exhibit 99.2 row. | Publication/filing **2026-08-05**. The deck's general June-quarter basis does not replace slide 17's specific month. |
| Construction registration | [TDLR TABS2025012175](https://www.tdlr.texas.gov/TABS/Search/Print/TABS2025012175), PROJECT section: Helios Light Speed, facility Helios, 984 County Road 112, Afton, Dickens County; registered 136,057 ft² data center and 11,400 ft² water-treatment building. | Registration **2025-02-18**; scheduled completion **2026-06-30**, not commissioning evidence. Its postal code is **79920**, retained as reported. |
| Permit application | [TCEQ PI-1S, dID 8718222](https://records.tceq.texas.gov/cs/idcplg?IdcService=TCEQ_EXTERNAL_SEARCH_GET_FILE&Rendition=Web&dID=8718222), PDF pp. **1–2**, registrant/facility and location; p. **7**, signature date. Galaxy Helios I LLC; RN111537775; the same street/Afton/Dickens address, postal code **79220**. | Signature **2025-01-30**. Keep this source's postal code separate from TDLR's discrepancy. |
| Permit review | [TCEQ technical review, dID 8711478](https://records.tceq.texas.gov/cs/idcplg?IdcService=TCEQ_EXTERNAL_SEARCH_GET_FILE&Rendition=Web&dID=8711478), PDF p. **1**, Project Description, registration 179090/RN111537775. Galaxy Helios I LLC owns/operates the named datacenter; application covers 120 CAT diesel generators, approximately 251 MW for outages. | Received **2025-02-06**; reviewer **2025-03-06**, manager **2025-03-07**, p. 2. Authorization/review is different from verified installed count, normal grid supply and IT load. |
| Community map | [Original bounded OSM map request](https://api.openstreetmap.org/api/0.6/map?bbox=-100.9,33.75,-100.83,33.8), corresponding native ways and revisions below. The original XML contains independent tags, geometry, node references and edit timestamps. | Snapshot **2026-10-11T17:04:49.964903+00:00**. An edit timestamp is not a construction, acquisition or energization date. |

NAIP is georeferenced imagery distributed by USGS; its archive description
documents the public-domain source and orthorectified product. This does not make
Atlas's manually traced roof a land survey. The repository crop is
`data/campus/helios-naip-20220905.jpg`, SHA-256
`ee45886aac8a91469f73e8dc1fee9e2b6d2cdc92befa723a41cc24c5d23154e7`;
the interpretation is `helios-naip2022-roof-01` in `data/campus/scenes.json`.
[USGS NAIP archive](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-aerial-photography-national-agriculture-imagery-program-naip),
published 6 July 2018, product description and Sources/Usage.

The operator slide's original raster was inspected privately and is not included
in this note or a public asset. Its existing private source copy is 136,755 bytes,
SHA-256 `75fc22fa7e7536ada7a8f56d06449525271d092df387dac431bd1787c9b303d9`;
the filing index identifies `exhibit992-q22026overvie017.jpg`. Link to the
publisher. The presentation carries redistribution restrictions on slide 2.
[Galaxy exhibit](https://www.sec.gov/Archives/edgar/data/1859392/000185939226000084/exhibit992-q22026overvie.htm),
slides 2 and 17; [graphic metadata](https://www.sec.gov/Archives/edgar/data/1859392/000185939226000084/0001859392-26-000084-index.htm), sequence 24.

## Roof identity review

**Reviewed correspondence, suitable for attributed publication:** the historical
roof corresponds to the long building indicated by callout 3 in the operator
illustration. The match uses the elongated east–west roof, equipment parallel to
both long sides, a station immediately beyond the west end, and the access-road
turn and water/utility area beyond the east end. In our inferred orientation of
the oblique view, north lies to the right and west lies toward the background. These
landmark relationships agree with the georeferenced NAIP crop and the native
station positions; this is stronger than a name or nearest-point match.
Basis: [NAIP raster 190775](https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/query?f=json&where=OBJECTID%3D190775&outFields=OBJECTID%2CName%2CYear%2Cacquisition_date&returnGeometry=false)
and [operator illustration, slide 17, callouts 1–5](https://www.sec.gov/Archives/edgar/data/1859392/000185939226000084/exhibit992-q22026overvie.htm).

The interpretation is **visual identity**, not photogrammetric registration.
Equipment yards changed between the observations; oblique perspective, parallax
and unknown building height prevent a claim of exact common boundaries. Keep the
2022 geometry and its approximate image-derived center
`33.7744161, -100.8690495`. The aerial does not give a survey identifier that binds
that polygon to a lease schedule, data-hall schedule or building permit plan.

Historical campus use has independent first-party support: its electrical EPC
contractor described the Argo bitcoin-mining facility and May 2022 energization.
Galaxy's later financing release describes retrofit and expansion for AI/HPC.
This supports a dated use transition at the campus; avoid importing the older
mining project's phase numbering into the later AI phase model.
[Saber Power, 11 May 2022](https://saberpower.com/saber-power-helps-build-helios-argo-blockchains-texas-bitcoin-mine%EF%BF%BC/),
opening project description and energization paragraph;
[Galaxy financing, 15 August 2025](https://www.galaxy.com/newsroom/galaxy-closes-helios-project-financing),
paragraph beginning with the debt facility's retrofit purpose.

**Unresolved:** the TDLR registered floor area cannot yet be allocated to this
roof. Matching campus address and roughly compatible size are insufficient to
identify a registered floor plan, extension or gross-area boundary. Keep the
registered areas as project evidence. The traced roof is not IT white space or
floor area; its polygon must not be adjusted to reproduce a registered number.
This is a review limitation of the [TDLR PROJECT/Scope of Work fields](https://www.tdlr.texas.gov/TABS/Search/Print/TABS2025012175)
and image interpretation, not an asserted disagreement between measurements.

The reference's Building A/B/C/D labels are not accepted physical identities.
Equipment arrays have their own roles; additional geometry requires independent
allowed source derivation and precision review. This decision approves no new
yard, water, building or parcel polygon.

## Registry identity is corroboration, not a roof location

The official EPA ECHO feature service was queried for exactly three registry IDs.
Its ArcGIS item is owned by **OECA_EPA**, item
`ce5d77fa20d0478882db3f7f589c1906`. Locator: each returned feature's attributes
`registry_id`, `fac_name`, address, latitude/longitude, collection method and
accuracy field. Retrieval is 11 October 2026; the response does not provide an
individual facility observation date.
[EPA item metadata](https://www.arcgis.com/sharing/rest/content/items/ce5d77fa20d0478882db3f7f589c1906?f=json),
[bounded EPA query](https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/ECHO_All_Media_Facilities/FeatureServer/0/query?f=json&where=registry_id+IN+%28%27110071953658%27%2C%27110071142021%27%2C%27110072200020%27%29&outFields=registry_id%2Cfac_name%2Cfac_street%2Cfac_city%2Cfac_state%2Cfac_zip%2Cfac_lat%2Cfac_long%2Cfac_collection_method%2Cfac_accuracy_meters&returnGeometry=false&resultRecordCount=3).

| Registry ID | Returned identity/location metadata | Review implication |
|---|---|---|
| `110071953658` | GALAXY HELIOS; 984 County Road 112, Afton, TX 79220; `33.78026,-100.85931`; address matching/house number; accuracy field 50 m. | Identity/address corroboration. The coordinate is about **1,110 m** from the interpreted roof center; the nominal accuracy field is not evidence of 50 m roof-level accuracy. |
| `110071142021` | ARGO DATA CENTER; southwest of CR 112/CR 131, Afton, TX 79220; `33.774823,-100.868967`; method unset; accuracy field 17,483 m. | Supports legacy locality/name. The point is about **46 m** from the interpreted center but the accuracy field is coarse. Proximity does not make it a surveyed center. |
| `110072200020` | HEL03; southeast of CR 112/CR 131, Afton, TX 79220; `33.776622,-100.859881`; method unset; accuracy field 17,483 m. | Unresolved record. A short registry name is insufficient to identify an additional physical building or Phase III. |

Distances above are **Atlas-derived** spherical center-to-point distances using
the returned coordinates and the existing interpreted roof center, rounded to
meters; they are not EPA measurements or evidence of geodetic accuracy. Keep
the archival project anchor, registry points and reviewed image anchor as separate
coordinate roles. Preserve each registry's original postal code and method.

## Utility-object correspondence decisions

The native-source column is a statement about the captured OSM database,
not certification by a utility. The reviewed-source column is a separate visual
or identity interpretation. Retain its source, locator, review date and confidence
without adding the reviewed attributes to `tags`.

| Native object and captured revision | Native source facts | Reviewed correspondence and publication boundary |
|---|---|---|
| [way 1130569621](https://www.openstreetmap.org/way/1130569621/history), version **2**, edited **2025-03-09T00:44:58Z** | Fenced industrial substation, `voltage=345000`; no name/operator tag. Bounds `[-100.8725131,33.7741574,-100.8713057,33.7760388]`. | **Accept an approximate visual match** to the on-site station beyond the roof's west end. Its relative position, compound layout and nearby transmission/equipment setting agree across the licensed historic image and later illustration. Operator-reported ownership and transformer scope may appear in a separately cited review section; no legal-title, energized transformer count or power delivered to this roof is established. |
| [way 453589317](https://www.openstreetmap.org/way/453589317/history), version **2**, edited **2017-06-04T18:54:02Z** | Cottonwood Substation; native WETT operator string; transmission substation; `voltage=345000`. Bounds `[-100.878323,33.7773185,-100.8749799,33.7792625]`. | **Accept identity correspondence** using native name/operator plus the large compound northwest of the roof in the later view. The operator illustration groups the two regional stations under callout 6 rather than individually geocoding them. This is an attributed identity match, not a validated enclosure boundary or current service schedule. |
| [way 1490401522](https://www.openstreetmap.org/way/1490401522/history), version **1**, edited **2026-03-19T00:01:03Z** | Pitchfork Switchyard, `power=substation`, `construction=yes`; no native voltage/operator tag. Bounds `[-100.8802307,33.7735451,-100.876859,33.7763389]`. | **Accept a reviewed named-site correspondence**, with lower precision than a surveyed match: name, developing compound west/southwest of Cottonwood, and the operator's paired regional-site identification agree. Separately sourced voltage/owner may be shown as reported review facts. Keep native construction tagging and its date; neither a photograph nor the source edit proves the station was energized. |
| [way 1490401526](https://www.openstreetmap.org/way/1490401526/history) and [way 1490401527](https://www.openstreetmap.org/way/1490401527/history), version **1**, edited **2026-03-19T00:01:03Z** | Other generation substations, tagged operators Engie North America and Burksol, LLC. | **No Helios ownership/service match.** Do not propagate the operator's claims to other nearby compounds. |

Review basis for the first three matches:
[USGS NAIP raster 190775](https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/query?f=json&where=OBJECTID%3D190775&outFields=OBJECTID%2CName%2CYear%2Cacquisition_date&returnGeometry=false),
[original OSM snapshot](https://api.openstreetmap.org/api/0.6/map?bbox=-100.9,33.75,-100.83,33.8)
and [Galaxy exhibit, slide 17, callouts 1 and 6](https://www.sec.gov/Archives/edgar/data/1859392/000185939226000084/exhibit992-q22026overvie.htm),
reviewed 11 October 2026. These are publishable **reviewed correspondences** if the
UI carries their interpretation status; they are not authoritative utility GIS.
The repository's NAIP crop directly supports the roof/on-site-station setting;
the two regional compounds are outside that crop. Their correspondences rely on
native names/roles and relative placement in the later operator view, not a claim
that their complete compounds were inspected in the displayed 2022 image.

The OSM snapshot also has 33 power-line ways, including internal busbars and
regional lines. [Way 1365644091](https://www.openstreetmap.org/way/1365644091/history),
version 2, edited 19 March 2026, has a native 345,000 V tag and endpoints in the
on-site and Cottonwood compounds. This is a **candidate community-mapped route**,
not sufficient to publish an exact utility circuit identity, owner, service
capacity, redundancy or current energized connection. Do not give internal
busbars the station's transformer MW scope. Both original full coordinates and
bounded display clipping remain separate.

A first-party campus relationship is supported independently of native geometry:
Galaxy reports a service agreement with AEP Texas for its additional approved
capacity and identifies WETT as the transmission interconnection provider. Publish
these as dated campus/provider relationships, without assigning them to an
unidentified native line.
[Galaxy SEC exhibit 99.1, 15 January 2026](https://www.sec.gov/Archives/edgar/data/1859392/000185939226000005/heliosercotapproval_1x15.htm),
opening announcement and following service-provider paragraph.

Two additional primary documents are useful **leads requiring direct document
review**, not accepted new circuit claims from this run:

- [PUCT docket 55029, item 1](https://interchange.puc.texas.gov/Documents/55029_1_1296831.PDF): indexed text from WETT's L. Wayne Morton testimony, dated **22 May 2023**, printed p. **10**, Helios project row, describes a Cottonwood-to-AEP Helios metering interconnection and a 0.5-mile 345 kV line. It predates the AI conversion. The whole document and exact geometry were not retrieved here.
- [PUCT docket 55999, item 112](https://interchange.puc.texas.gov/Documents/55999_112_1485028.PDF): indexed text includes WETT's Pitchfork proposal and **Attachment C**, ERCOT acceptance letter dated **24 March 2025**, filed **1 April 2025**. It concerns proposed station/line additions; it is not an energization certificate or native-object crosswalk.

Direct document access returned 403 (the web fetch reported 402/403). No access
restriction was bypassed and no bulk utility archive was downloaded. Search
index text served from those primary document URLs establishes the leads but is
insufficient for exact circuit mapping or acceptance of the unreviewed attachments.

## Phase, IT and scope decision

[Galaxy's 6 July 2026 delivery release](https://www.galaxy.com/newsroom/galaxy-completes-phase-i-of-its-helios-data-center-campus),
delivery/development paragraphs, reports Phase I's **133 MW critical IT** and
approximately **200 MW gross**, delivered to CoreWeave, with rent beginning in
Q2 2026. It reports Phase II at **260 MW critical IT** and the combined three
phases at **526 MW critical IT / 800 MW gross**. These are dated phase/contract
scopes, not measured consumption or individual roof allocations.

[Galaxy's 5 August 2026 results](https://galaxydigital.gcs-web.com/news-releases/news-release-details/galaxy-announces-second-quarter-2026-financial-results),
**Helios Data Center Campus** bullet list, confirms Phase I delivery and describes
Phase II construction with data-hall deliveries expected from **Q2 2027**.
That later schedule is more specific than the July release's H1 2027 outlook.
Preserve both dated disclosures and reconcile the accepted schedule through the
normal evidence review; this doc-only decision does not silently update a claim.

The quantity from the station callout is a **transformer scope across phases**.
Do not convert it into building IT load, a phase-specific connection rating or
simultaneously available delivered power. Its publisher uses MW; do not silently
rewrite that unit as MVA or infer power factor. A broad approval envelope is a
different quantity from both the leased phases and a physical feature's load.

No reviewed source in this set supplies a building-number/lease exhibit, hall
allocation, electrical one-line or measured load schedule binding the historical
roof's ID to all of a phase's IT quantity. Neither similarly sized registered
floor area, a single visible roof nor the phase-captioned image supplies that
missing allocation. The inspector can link to the phase disclosure as related
evidence while its main physical-feature quantity remains unallocated.

## Recommended publication record and unresolved work

For the existing roof, retain original geometry/provenance and add only a reviewed
identity/use record with `reviewed_at=2026-10-11`, explicit visual-match method,
operator source/slide locator, source caption month, filing date, and limitations.
Use a name such as **Long data-center roof — 2022 geometry**. A separate description
can state that its later use was reviewed from the operator depiction, as of that
depiction's caption month; this does not assert current October operations.

For native stations, retain the full original tags and object/version metadata.
Separate reviewed name/role/owner/voltage assertions from native attributes.
Source links and exports must disclose both dates and interpretation status. A
native absent operator tag means **not tagged in this snapshot**, not **owner
unknown despite all reviewed evidence**. Conversely, a source that discusses a
campus does not automatically apply to every nearby object.

Acquisition/review still needed:

1. A permitted current nadir image or official site plan with datum, date and geometry review; the USGS query performed here is service-specific.
2. Exact physical building/hall identifiers and documentary phase/IT allocations before assigning them to geometry.
3. A directly reviewed utility source with a geospatial/circuit crosswalk and dated energization evidence before upgrading candidate mapped lines.
4. Independently verified current equipment, water, building and parcel inventory; registry records alone do not supply it.
5. Reconciliation of the TDLR postal discrepancy, floor-area scopes and later phase schedule as source-specific evidence changes, without overwriting historical statements.

The original OSM XML is 580,008 bytes, SHA-256
`33e602ca7769b6c4ff4f02150f09263567256f0c2e0ae73e8b9b51646b4ba93b`.
Native geometry remains ODbL-1.0 with **© OpenStreetMap contributors** attribution.
[OSM copyright/license](https://www.openstreetmap.org/copyright), licensing and
attribution sections, accessed 11 October 2026. This note introduces no source
image redistribution or derivative geometry. Live bounded EPA/USGS query results
were saved privately for reproducibility; no browser, build, database write,
checkout change or application-data mutation was performed for this research.
