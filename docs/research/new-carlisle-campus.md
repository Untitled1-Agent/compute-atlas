# Source-backed New Carlisle campus imagery footprint

Decision for [Research ticket #37](https://github.com/Untitled1-Agent/compute-atlas/issues/37). This refines the imagery-source decision in [#35](https://github.com/Untitled1-Agent/compute-atlas/issues/35). Research used official county, state planning, regulatory and GIS metadata. No aerial rasters were acquired or visually assessed in this task.

## Decision

Use **two named AWS components**, rather than the city anchor or one continuous campus polygon: **Edison Road / IEC-2** and **State Road 2 / IEC-3**. Acquire the bounded Edison image first as the selected campus view; retain SR2 as a separately named, bounded context image. Treat both as **2025 historical imagery**, with the exact source date precision below. Parent visual review must establish which buildings and construction states the derivatives actually show before UI release.

Reject **OBJECTID 2386 / `in2025_11122337_3in`** as an AWS hero. Its WGS84 footprint is approximately west −86.46027, south 41.66281, east −86.45565, north 41.66627: east of the Strawberry Road campus boundary, whose official centerline is near longitude −86.46244. It is a useful catalog/acquisition example from #35, not a verified image of AWS. The existing region anchor around longitude −86.51, latitude 41.70 is likewise not the campus footprint. [Official imagery catalog record](https://di-ingov.img.arcgis.com/arcgis/rest/services/DynamicWebMercator/Indiana_Current_Imagery/ImageServer/query?f=json&objectIds=2386&outFields=OBJECTID%2CName&returnGeometry=true&outSR=4326), [county-origin road record](https://gisdata.in.gov/server/rest/services/Hosted/Road_Centerlines_of_Indiana_2025/FeatureServer/0/query?f=json&objectIds=527452&outFields=objectid%2Cst_name%2Cnguid%2Csource_originator&returnGeometry=true&outSR=4326).

## Identity and extent evidence

The [IEDC announcement of 25 April 2024](https://www.iedc.in.gov/events/news/details/2024/04/25/gov.-holcomb-announces-amazon-web-services-plans-to-invest-11b-to-create-a-new-data-center-campus-in-northern-indiana) places the AWS development in the Indiana Enterprise Center near New Carlisle; it supplies no precise campus geometry.

**Edison / IEC-2:** IDEM's source summary identifies Amazon Data Services at **31100 Edison Road**, Part 70 source **T141-47750-00642**. Its draft significant modification retains that source and address; locate **Section A.1, permit page 5 of 47**. IDHS project application **SBC 446649, filed 14 June 2024**, names **IEC-2 – Building C**, the same address and Larrison Drive as the closest intersecting road. These sources establish site identity, not visible roof outlines or commissioning. [IDEM source document](https://ecm.idem.in.gov/cs/idcplg?IdcService=GET_FILE&dDocName=83835924&dID=83831881), [IDHS construction application](https://oas.dhs.in.gov/reports/rwservlet?dfbsepnpdf=&p_form_id=1128429&report=plan_application_information.rdf). The IDEM endpoint failed direct retrieval during this task; the quoted locator and address were read in the indexed primary-document text, not a downloaded full permit or site map.

The county's [IEC Site 2 page](https://www.stjoepros.org/2191/IEC-Site-2), under **IEC Site 2**, describes a **195-acre development area southwest of Edison Road and Larrison Boulevard**. Its linked [one-page boundary map](https://www.stjoepros.org/DocumentCenter/View/55145/IEC-Site-2) and [one-page parcel information map](https://www.stjoepros.org/DocumentCenter/View/55146/IEC-Site-2---Parcel-Map) are historical planning locators, not a verified current AWS boundary. The county-commissioned [Orbis review, 16 February 2022](https://www.sjcparks.org/DocumentCenter/View/55165/Cultural-Resources-Desktop-Review---IEC-Site-2---Orbis---02-16-22), **PDF page 2, Introduction**, places that area south of Edison, mostly between Elderberry and Larrison. Do not equate all of that old development area with Amazon-owned or occupied land.

**SR2 / IEC-3:** IDEM identifies another Amazon source at **31100 State Road Highway 2**, proposed Part 70 source **T141-48298-00650**. IDHS names **IEC-3 – Buildings 1 through 9** at **31100 State Road 2 Highway**, with Amazon Data Services as applicant; locate **Owner / Applicant Information** and **Project Information**. [IDEM notice](https://ecm.idem.in.gov/cs/idcplg?IdcService=GET_FILE&allowInterrupt=1&dDocName=83762338&dID=83758295), [IDHS project record](https://oas.dhs.in.gov/reports/rwservlet?dfbsepnhtml=&p_var_id=24472&report=variance_view_application.rdf). Permit applications and building labels do not establish nine completed or operational buildings. The IDHS record also contains an inconsistent city-state abbreviation; use the corroborated St. Joseph County / Indiana permit identity, not that field alone.

County [Redevelopment Commission minutes, 9 November 2023](https://www.sjcparks.org/AgendaCenter/ViewFile/Minutes/_11092023-1809), **PDF pages 1–2, resolutions 2023-16 and 2023-17; audio marker 0:03:47**, link Razor 5 development agreements to the Edison/Larrison southwest corner and a separate **640-acre planned area south of SR2, west of Strawberry Road, east of the Huckleberry Ditch / Navistar boundary and north of Warden Road**. This is a predevelopment planning box, not proof that every acre belongs to AWS today.

### County-origin parcel records corroborate the addresses

The state 2025 parcel API supplies county-origin records with the exact two addresses. Use **county_fips `18141`**, not `141`. It contains no ownership field. Native county IDs are more meaningful identities than mutable service OBJECTIDs. The same Edison county ID has **two disjoint feature records**; preserve both instead of silently choosing one.

| Component / source OBJECTID | County parcel ID; state parcel ID | Returned WGS84 envelope [west, south, east, north] |
| --- | --- | --- |
| Edison main, **3684096** | `71-06-01-200-005.000-017`; `710601200005000017` | `[-86.469658066, 41.687581270, -86.463003796, 41.693883235]` |
| Edison separate south part, **3716735** | Same county and state ID | `[-86.467154577, 41.684435811, -86.462401514, 41.686590848]` |
| SR2, **3684094** | `71-06-12-400-001.000-017`; `710612400001000017` | `[-86.482011894, 41.657484007, -86.462303979, 41.671672972]` |

[Reproducible native parcel-record query](https://gisdata.in.gov/server/rest/services/Hosted/Parcel_Boundaries_of_Indiana_2025/FeatureServer/0/query?f=json&objectIds=3684094%2C3684096%2C3716735&outFields=objectid%2Cstate_parcel_id%2Cparcel_id%2Cprop_add%2Ccounty_fips%2Csource_originator%2Cloaddate&returnGeometry=false).

All three records have `source_originator = St. Joseph County` and `loaddate = 1756252800000` (**27 August 2025**). Envelopes above are derived from returned rings, not official survey bounds. The Edison main ring is L-shaped and the SR2 ring has a northeast cutout: drawing these envelopes as owned-land polygons would overclaim. Address matching supports campus-location review; it does not prove the complete campus perimeter. A context query also returns neighboring parcels with other addresses, so the full image crop must remain **campus context**, not an AWS ownership overlay.

Useful derived map focus points, rounded to five decimals, are **Edison main −86.46704, 41.68996** and **SR2 −86.47307, 41.66408**. These are planar centroids calculated from WGS84 parcel rings, **not surveyed facility or building positions**. Keep any previous region point as a region reference and label any new map focus with its derivation.

### Parcel rights and status

The [official IndianaMap item](https://www.arcgis.com/sharing/rest/content/items/f38abeb0f923447485572e0207660c2d?f=pjson), fields **owner, access, description, licenseInfo**, is public and owned by `IndianaMap`. Its terms request but do not require Indiana GIS Data Harvest credit, disclaim survey use and state that no spatial accuracy standard is enforced. The [service](https://gisdata.in.gov/server/rest/services/Hosted/Parcel_Boundaries_of_Indiana_2025/FeatureServer?f=pjson) offers `Query,Extract`. Neither response explicitly marks parcel data CC0/public-domain or states a standalone redistribution license. **For this implementation, cite the IDs, addresses and factual extents; do not bundle complete parcel geometry as CC0.** This is a conservative reuse decision, not a finding that the public data cannot be reused.

There is a metadata inconsistency: the item says parcel release **7 November 2025**; the service description is generic administrative-boundary wording with **1 December 2025**. Preserve the item identity and returned record vintage; do not treat either release date as a survey or campus construction date.

## Exact 2025 imagery selection

The [Current Imagery ImageServer](https://di-ingov.img.arcgis.com/arcgis/rest/services/DynamicWebMercator/Indiana_Current_Imagery/ImageServer?f=pjson), **copyrightText**, explicitly grants **CC0** access. The matching [2025 EAST Tier 1 3-inch project XML](https://gisimageryingov.s3.us-east-2.amazonaws.com/imagerymetadata/statewide/2025/IN_2025_Statewide_EAST_Tier1_Project_Level_3inch.xml), **idinfo/timeperd/timeinfo/rngdates** and **accconst/useconst**, records acquisition **8 March–7 May 2025**, publication **26 September 2025**, public-domain status and no distribution restrictions. Its abstract lists St. Joseph in the **Indiana State Plane East**, **EPSG:6459**, 0.25-foot imagery group. Prefer this matching EAST metadata over the WEST date range in the earlier exploratory note.

The source is nominal **3-inch / 0.25-foot, four-band** imagery; metadata reports a tested **7.5 cm RMSEH horizontal accuracy class** for the product. That is not a guarantee for manually digitized roofs or displayed export pixels. Tile `Image_Year`, `County` and `Pixel_Size` attributes are null in these query results; infer the year/group from native names and project metadata, and preserve the nulls in raw records. Service geometries are returned in **EPSG:4326**; exports below use **EPSG:3857**. Do not treat the printed decimal count as coordinate accuracy.

### Edison context: 16 pinned tiles

Requested WGS84 bounds **`[-86.4702, 41.6838, -86.4598, 41.6945]`**, **1200 × 1600** pixels, maximum derivative download **2,000,000 bytes**. This includes both address-associated parcel components and road landmarks. The crop is context; not all land inside it has verified AWS identity.

| Native OBJECTID | Native Name |
| --- | --- |
| 1450 | `in2025_10752345_3in` |
| 1451 | `in2025_10752346_3in` |
| 1452 | `in2025_10752347_3in` |
| 1453 | `in2025_10752348_3in` |
| 1764 | `in2025_10872345_3in` |
| 1765 | `in2025_10872346_3in` |
| 1766 | `in2025_10872347_3in` |
| 1767 | `in2025_10872348_3in` |
| 2078 | `in2025_11002345_3in` |
| 2079 | `in2025_11002346_3in` |
| 2080 | `in2025_11002347_3in` |
| 2081 | `in2025_11002348_3in` |
| 2392 | `in2025_11122345_3in` |
| 2393 | `in2025_11122346_3in` |
| 2394 | `in2025_11122347_3in` |
| 2395 | `in2025_11122348_3in` |

The seven catalog footprints directly intersecting the two Edison parcel rings are **1764, 1765, 1766, 1767, 2078, 2079, 2080**. The other nine are needed to cover the rectangular context crop; they must not inherit AWS ownership just because they are included in the raster. [Catalog query for the 16 source records](https://di-ingov.img.arcgis.com/arcgis/rest/services/DynamicWebMercator/Indiana_Current_Imagery/ImageServer/query?f=json&objectIds=1450%2C1451%2C1452%2C1453%2C1764%2C1765%2C1766%2C1767%2C2078%2C2079%2C2080%2C2081%2C2392%2C2393%2C2394%2C2395&outFields=OBJECTID%2CName%2CCategory&returnGeometry=true&outSR=4326).

### SR2 context: 25 pinned tiles

Requested WGS84 bounds **`[-86.4828, 41.6569, -86.4616, 41.6726]`**, **1200 × 1200** pixels, maximum derivative download **2,000,000 bytes**. This shows the addressed parcel with SR2 and Strawberry context.

| Native OBJECTID | Native Name |
| --- | --- |
| 814 | `in2025_10502335_3in` |
| 815 | `in2025_10502336_3in` |
| 816 | `in2025_10502337_3in` |
| 817 | `in2025_10502338_3in` |
| 818 | `in2025_10502340_3in` |
| 1128 | `in2025_10622335_3in` |
| 1129 | `in2025_10622336_3in` |
| 1130 | `in2025_10622337_3in` |
| 1131 | `in2025_10622338_3in` |
| 1132 | `in2025_10622340_3in` |
| 1442 | `in2025_10752335_3in` |
| 1443 | `in2025_10752336_3in` |
| 1444 | `in2025_10752337_3in` |
| 1445 | `in2025_10752338_3in` |
| 1446 | `in2025_10752340_3in` |
| 1756 | `in2025_10872335_3in` |
| 1757 | `in2025_10872336_3in` |
| 1758 | `in2025_10872337_3in` |
| 1759 | `in2025_10872338_3in` |
| 1760 | `in2025_10872340_3in` |
| 2070 | `in2025_11002335_3in` |
| 2071 | `in2025_11002336_3in` |
| 2072 | `in2025_11002337_3in` |
| 2073 | `in2025_11002338_3in` |
| 2074 | `in2025_11002340_3in` |

Twenty-three footprints intersect the SR2 parcel polygon; **2073 and 2074** cover the context crop's northeast corner outside that address-associated parcel. They are not evidence of additional AWS land. [Catalog query endpoint](https://di-ingov.img.arcgis.com/arcgis/rest/services/DynamicWebMercator/Indiana_Current_Imagery/ImageServer/query?f=json&objectIds=814%2C815%2C816%2C817%2C818%2C1128%2C1129%2C1130%2C1131%2C1132%2C1442%2C1443%2C1444%2C1445%2C1446%2C1756%2C1757%2C1758%2C1759%2C1760%2C2070%2C2071%2C2072%2C2073%2C2074&outFields=OBJECTID%2CName%2CCategory&returnGeometry=true&outSR=4326).

### Exact date precision

The official [Photo Centers service, layer 41](https://gisdata.in.gov/server/rest/services/Hosted/Indiana_Imagery_Photo_Centers_2021_to_2024/FeatureServer/41?f=pjson) is **Photo Centers 2025 (3 in)** despite the parent service's old 2021–2024 name. The [official photo-center item](https://www.arcgis.com/sharing/rest/content/items/b462ca68cae14904a524754b36ea2540?f=pjson), **licenseInfo**, separately states CC0. Within the SR2 parcel, it returns:

| OBJECTID | Native frame name | WGS84 photo center | Native date |
| --- | --- | --- | --- |
| 3878 | `026_32_183702` | `−86.473309261, 41.668116706` | `1745798400000` = **28 April 2025 UTC** |
| 3879 | `026_33_183659` | `−86.473217178, 41.664557433` | Same |
| 3880 | `026_34_183656` | `−86.473129549, 41.660958016` | Same |

[Reproducible native photo-center query](https://gisdata.in.gov/server/rest/services/Hosted/Indiana_Imagery_Photo_Centers_2021_to_2024/FeatureServer/41/query?f=json&objectIds=3878%2C3879%2C3880&outFields=objectid%2Cframename%2Cdate%2Cmonth&returnGeometry=true&outSR=4326).

No photo-center points intersect the two returned Edison parcel rings. Nearby west flight-line centers **3870–3874** are also dated 28 April, but are **outside** those parcel components and the requested Edison crop. A photo center is a point recorded for a frame, not an orthophoto coverage polygon. No frame-to-tile lineage was returned. **Do not assign 28 April, or nearby east-flight 27 April, as the exact capture day of either locked mosaic.** The honest image date is **2025**, with the EAST project acquisition range available in provenance; the SR2 frame evidence can separately show its exact date and native identity.

## Bounded export recipe for the parent

`/tmp/compute-atlas-design/new-carlisle-campus-export-requests.json` contains the exact unexecuted request URLs, native IDs/names, requested extents, sizes, source-response hashes and byte caps for both components. Example request parameters:

```json
{
  "f": "json",
  "bbox": "-86.4702,41.6838,-86.4598,41.6945",
  "bboxSR": 4326,
  "imageSR": 3857,
  "size": "1200,1600",
  "format": "jpg",
  "compressionQuality": 88,
  "bandIds": "0,1,2",
  "mosaicRule": {
    "mosaicMethod": "esriMosaicLockRaster",
    "lockRasterIds": [1450,1451,1452,1453,1764,1765,1766,1767,2078,2079,2080,2081,2392,2393,2394,2395]
  }
}
```

Send these as URL-encoded query parameters to the ImageServer **`/exportImage`** endpoint. First request `f=json` only; reject API errors, unexpected size/CRS or source drift, then fetch its returned derivative URL one image at a time with a strict byte cap. Store the **returned extent, width, height and spatialReference**, not only the requested bbox, alongside native IDs/names, retrieval timestamp, derivative SHA-256 and source metadata hashes. The service may adjust export aspect/extent; registration must use the returned metadata. [Official ArcGIS exportImage documentation](https://developers.arcgis.com/rest/services-reference/enterprise/export-image/).

Before export, requery the listed OBJECTIDs and require every native Name to match: service OBJECTIDs can change as the rolling catalog is rebuilt. All discovery queries must specify **`spatialRel=esriSpatialRelIntersects`**, `inSR=4326`, `Category=1`, the `in2025%` name filter and a bounded geometry. Never fall back silently to the service's default rolling mosaic.

This method requires no 96 MB source-TIFF download or campus-wide raw raster archive. Keep each derivative below 2 MB and acquire the Edison crop first. The export remains much coarser than the native 3-inch imagery; label native resolution and displayed image resolution separately when needed.

## Remaining review limits

Parent visual verification must compare the returned aerial roads and parcel landmarks, distinguish AWS from neighboring development, and determine whether visible construction supports any status language. This metadata research does not identify individual roof IDs, assign IEC building letters to pixel footprints, establish IT load, energization, fiber service or commissioning, or prove the 2025 addressed parcels form the complete campus. Use the two component identities and explicit date limits; do not turn the historical county development box into an ownership boundary.

All raw responses remain under `/tmp/compute-atlas-design/site-acquisition/`. The doc branch adds only this note; no imagery, parcel rings, source code or production state changes.
