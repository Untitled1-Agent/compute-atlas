# Electricity context for the New Carlisle campus scenes

Decision for [Wayfinder Research #39](https://github.com/Untitled1-Agent/compute-atlas/issues/39). Read with [the campus identity note](new-carlisle-campus.md) and [the earlier source survey](imagery-infrastructure.md). All acquisition was read-only, bounded metadata/native geometry, with a hard **2,000,000-byte cap per response**. No app collection, aerial raster, checkout, production or infrastructure state was changed.

## Recommendation

Prefer **direct native OpenStreetMap geometry under ODbL** for the bounded Edison and SR2 electricity overlays. Publish it as **mapped electricity context, independently dated from the 2025 aerial imagery**. The native API returns line and substation geometry in both selected campus scenes, with exact object IDs, versions, node references, tags and edit timestamps. Preserve the complete raw snapshots, prepare the separately attributable/exportable ODbL derivative, and use bounded display clipping rather than replacing complete source paths with synthetic campus connectors.

For initial campus display, prioritize the **25 source ways** representing **22 lines and three substation outlines** across the two scenes. Keep the 42 SR2 cable ways and electrical point details available in source inventory; do not draw those dense, voltage-untagged underground routes as a verified AWS service diagram. All feature/operator/energization/service confidence remains source-reported or unknown.

Keep Indiana's **2022 HIFLD republication as a historical comparison lead**. It has sparse campus coverage, older feature dates and mixed third-party source attribution. Do not label it CC0, use a 2026 catalog edit date as infrastructure vintage, or deduplicate close parallel features merely because they share an envelope/endpoints.

## Bounded native OSM acquisition and retained files

The exact native requests are:

- [Edison map query](https://api.openstreetmap.org/api/0.6/map?bbox=-86.4702,41.6838,-86.4598,41.6945), WGS84 bounds **`[-86.4702,41.6838,-86.4598,41.6945]`**.
- [SR2 map query](https://api.openstreetmap.org/api/0.6/map?bbox=-86.4828,41.6569,-86.4616,41.6726), WGS84 bounds **`[-86.4828,41.6569,-86.4616,41.6726]`**.

These are snapshots from the native read API, not screenshots or bulk region extracts. A bounding-map response can include complete ways and their nodes outside the requested rectangle. It is therefore essential to retain source geometry and separately clip what the scene draws. Point coordinates use WGS84 longitude/latitude; their decimal precision is not a surveyed positional-accuracy guarantee. [Native API description](https://wiki.openstreetmap.org/wiki/API_v0.6#Retrieving_map_data:_GET_/api/0.6/map).

| Scene | Capture UTC | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| edison | `2026-10-11T21:07:31.128095+00:00` | 156785 | `30b8df9a296f0ed31b82d92935de8f6bae974d49ac09bd4c251b3113d3c81fd7` |
| sr2 | `2026-10-11T21:07:31.462999+00:00` | 300954 | `59fbaa7a177c00be0727a5f44cd2fdc6bc73f20bc7dbf7d737939d6c46aadeb2` |

All files remain in **`/tmp/compute-atlas-design/electricity-acquisition/`**:

| Retained file pattern | Contents |
| --- | --- |
| `edison-osm-native-map.xml`, `sr2-osm-native-map.xml` | Exact unmodified native responses, including complete returned ways/nodes and public source metadata |
| `osm-query-manifest.json` | Request URL, UTC retrieval time, byte count, SHA-256 and response budget |
| `*-osm-power-metadata.json` | Every native `power` element's ID/type/version/changeset/edit time, raw tags and way node references; unnecessary contributor name/UID omitted |
| `*-osm-power-reference.json` | Research reference bundle of every selected power way, its full coordinate path/node refs and every referenced node's ID/version/edit time/tags; **not an app asset** |
| `*-core-way-ids.json` | Core line/substation way identities for later explicit normalization |
| `cross-scene-native-overlap.json` | Full-response shared object IDs and version consistency |

All power-way node references were present in their native response. The reference bundles contain **13 Edison ways / 37 referenced nodes** and **54 SR2 ways / 243 referenced nodes**. They exclude unrelated roads/buildings from the derived bundle without altering their presence in the preserved raw capture.

### Native inventory and operating-status limits

| Native `power` inventory | Edison | SR2 |
| --- | ---: | ---: |
| Line ways | 11 | 11 |
| Substation ways | 2 | 1 |
| Cable ways | 0 | 42 |
| Tower nodes | 14 | 17 |
| Portal nodes | 14 | 16 |
| Switch nodes | 50 | 70 |
| Transformer nodes | 5 | 6 |
| Total selected power elements | 96 | 163 |

Counts describe the bounded API responses, including referenced geometry outside the rectangle; they are not counts of facilities wholly inside the campus or proof of installed equipment. None of the selected power ways has a `status`, `operator` or `name` tag. No power lifecycle tags were found in these responses. Absence of `construction`, `disused` or other lifecycle tags does **not** establish energized status. Preserve untagged status as unknown.

The core ways all carry **2026-01-14T01:29:03Z** last-edit timestamps. Edison core ways are version **1**; SR2 `1463187602/3/4/6/7/8` are version **2**, and `1466907511–7516` are version **1**. The 42 cable ways divide into **14 last edited 2026-06-25T14:52:53Z** and **28 last edited 2026-06-26T13:01:33Z**. Node versions and edit dates vary independently: an unchanged way can reference recently edited nodes. Preserve both levels; a mapping edit is not an infrastructure capture, construction, inspection or energization date.

### Core native identities

The following are exact native way IDs from the linked bounded responses above. For immutable way metadata, native API paths such as [`/way/1466907498/1`](https://api.openstreetmap.org/api/0.6/way/1466907498/1) identify a version. The frozen response also pins the node versions/coordinates needed to reconstruct that captured geometry.

| Scene | Native way ID | Version | `power` | Raw voltage tag |
| --- | --- | ---: | --- | --- |
| edison | `1466907494` | 1 | line | `345000;345000` |
| edison | `1466907495` | 1 | line | `345000` |
| edison | `1466907496` | 1 | line | `345000` |
| edison | `1466907497` | 1 | line | `345000` |
| edison | `1466907498` | 1 | substation | `345000` |
| edison | `1466907499` | 1 | substation | `345000` |
| edison | `1466907500` | 1 | line | `345000` |
| edison | `1466907501` | 1 | line | `345000` |
| edison | `1466907502` | 1 | line | `345000` |
| edison | `1466907503` | 1 | line | `345000` |
| edison | `1466907504` | 1 | line | `345000` |
| edison | `1466907505` | 1 | line | `345000` |
| edison | `1466907506` | 1 | line | `345000;345000` |
| sr2 | `1463187602` | 2 | substation | `345000` |
| sr2 | `1463187603` | 2 | line | `345000` |
| sr2 | `1463187604` | 2 | line | `345000` |
| sr2 | `1463187606` | 2 | line | `345000;345000` |
| sr2 | `1463187607` | 2 | line | `345000` |
| sr2 | `1463187608` | 2 | line | `345000` |
| sr2 | `1466907511` | 1 | line | `345000` |
| sr2 | `1466907512` | 1 | line | `345000` |
| sr2 | `1466907513` | 1 | line | `345000` |
| sr2 | `1466907514` | 1 | line | `345000` |
| sr2 | `1466907515` | 1 | line | `345000` |
| sr2 | `1466907516` | 1 | line | `345000` |

The three substation source envelopes are:

| Native way | Source-reported class | Derived WGS84 envelope [west, south, east, north] |
| --- | --- | --- |
| `1466907498` | `substation=transmission`, `voltage=345000` | `[-86.4668056,41.6878600,-86.4648543,41.6901288]` |
| `1466907499` | `substation=industrial`, `voltage=345000` | `[-86.4646730,41.6879867,-86.4636826,41.6897070]` |
| `1463187602` | `substation=industrial`, `voltage=345000` | `[-86.4724641,41.6653710,-86.4693631,41.6675997]` |

These are useful location checks against the independently addressed campus parcels in #37. They have no native AWS operator/name field and no independently established utility service-point identity. Label them **OSM-mapped transmission/industrial substation**, not **AWS delivery substation**, **AWS energized capacity** or a verified building connection.

OSM uses voltage values in volts. Preserve strings such as **`345000;345000`**, `circuits=2` and `cables=6`; a semicolon voltage list must not be summed into 690 kV or converted into MW. All 42 cable ways have `power=cable`, `location=underground`, `layer=-1` and **no voltage tag**. Neither voltage, circuit count, substation area nor transformer symbols establishes campus IT load or contracted/available capacity.

### Cross-scene overlap and deduplication

The selected power-way sets share **zero way IDs**, and their referenced-node sets share **zero node IDs**. The complete raw responses share exactly **one non-power node, `181656461`**, with matching version; they share no ways or relations. Preserve scene membership, and deduplicate combined primitive records by **type + native ID + version**, never by untyped ID, coordinate proximity or envelope. If a later capture returns a different version for the same primitive, retain that version distinction instead of silently choosing whichever scene loads last. The computed native overlap is retained in `cross-scene-native-overlap.json`.

## Rights and export obligations

OSM's [copyright/license page](https://www.openstreetmap.org/copyright), **OpenStreetMap licensing** and **How to credit OpenStreetMap**, explicitly permits copying, redistribution and adaptation under **ODbL**, with contributor credit and applicable share-alike obligations. The [OSMF attribution guidelines](https://osmfoundation.org/wiki/Attribution_Guidelines) describe map attribution placement. The implementation should retain visible **© OpenStreetMap contributors**, link the license, and expose the separately identified ODbL data/derivative and source provenance through the existing export/source journey. Do not mark these vectors CC0 or combine them into an unlabeled proprietary geometry database. This recommendation uses the explicit license on the selected source; it does not determine every possible legal classification of a later database architecture.

## HIFLD comparison: exact schema, dates and coverage

The surviving official [Indiana layer](https://gisdata.in.gov/server/rest/services/Hosted/Electric_Power_Transmission_Lines_2022/FeatureServer/0?f=pjson) uses **`objectid_1`** as its actual query OBJECTID. It separately exposes `objectid`, HIFLD string `id`, `globalid`, `type`, `status`, `owner`, `source`, `sourcedate`, `val_method`, `val_date`, `voltage`, `volt_class`, `inferred`, `sub_1`, `sub_2` and length fields. The fresh hosted layer returns native geometry in **EPSG:4326**; the older item XML contains a Web Mercator dataset reference. Respect the response CRS rather than assuming the historical metadata CRS is still the hosted service's storage CRS.

Explicit `esriSpatialRelIntersects` ID queries return **two Edison records**, **zero SR2 records**, and **31 records** in the bounded regional box `[-86.53,41.64,-86.40,41.73]`. This is missing source coverage at SR2, not proof of no electricity infrastructure or service. Native query and small comparison responses are retained in the same acquisition directory: `*-transmission-nativeids.json`, `regional-native-attributes.json`, `edison-native-geometry.json`, and `query-manifest.json`.

| Indiana query OBJECTID | Source `objectid`; HIFLD `id`; GlobalID | Source date / imagery-validation date | Source-reported electrical tags |
| --- | --- | --- | --- |
| **915** | `19678`; `102772`; `79bc746b-e6cf-4da5-8c30-4ca42684ad0e` | **2015-04-08 / 2015-09-29** | 345 kV; AC overhead; `IN SERVICE`; `inferred=N`; I&M; OLIVE–DUMONT |
| **1562** | `37402`; `125633`; `156e0eb6-70a6-4c0c-83f5-b6ce49f88007` | **2015-04-17 / 2015-09-29** | Same tag values |

[Reproducible native feature query](https://gisdata.in.gov/server/rest/services/Hosted/Electric_Power_Transmission_Lines_2022/FeatureServer/0/query?f=json&objectIds=915%2C1562&outFields=%2A&returnGeometry=true).

Both full paths have **18 vertices and the same envelope**, but **are not identical geometry**: many corresponding intermediate vertices differ by approximately 10 m, with other offsets near endpoints. This corrects an early research message that called them duplicates based on their envelope/count. Preserve distinct source records; neither collapsing them nor assigning independent circuit identities is justified from envelope equality. Their per-feature `IN SERVICE` value is old source metadata, not present-day energization verification.

The regional query also returns **16 `inferred=Y` records**, **ten `N` records**, and **five `NOT AVAILABLE` records**. Those five have **`voltage=-999999`**, an unavailable sentinel; never display negative kilovolts or treat it as zero. Preserve source `NOT AVAILABLE` owner/endpoints, and distinguish unknown/inferred routes from independently surveyed infrastructure.

The [item XML](https://www.arcgis.com/sharing/rest/content/items/9fe5e12fef5f4ee9ab3861237a9012e6/info/metadata/metadata.xml?format=default&output=html), **dataIdInfo/idPurp**, states **December 2022 HIFLD update / April 2023 IGIO publication**. Hosted **lastEditDate** is **2026-04-19T18:56:17.222Z**; the fresh [IndianaMap item](https://www.arcgis.com/sharing/rest/content/items/9fe5e12fef5f4ee9ab3861237a9012e6?f=pjson) was created **2026-06-01T17:43:02Z**, modified one second later. These hosting/catalog dates do not update the 2015–2022 infrastructure source or validation dates.

The [federal legacy catalog](https://catalog.data.gov/dataset/electric-power-transmission-lines), identifier **MGMT-GMO-HIFLD-847169**, declares public access and a government-works license link; its dataset timestamp is **2022-10-24**, differing from Indiana's described December update. The Indiana item gives an AS-IS disclaimer, not a separate explicit CC0 grant. More concretely, record **915** names **OpenStreetMap** in `source`; record 1562 names imagery and a Purdue report. The [USAGov explanation](https://www.usa.gov/government-copyright), **Restrictions on using U.S. government materials** and **State and local government materials**, warns that federal publication does not make third-party or state/local work a federal government work. Therefore the federal link alone is insufficient to treat this mixed-source republication as unqualified CC0 geometry. Direct OSM is the preferred, explicitly licensed campus geometry; HIFLD remains cited comparison evidence.

## Independent utility evidence does not establish mapped AWS service

I&M's [19 February 2025 announcement](https://www.indianamichiganpower.com/company/news/view?releaseID=10036), **Indiana Michigan Power Receives Order in Large Load Settlement**, names AWS in the tariff settlement and its New Carlisle development. The [IURC order, Cause 46097, approved 19 February 2025](https://secure.in.gov/iurc/files/ord_46097_021925.pdf), documents the tariff proceeding. This supports the utility/customer planning relationship, but does **not** attach either OSM substation, HIFLD OLIVE–DUMONT feature, meter/delivery point or feeder to either campus component. No independently verified **mapped AWS service** is accepted by this decision.

For separately dated regional project context, AEP's [Olive–Reynolds project](https://www.aeptransmission.com/indiana/Olive-Reynolds/), **Project Updates**, describes spring 2026 engineering soil borings for a planned 345-kV rebuild. OLIVE–REYNOLDS is not the OLIVE–DUMONT endpoint pair of the Edison comparison records. Do not attach that project's 2026 update to those geometries or use a proposed rebuild as evidence of campus power availability.

## Implementation acceptance boundary

Normalize only after root reviews these native snapshots. Keep Edison and SR2 scene identities separate; retain complete geometry/provenance, native timestamps, unknown physical capture/status, and a distinct **2025 aerial / 2026-edited vector** explanation. A 2026 mapping edit cannot establish what was present in the 2025 aerial. If a line or substation is not visible in that image, preserve the date difference instead of inventing agreement.

Live visual verification should review registration against the returned imagery extent and source coordinates, select appropriate detail for each scale, and exercise object source/return/export journeys before a merge. This research does not certify observed roofs, utility topology, energization, contracted capacity, IT allocation or AWS service. The source decision is ready to resolve with direct ODbL context geometry; operational and service assertions remain unproven.
