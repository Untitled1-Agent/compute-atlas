

## Analyst evidence desk and update notifications

The facility attribute/source cards open a read-only evidence desk with searchable
quantities, attributes, counterparties and earlier revisions. Values retain their
measurement scope, source date, status and inequality. Non-power disclosures such
as PUE and annual kWh are not rounded into whole MW. Cited dossier export includes
source records for both current and superseded claims, separately from archival
estimates and the user's optional private note.

The service browser conditionally checks the publication ETag every five minutes
while visible. A changed *accepted publication* prompts the analyst to apply it;
a new source capture alone cannot change displayed capacity. Applying an update
preserves the selected facility, filters and private notes. Invalid/unavailable
responses keep the last loaded evidence and show a retry notice. The standalone
makes no background requests. The full database decision log remains available
through the read-only history API and durable backup.
