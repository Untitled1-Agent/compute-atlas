# Worldwide exploration and dated physical sources

The six reference compositions now extend into country and local exploration. The searchable destination browser exposes all **122 named countries and territories**; country views group their actual source locations, identify local operators and open a physical source within the selected geography. Selecting Japan from Europe clears the incompatible continent filter. Whole-country US views no longer inherit the curated Midwest/East Coast title. Zooming updates the heading, scale controls, scope rail and breadcrumb together.

| Geographic journey | Actual application capture |
| --- | --- |
| Europe → Germany → local sources | [Germany](review/global-exploration/germany.png) |
| Asia → Japan → local sources | [Japan](review/global-exploration/japan.png) |
| South America → Brazil → local sources | [Brazil](review/global-exploration/brazil.png) |
| Africa → South Africa → local sources | [South Africa](review/global-exploration/south-africa.png) |
| Oceania → Australia → local sources | [Australia](review/global-exploration/australia.png) |
| North America → United States → local sources | [United States](review/global-exploration/united-states.png) |
| Native outline with georeferenced imagery | [Physical source inspection](review/global-exploration/native-aerial.png) |
| Searchable country browser on a phone | [390-pixel browser](review/global-exploration/destinations-390.png) |

Local group labels come from published city fields or a nearby Natural Earth reference place. Their map windows bound the actual records; they do not create administrative boundaries or assert market share. Original source identities and all **6,471 captured records** remain intact, including **345 records without coordinates**. Independent publications can describe the same facility.

The physical archive adds **79 original NAIP exports at published US coordinates**, retaining raster catalogs, acquisition dates, requested and returned geographic extents, reuse terms and image hashes. Two attempted windows remain explicitly unavailable. These are geographic context, separate from the three reviewed campus scenes and nine reviewed roof interpretations. Worldwide physical coverage continues to include **4,394 native facility outlines** and **244,002 captured context objects at 169 anchors in 32 countries**.

The app uses one Mercator ground projection for imagery and native outlines. Plan, 3D and Satellite controls preserve source selection. Unknown heights remain unknown. Physical views can be saved on the research shelf and reopened with their camera and source-version pins. The image library exposes every capture attempt, and downloads reproduce the retained image bytes exactly. Imagery, native catalogs, all captured source publications and original research attachments are embedded in the offline app.

`qa/global-journeys.py` passes **143/143 checks** across the hosted and offline editions. It exercises all six continental journeys, incompatible filter recovery, stale-cluster clearing, semantic zoom, physical bookmarks, image georeferencing, source-version recovery, exact metadata/image exports, library selection and four responsive sizes. The offline run verifies that these journeys require no external requests. Publication tests independently compare every delivered image and metadata file against its hashes, native raster catalog, acquisition dates and returned extent.

[Capture routes and receipt](review/global-exploration/capture-notes.json) · [Six-reference comparison](mockup-ui-review.md) · [Imagery provenance](../../data/maps/anchor-imagery/README.md)
