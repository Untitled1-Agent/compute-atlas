# Equinix published location directory

Primary source: https://docs.equinix.com/colocation/availability/

All country-group tables were read and compared with the parsed capture. The captured document lists 253 unique facility codes, with 93 in the publisher's EMEA category, 53 APAC and 107 Americas. Country-group counts are source labels, not harmonized jurisdiction assertions. The table has no publication date. The exact source-body SHA-256 and UTC capture time are recorded in the publication.

Important examples checked: Germany has 13 codes; DU1 has blank service coverage and remains null. France includes PA9x, whose service column says Smart Hands is unavailable; this does not establish operating status or IT MW. UK lists LD4 and LD8; its country label is normalized only for provisional map matching to United Kingdom. Hong Kong entries remain under the publisher's China heading, without silently rewriting the map's distinct country labels.

The parser reads valid optional HTML end tags using html5lib, preserves metro labels and facility type, and normalizes codes to uppercase. Every entry inherits the same exact primary-source URL; no guessed individual facility URLs are produced. No capacities, area conversions, surveyed coordinates or inferred centroid locations are added.

Proposed map matching requires an exact code token, Equinix operator/name and compatible country label. Code suffixes such as FR2.6 are not truncated to FR2. Multiple map candidates are kept rather than silently deduplicated. A matching community outline remains separately sourced under ODbL; the publisher's directory is not relabeled as ODbL data. Entries without matches remain searchable.

Acceptance is identified by `data/catalog/operator-directory-review.json`. This is an explicit reviewer-selected artifact and immutable content identity, not permission for future captures to replace the publication automatically.
