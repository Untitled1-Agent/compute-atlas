# Published-coordinate aerial context

The [manifest](../anchor-imagery.json) indexes 81 United States anchors from the existing global context publication. **79 native NAIP image exports are retained**. Two windows remain explicitly unavailable, with the acquisition failure or insufficient source-image coverage recorded in the manifest. These are bounded geographic windows, not reviewed campus boundaries or a building inventory.

Each `.jpg` is the original response from the USDA NAIP / USGS National Map image service. Each matching `.json` retains the original raster-catalog response, selected raster IDs, export URL and returned extent, capture time, image hash and attribution. The manifest pins both the image and its metadata file. Acquisition dates describe the individual source rasters; missing dates are not synthesized from a capture date. The publisher's public-domain terms are linked from every successful capture.

The exporter requests a 1.8 × 1.35 km ground window at 1024 × 768 pixels, natural color, JPEG quality 68. Older valid responses are retained if a subsequent acquisition fails. Image dimensions, pixel variation and uncovered-pixel fraction are checked before accepting a response. The native server export bytes are never resampled or edited locally. ArcGIS may append metadata after the JPEG end marker; that trailer is retained.

The app projects the returned EPSG:3857 extent and independent source outlines onto the same ground plane. It does not assign source polygons to the coordinate's project, invent building heights, infer operating status, or allocate project power to buildings. Reviewed campus images and roof interpretations remain separately selectable evidence. The complete manifest, native metadata and image downloads work in the standalone edition without network access.

To acquire a new publication explicitly, install Pillow in a development environment and run `python tools/capture_anchor_imagery.py`, then review the returned images and metadata before rebuilding. The normal application build never fetches images or mutates source data.
