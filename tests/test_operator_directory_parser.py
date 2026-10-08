import pytest
from tools.capture_operator_directory import parse_directory


def sample(rows='<tr><td>Frankfurt, Hesse</td><td>Equinix Data Center</td><td>FR2</td><td>24/7 on-site operational coverage</td></tr>'):
    return ('<main><h2>EMEA</h2><h3>Germany</h3><table><tr><th>Metro</th><th>IBX&nbsp;Type</th><th>IBX Name</th><th>Coverage Type</th></tr>'+rows+'</table></main>').encode()


def test_operator_parser_preserves_boundaries():
    rows = parse_directory(sample())
    assert rows[0]['code'] == 'FR2' and rows[0]['source_country'] == 'Germany'
    assert rows[0]['coordinates'] is None and rows[0]['it_mw'] is None
    assert rows[0]['service_coverage'] == '24/7 on-site operational coverage'
    assert 'status' not in rows[0]


def test_empty_coverage_is_null_not_zero():
    assert parse_directory(sample().replace(b'24/7 on-site operational coverage', b''))[0]['service_coverage'] is None


@pytest.mark.parametrize('raw', [b'<html>blocked</html>', sample().replace(b'IBX Name', b'New schema'),
    sample().replace(b'EMEA', b'Unknown region'), sample('').replace(b'<h3>Germany</h3>', b''),
    sample().replace(b'FR2', b'FR2/FR4'), sample().replace(b'<td>FR2</td>', b'<td></td>'), sample('')])
def test_schema_drift_fails_closed(raw):
    with pytest.raises(ValueError):
        parse_directory(raw)


def test_duplicate_codes_do_not_silently_collapse():
    row = '<tr><td>Frankfurt</td><td>Equinix Data Center</td><td>FR2</td><td></td></tr>'
    with pytest.raises(ValueError, match='Duplicate'):
        parse_directory(sample(row + row))


def test_browser_optional_end_tags_keep_cells_separate():
    raw = sample().replace(b'</th>', b'').replace(b'</td>', b'').replace(b'</tr>', b'')
    assert parse_directory(raw) == parse_directory(sample())
