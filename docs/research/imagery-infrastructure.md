# Redistributable imagery and infrastructure sources

Decision research for [ticket #35](https://github.com/Untitled1-Agent/compute-atlas/issues/35). Checked **2026-10-11 UTC**. This chooses acquisition paths; it does not publish new geometry or certify a site's service, capacity, ownership, construction status, or precise location. Only metadata and small catalog records were read. No raster, national infrastructure archive, or regional fiber database was downloaded.

## Decisions

| Journey | Chosen source and next action | Constraint |
|---|---|---|
| New Carlisle campus imagery | Indiana GIO's **2025, 3-inch, CC0/public-domain** orthoimagery. First review one pinned, small ImageServer export, retaining its returned extent and tile ID. | The 2025 tile exists; exact tile acquisition day and campus-to-roof identity still need review. Nearby photo-center dates are independent evidence. |
| Helios historical campus | Keep the existing **2022-09-05 USDA NAIP** raster as the redistributable baseline. Check USDA/Texas catalogs for a newer specific tile before a second acquisition. | This research does **not** establish that 2022 is the newest imagery anywhere. |
| Helios 2026 operator aerial | Cite the Galaxy SEC exhibit and manually review factual features; continue **link-only** treatment of the operator photograph. | SEC hosting is not a grant to republish an issuer photograph. Oblique photograph geometry is not a survey. |
| Helios local electricity and roads | Keep the existing bounded native OSM capture, with ODbL attribution and dated source inspection/export. | Mapping edit/capture dates do not establish infrastructure commissioning or site service. |
| New Carlisle electricity | Use a small **Indiana government republication of December 2022 HIFLD** geometry as historical regional context after recording the original license chain and native per-feature dates. | The service is incomplete and includes inferred lines. Its 2026 service edit time is not a 2026 infrastructure vintage. |
| Chicago electricity / fiber routes | Keep explicit missing-coverage states until a suitable bounded, licensed source is reviewed. Link to operator evidence where useful. | Do not draw campus connections from a regional network map, FCC availability points, or proximity. |

The preferred New Carlisle imagery service explicitly states CC0. Its project-level metadata independently states that products are public domain and have no distribution restrictions. This is a concrete acquisition path, unlike merely finding a publicly viewable map. [Indiana current ImageServer](https://di-ingov.img.arcgis.com/arcgis/rest/services/DynamicWebMercator/Indiana_Current_Imagery/ImageServer?f=pjson), [2025 project metadata](https://gisimageryingov.s3.us-east-2.amazonaws.com/imagerymetadata/statewide/2025/IN_2025_Statewide_WEST_Tier1_Project_Level_3inch.xml).

## Priority: New Carlisle's licensed 2025 imagery

A point-only query at **longitude -86.459, latitude 41.666** returned the following native record:

- Service: `DynamicWebMercator/Indiana_Current_Imagery/ImageServer`.
- `OBJECTID`: **2386**; `Name`: **in2025_11122337_3in**; `Category`: **1** (primary).
- Native `Image_Year`, `County`, and `Pixel_Size` attributes are **null**. Preserve these nulls; the year/resolution interpretation comes from the tile name and project metadata, not nonexistent populated fields.
- WGS84 service footprint: west **-86.46026733515716**, south **41.66280581849469**, east **-86.45565092884469**, north **41.66626747459178**. Retain the full returned ring rather than replacing it with this enclosing box.
- Native worldfile: pixel spacing **0.25/-0.25 US survey feet**, no rotation; upper-left pixel-center coordinates **111250.125, 2338749.875**. The project documents Indiana State Plane East **EPSG:6459** and West **EPSG:6461**; this tile is in the **SPE** directory.

Sources: [point catalog query](https://di-ingov.img.arcgis.com/arcgis/rest/services/DynamicWebMercator/Indiana_Current_Imagery/ImageServer/query?f=json&geometryType=esriGeometryPoint&geometry=-86.459%2C41.666&inSR=4326&spatialRel=esriSpatialRelIntersects&where=Category%3D1&outFields=OBJECTID%2CName%2CImage_Year%2CCounty%2CPixel_Size&returnGeometry=false&resultRecordCount=5), [full native record and footprint](https://di-ingov.img.arcgis.com/arcgis/rest/services/DynamicWebMercator/Indiana_Current_Imagery/ImageServer/query?f=json&objectIds=2386&outFields=*&returnGeometry=true&outSR=4326), [38-byte worldfile](https://gisimageryingov.s3.us-east-2.amazonaws.com/imageryoptimized/statewide/2025/SPE/03in/in2025_11122337_3in.tfw).

The exact original COG exists at:

`https://gisimageryingov.s3.us-east-2.amazonaws.com/imageryoptimized/statewide/2025/SPE/03in/in2025_11122337_3in.tif`

The bounded S3 listing reports **100,649,438 bytes (96.0 MiB)** and multipart ETag `d432b0ded4e92bd9ebb3a48a80831c48-20`. The ETag is **not a content SHA-256**. Do not download this entire COG onto the shared VPS for a small preview. Prefer a pinned ImageServer export, or a bounded remote COG window reader with a byte budget. [Exact-prefix object index](https://gisimageryingov.s3.us-east-2.amazonaws.com/?list-type=2&max-keys=4&prefix=imageryoptimized%2Fstatewide%2F2025%2FSPE%2F03in%2Fin2025_11122337).

The 2025 project metadata records acquisition **2025-02-28 through 2025-05-09**, publication **2025-09-26**, 0.25-foot pixels, and testing to the **7.5 cm RMSEH horizontal positional accuracy class**. These are project/product specifications, not a guarantee that a manually traced roof has 7.5 cm accuracy or that a roof edge equals a ground footprint. [Project XML](https://gisimageryingov.s3.us-east-2.amazonaws.com/imagerymetadata/statewide/2025/IN_2025_Statewide_WEST_Tier1_Project_Level_3inch.xml).

### Photo dates: exact native frames, no silent tile-date assignment

The official CC0 photo-center service still has `2021_to_2024` in its URL but its current layer **41** is named **Photo Centers 2025 (3in)**. Source naming is therefore insufficient to determine availability. [Service layer list](https://gisdata.in.gov/server/rest/services/Hosted/Indiana_Imagery_Photo_Centers_2021_to_2024/FeatureServer?f=pjson), [photo-center item/license](https://www.arcgis.com/sharing/rest/content/items/b462ca68cae14904a524754b36ea2540?f=pjson).

A tight envelope surrounding the selected tile returned four native photo centers, all with date **2025-04-27** (`1745712000000` milliseconds UTC):

| Object ID | Native frame name | Longitude | Latitude |
|---|---|---|---|
| 4152 | `027_31_174157` | -86.4543600659511 | 41.67182127931484 |
| 4153 | `027_32_174154` | -86.45423509232876 | 41.66825162491743 |
| 4154 | `027_33_174150` | -86.45414235385209 | 41.66468242688874 |
| 4155 | `027_34_174146` | -86.45411362752593 | 41.66111071227029 |

[Bounded native photo-center query](https://gisdata.in.gov/server/rest/services/Hosted/Indiana_Imagery_Photo_Centers_2021_to_2024/FeatureServer/41/query?f=json&geometryType=esriGeometryEnvelope&geometry=-86.465%2C41.658%2C-86.450%2C41.672&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=objectid%2Cframename%2Cdate%2Cmonth&returnGeometry=true&outSR=4326&resultRecordCount=8).

These centers lie immediately east of the tile; a query restricted to the exact tile footprint returned no centers. A wider, earlier envelope also returned frame **3875**, `026_29_183712`, captured **2025-04-28** at **-86.4734636531562, 41.678857381264734**, north/west of this tile. **Neither the nearest frame nor the wider-envelope April 28 date is an established exact acquisition day for the orthomosaic tile.** Keep tile year, project acquisition range, and nearby original-frame dates as three separately scoped fields until a flight-to-tile lineage record establishes the relationship. [Native frame 3875](https://gisdata.in.gov/server/rest/services/Hosted/Indiana_Imagery_Photo_Centers_2021_to_2024/FeatureServer/41/query?f=json&objectIds=3875&outFields=objectid%2Cframename%2Cdate%2Cmonth&returnGeometry=true&outSR=4326).

Indiana's September 28, 2026 announcement says that new 3-inch spring leaf-off imagery and 6-inch 2025 leaf-on imagery are rolling out county by county. St. Joseph is absent from that announcement's released-county lists. An exact-prefix check found **no** `2026/SPE/03in/in2026_11122337` object. These checks do not prove that all newer New Carlisle imagery is unavailable. Recheck the actual tile/county catalog at acquisition time; do not substitute the newest statewide headline for a local capture date. [2026 release announcement](https://www.in.gov/gis/geoinsights/posts/indiana-leafoff-and-leaf-on-imagery-updates/), [exact 2026 prefix check](https://gisimageryingov.s3.us-east-2.amazonaws.com/?list-type=2&max-keys=4&prefix=imageryoptimized%2Fstatewide%2F2026%2FSPE%2F03in%2Fin2026_11122337).

### Bounded derivative acquisition recipe

1. Re-run the native tile/footprint query and preserve the complete JSON, retrieval time, URL, license evidence and SHA-256. Pin tile **2386** using `mosaicRule={"mosaicMethod":"esriMosaicLockRaster","lockRasterIds":[2386]}`; verify the result actually covers the requested bounds.
2. Request **one 1200 × 1200 JPEG** through `/exportImage`, with the footprint-enclosing WGS84 `bbox`, `bboxSR=4326`, `imageSR=3857`, `format=jpg`, `compressionQuality=88`, `bandIds=0,1,2`, the pinned mosaic rule, and `f=json`. This is a suggested next acquisition; it was **not executed** here. Download only its returned image URL after inspecting the metadata, with a small response-size ceiling. Retain the **returned** extent, width, height and spatial reference; do not assume the request bbox survives export resampling unchanged. [ImageServer export endpoint](https://di-ingov.img.arcgis.com/arcgis/rest/services/DynamicWebMercator/Indiana_Current_Imagery/ImageServer/exportImage), [ArcGIS export-image parameter documentation](https://developers.arcgis.com/rest/services-reference/enterprise/export-image/).
3. Show the result as **2025 Indiana orthoimagery** initially. Display nearby original-frame dates only in source evidence. Identify the photographed site against the official county/IEDC record before attaching it to the AWS campus.
4. If this crop misses the full campus, first query the desired **small** campus envelope, inspect adjacent native tile IDs/vintages, and lock those IDs for a second bounded derivative. Do not download the county or silently use the unpinned current mosaic.
5. Trace geometry only after manual visual review. Store image-derived roof polygons as interpretations, with method, source, approximate alignment and review state. Leave floor count, height, ownership, building/phase identity and IT MW unknown unless separate sources establish them.

The Atlas archival New Carlisle anchor **41.7, -86.51** is a city/region anchor, not the tile query point or a surveyed campus coordinate. A proper spatial query there returned **2025 tile 138295 / in2025_97502350_3in** and an overlapping **2023 tile 287946 / in2023_31072350_06**. This reinforces the need for pinned vintage and reviewed site identity. The state announcement places AWS in the Indiana Enterprise Center; county minutes describe the frontage road across the AWS site and Larrison/SR 2 context, but neither establishes that every roof in the proposed crop is an AWS facility. [IEDC campus announcement](https://www.iedc.in.gov/events/news/details/2024/04/25/gov.-holcomb-announces-amazon-web-services-plans-to-invest-11b-to-create-a-new-data-center-campus-in-northern-indiana), [county July 8, 2025 minutes](https://www.sjcindiana.gov/AgendaCenter/ViewFile/Minutes/_07082025-2228).

## Helios imagery: reliable baseline, newer-source search remains open

The existing USGS point query returns native raster **190775**, `m_3310010_sw_14_060_20220905`, acquisition **2022-09-05**, agency **USDA**, resolution **0.6 m**. Texas's official NAIP service directory currently lists flights through **2022**; its separate TOP directory lists older 1996/2008/2009/2015 services. These are catalog observations, not an exhaustive statement about all USDA or other holdings. USGS explicitly provides a route for imagery acquired but not yet available through EarthExplorer. [USGS NAIP ImageServer](https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer), [Texas NAIP directory](https://imagery.geographic.texas.gov/server/rest/services/NAIP?f=pjson), [Texas TOP directory](https://imagery.geographic.texas.gov/server/rest/services/TOP?f=pjson), [USGS NAIP access and accuracy information](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-aerial-photography-national-agriculture-imagery-program-naip).

The Texas Imagery Service offers newer 6-inch imagery but explicitly distinguishes its licensed Hexagon imagery from unrestricted NAIP/TOP. Some licensed subscribers can expose it in public-facing applications; that does not give Atlas permission to self-host its rasters. Cook County's service similarly advertises 2025 imagery, while its 2022 tile-index metadata expressly requires permission for redistribution/network availability. Leave both as license-review candidates, not bundled assets. [Texas imagery terms and public-web-app FAQ](https://geographic.texas.gov/texas-imagery-service), [Cook current imagery metadata](https://gis.cookcountyil.gov/imagery/rest/services/Basemap/CookImagery/ImageServer/info/iteminfo), [Cook 2022 tile-index terms](https://gis.cookcountyil.gov/traditional/rest/services/Ortho_Reference_Tiles/MapServer/0/iteminfo).

The Galaxy July 2026 SEC exhibit identifies a data-center building, chiller/electrical yards, water facilities, Galaxy's 345 kV substation, and WETT's Pitchfork/Cottonwood substations. Its transformer-capacity statement is not building IT MW, and its contiguous controlled acreage is not a georeferenced parcel polygon. Use this to review factual identity and roles while keeping the restricted aerial link-only. [Galaxy exhibit, slide 17](https://www.sec.gov/Archives/edgar/data/1859392/000185939226000084/exhibit992-q22026overvie.htm).

## Electricity geometry and native dates

OSM is a redistributable **ODbL** source with attribution/share-alike obligations; keep original IDs, revisions, mapping edit times, raw tags, complete geometry, bounded display clipping and an export of the derived database. Its API supports small bounded map requests; it is not a production tile backend or a reason to crawl a whole region. The existing Helios source can support dated local context, but not presumed utility connection, current status, survey precision or IT capacity. [OSM license](https://www.openstreetmap.org/copyright), [OSMF attribution guidance](https://osmfoundation.org/wiki/Attribution_Guidelines), [native map API](https://wiki.openstreetmap.org/wiki/API_v0.6#Retrieving_map_data:_GET_/api/0.6/map).

HIFLD's public portal transition is confirmed by DHS's FY2025 report: access moved into secure DHS GII and now requires a government sponsor, login.gov and a data-use agreement. A surviving catalog entry or third-party archive is not a current official feed. The federal catalog's legacy transmission entry declares public access and a government-works license, with a 2022 dataset date. [DHS report](https://www.fgdc.gov/gda/gda-ca-reports/FY25CoveredAgencyReports/FY25DHSGDAReport), [legacy DHS transmission license/catalog](https://catalog.data.gov/dataset/electric-power-transmission-lines).

A practical surviving **government** source is Indiana's [2022 transmission FeatureServer](https://gisdata.in.gov/server/rest/services/Hosted/Electric_Power_Transmission_Lines_2022/FeatureServer/0?f=pjson). Its [original metadata](https://www.arcgis.com/sharing/rest/content/items/9fe5e12fef5f4ee9ab3861237a9012e6/info/metadata/metadata.xml?format=default&output=html) identifies a December 2022 HIFLD update and April 2023 IGIO publication, no access constraints, and a warranty/liability disclaimer. The item does **not** name a separate CC0 license. Preserve that distinction and the federal-origin license evidence when publishing a bounded historical derivative.

A four-record metadata query near New Carlisle demonstrates why source vintage and inference fields must survive normalization:

| HIFLD native ID | Indiana object ID | Voltage tag | Native endpoints | Source date | Validation date | Inferred |
|---|---|---|---|---|---|---|
| 141261 | 5 | 345 kV | OLIVE / REYNOLDS | 2015-04-17 | 2018-02-21 | N |
| 141495 | 12 | 765 kV | COOK / DUMONT | 2016-08-01 | 2016-08-01 | N |
| 143491 | 56 | 138 kV | TAP139932 / OLIVE | 2015-04-08 | 2018-03-01 | Y |
| 145231 | 111 | 138 kV | UNKNOWN129046 / NEW CARLISLE | 2015-06-24 | 2018-03-01 | Y |

These are **source-reported tags**, not our verification of electrical topology or present service. The first owner tag is `NOT AVAILABLE`; preserve it. [Bounded native attribute query](https://gisdata.in.gov/server/rest/services/Hosted/Electric_Power_Transmission_Lines_2022/FeatureServer/0/query?f=json&geometryType=esriGeometryEnvelope&geometry=-86.53%2C41.64%2C-86.40%2C41.73&inSR=4326&outFields=objectid_1%2Cid%2Cowner%2Cvoltage%2Csourcedate%2Cval_date%2Cval_method%2Cinferred%2Csub_1%2Csub_2&returnGeometry=false&resultRecordCount=4).

For independently dated context, AEP's current Olive–Reynolds project page describes a planned 68-mile 345 kV rebuild, Olive Substation near US 20/New Carlisle, and spring 2026 soil-boring work. This does not make an old HIFLD line new or establish AWS service. For Helios native-feature identity review, PUCT filings identify Pitchfork 345 kV Station and describe the station/two 0.5-mile line project on WETT property; review their maps before joining to OSM feature IDs. [AEP project](https://www.aeptransmission.com/indiana/Olive-Reynolds/), [PUCT station attachment](https://interchange.puc.texas.gov/Documents/55999_112_1485028.PDF), [PUCT construction report](https://interchange.puc.texas.gov/Documents/57477_209_1520434.PDF). The PUCT documents were discoverable through primary indexed text, but direct fetch was blocked during this research; full map review remains pending.

## Fiber decision

Keep the physical fiber layer **unavailable** for these journeys until route geometry, redistribution rights, vintage and geographic precision are established. FCC BDC is provider-reported **mass-market service availability at locations**, not physical conduit/cable routes. Fabric access has its own license agreement. Do not convert these points into a fiber network, assign campus connectivity from them, or assume the whole FCC map is a redistributable geometry dataset. [FCC map scope](https://help.bdc.fcc.gov/hc/en-us/articles/13532984820379-What-s-on-the-National-Broadband-Map), [Fabric access process](https://help.bdc.fcc.gov/hc/en-us/articles/8554187214107-Fabric-Challenge-Process).

Zayo and FiberLight publish first-party network maps, but this research found no source record granting redistribution of a precise route dataset for the selected corridors. They can inform source discovery and site-specific inquiries; their marketing maps are not a native survey layer or evidence of an AWS/Helios lateral. INDOT requires precise as-built fiber plans from permittees, demonstrating a possible later documentary source, but the requirement itself does not establish public availability or reuse rights. [Zayo network source](https://www.zayo.com/network/), [FiberLight network source](https://www.fiberlight.com/fiber-network/), [INDOT as-built requirement](https://www.in.gov/indot/doing-business-with-indot/files/Broadband-Permit-Guidelines.pdf).

## Evidence limits and completion criteria

This ticket's source choice can close after review of the choices above. Implementation should retain separate **acquisition time, publication time, source capture time, native edit time, inspection/review time**, and unknown values. A 2025 image does not certify 2026 operations; an old transmission map does not establish campus allocation.

Before the next imagery release: identify the AWS campus within the chosen crop using primary site documents, acquire a bounded pinned derivative, establish and accurately label the available image-date scope, hash image and metadata, manually verify georegistration/roof interpretation, and live-test all affected scales and source/return/export journeys. A full-campus image/building inventory, exact tile day, newer Helios unrestricted high-resolution coverage, Chicago licensed electricity detail, and native licensed fiber geometry remain **open**, not silently satisfied by this research.

Metadata endpoint failures were preserved as uncertainty: USDA's older APFO host reset the connection; USGS NAIPPlus point queries timed out/returned 504; the Texas DataHub frontend returned 403; the 2024 USDA coverage query returned 503. None is evidence that the corresponding data does not exist. Small raw metadata records are retained privately under `/tmp/compute-atlas-design/site-acquisition/`; only this research note is proposed for the repository.
