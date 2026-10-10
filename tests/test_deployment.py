"""Path hosting cannot escape authentication or make private evidence cacheable."""
import pytest
from fastapi.testclient import TestClient
from server.app import create_app, deployment_prefix


@pytest.mark.parametrize('prefix',['/../compute','/compute/','//compute','https://example.com','/compute?x=1','/compute"</script>','/a%2fb',None])
def test_invalid_deployment_prefix_rejected(prefix):
    with pytest.raises(ValueError): deployment_prefix(prefix)


def test_prefix_bootstrap_and_private_responses(tmp_path):
    app=create_app(tmp_path/'atlas.sqlite3',background=False,root_path='/tools/compute')
    with TestClient(app) as client:
        page=client.get('/')
        assert page.status_code==200
        assert 'base:"/tools/compute/api"' in page.text
        for endpoint in ['publication','catalog/publication','operators/publication','operators/publication?publisher=digital-realty']:
            assert "'/tools/compute/api/"+endpoint+"'" in page.text
        assert "load('evidence-data','/api/publication')" not in page.text
        for path in ['/','/src/pointer-gestures.js','/data/evidence.json','/originals/compute_infrastructure_report.pdf','/api/health']:
            response=client.get(path)
            assert response.status_code==200
            assert 'private' in response.headers['cache-control']
            assert 'public' not in response.headers['cache-control']
        response=client.get('/api/publication')
        assert client.get('/api/publication',headers={'If-None-Match':response.headers['etag']}).status_code==304
        assert client.get('/var/atlas.sqlite3').status_code==404
        assert client.get('/server/app.py').status_code==404
        assert client.get('/data/catalog/source-capture.zip').status_code==404
        assert client.get('/api/docs').status_code==200
        assert '/tools/compute/api/openapi.json' in client.get('/api/docs').text
