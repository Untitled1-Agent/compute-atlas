import copy
import pytest
from src.campus_versions import feature_review_hash,validate_physical_versions

def collection():
    scene={'id':'test-scene','project_id':'test-project','image':{'sha256':'a'*64,'extent_3857':{'xmin':0,'xmax':1,'ymin':0,'ymax':1},'width':10,'height':10},'review':{'status':'accepted_historical_interpretation','reviewed_by':'test actor'},'features':[{'id':'test-roof','geometry':{'type':'MultiPolygon','coordinates':[[[[0,0],[1,0],[1,1],[0,0]]]]},'height_m':None,'phase_id':None,'it_power_mw':None}]}
    f=scene['features'][0];f['review_sha256']=feature_review_hash(scene,f)
    return {'scenes':[scene],'legacy_image_only_versions':[{'scene_id':scene['id'],'project_id':scene['project_id'],'feature_id':f['id'],'image_sha256':scene['image']['sha256'],'review_sha256':f['review_sha256']}]}

def test_changed_outline_on_same_image_requires_new_fingerprint():
    data=collection();data['scenes'][0]['features'][0]['geometry']['coordinates'][0][0][1][0]=1.01
    with pytest.raises(ValueError,match='fingerprint mismatch'):validate_physical_versions(data)

def test_changed_review_requires_new_fingerprint():
    data=collection();data['scenes'][0]['review']['reviewed_by']='different test actor'
    with pytest.raises(ValueError,match='fingerprint mismatch'):validate_physical_versions(data)

def test_accepted_reinterpretation_does_not_advance_legacy_identity():
    data=collection();legacy=copy.deepcopy(data['legacy_image_only_versions']);scene=data['scenes'][0];f=scene['features'][0];f['geometry']['coordinates'][0][0][1][0]=1.01;f['review_sha256']=feature_review_hash(scene,f)
    validate_physical_versions(data)
    assert data['legacy_image_only_versions']==legacy
    assert scene['image']['sha256']==legacy[0]['image_sha256'] and f['review_sha256']!=legacy[0]['review_sha256']

def test_duplicate_scene_identity_is_rejected():
    data=collection();data['scenes'].append(copy.deepcopy(data['scenes'][0]))
    with pytest.raises(ValueError,match='Duplicate physical scene'):validate_physical_versions(data)

def test_nonfinite_geometry_cannot_have_a_published_fingerprint():
    data=collection();scene=data['scenes'][0];f=scene['features'][0];f['geometry']['coordinates'][0][0][1][0]=float('nan')
    with pytest.raises(ValueError):feature_review_hash(scene,f)
