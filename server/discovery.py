"""Research leads remain outside site identity and accepted capacity series."""
from datetime import date
import math


def validate_candidate(db, claim):
    measurements=claim.get('candidate_measurements')
    if measurements is None:
        return  # Preserve the native, historical discovery records.
    if not isinstance(measurements,list) or not 1<=len(measurements)<=20:
        raise ValueError('Candidate measurements must be a bounded list')
    if any(claim.get(k) is not None for k in ('latitude','longitude','operating_it_mw')):
        raise ValueError('An unresolved research candidate cannot assert mapped or operating IT values')
    support=claim.get('supporting_source_ids',[])
    if not isinstance(support,list) or len(support)>16 or any(not isinstance(s,str) for s in support):
        raise ValueError('Invalid candidate supporting sources')
    sources={claim['source_id'],*support}
    if any(not db.execute('SELECT 1 FROM sources WHERE id=?',(sid,)).fetchone() for sid in sources):
        raise ValueError('Unknown candidate source')
    keys={'value','unit','boundary','label','source_id','scope','comparison','status','as_of'}
    for row in measurements:
        if not isinstance(row,dict) or set(row)!=keys:
            raise ValueError('Candidate measurement lacks its source, status or native scope')
        value=row['value']
        if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0):
            raise ValueError('Candidate value must be finite, nonnegative or null')
        if row['unit']!='MW' or row['boundary'] not in {'critical_it','gross_facility','secured_power','campus_power','site_power'}:
            raise ValueError('Unsupported candidate power boundary')
        if row['source_id'] not in sources or row['comparison'] not in {'stated','lte'} or row['status'] not in {'planned','disclosed'}:
            raise ValueError('Candidate measurement has an invalid source or state')
        if any(not isinstance(row[k],str) or not row[k].strip() or len(row[k])>500 for k in ('label','scope')):
            raise ValueError('Candidate measurement needs a bounded label and scope')
        if row['as_of'] is not None:
            try: date.fromisoformat(row['as_of'])
            except (TypeError,ValueError): raise ValueError('Invalid candidate reporting date') from None
