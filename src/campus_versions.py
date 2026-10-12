"""Exact physical interpretation identity, independent of image-only identity."""
import hashlib,json

def canonical_bytes(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')

def feature_review_hash(scene,feature):
    image=scene['image']
    payload={'schema_version':1,'scene_id':scene['id'],'project_id':scene['project_id'],
             'image':{k:image[k] for k in ['sha256','extent_3857','width','height']},
             'review':scene['review'],
             'feature':{k:v for k,v in feature.items() if k!='review_sha256'}}
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()

def validate_physical_versions(collection):
    ids=set();features=set()
    for scene in collection['scenes']:
        if scene['id'] in ids:raise ValueError('Duplicate physical scene identity')
        ids.add(scene['id'])
        for feature in scene['features']:
            if feature['id'] in features:raise ValueError('Duplicate physical feature identity')
            features.add(feature['id'])
            if feature.get('review_sha256')!=feature_review_hash(scene,feature):
                raise ValueError('Physical geometry/review fingerprint mismatch: '+feature['id'])
    # The allowlist preserves a prior accepted identity; it need not match a later
    # reinterpretation, which intentionally prevents silent image-only migration.
    for item in collection.get('legacy_image_only_versions',[]):
        if any(not isinstance(item.get(k),str) for k in ['scene_id','project_id','feature_id','image_sha256','review_sha256']):
            raise ValueError('Invalid historical migration identity')
