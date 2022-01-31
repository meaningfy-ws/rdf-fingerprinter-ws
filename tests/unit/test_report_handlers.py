from json import loads, dumps
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZipFile

from pathlib import Path

from fingerprinter.services.report_handling import zip_report_files, copy_report_files, generate_meta_file, \
    read_meta_file, build_fingerprinting_reports_location, get_available_fingerprintings, get_report, delete_report, \
    build_report_from_sparql_endpoint, fingerprint_sparql_endpoint


def test_zip_report_files(tmpdir, monkeypatch):
    monkeypatch.setenv('RDF_FINGERPRINTER_ZIP_REPORT_NAME', 'report.zip')
    monkeypatch.setenv('RDF_FINGERPRINTER_HTML_REPORT_NAME', 'report.html')
    monkeypatch.setenv('RDF_FINGERPRINTER_JSON_REPORT_NAME', 'report.json')

    html_report = tmpdir.join('report.html')
    html_report.write('html')
    json_report = tmpdir.join('report.json')
    json_report.write('json')

    location = tmpdir.mkdir('location')

    zip_location = zip_report_files(output_location=location, html_report=html_report, json_report=json_report)

    with ZipFile(zip_location) as zip_file:
        assert zip_file.namelist() == ['report.html', 'report.json']
        assert zip_file.read('report.html') == b'html'
        assert zip_file.read('report.json') == b'json'


def test_copy_report_files(tmpdir, monkeypatch):
    reports_location = tmpdir.mkdir('reports')

    monkeypatch.setenv('RDF_FINGERPRINTER_ZIP_REPORT_NAME', 'report.zip')
    monkeypatch.setenv('RDF_FINGERPRINTER_HTML_REPORT_NAME', 'report.html')
    monkeypatch.setenv('RDF_FINGERPRINTER_JSON_REPORT_NAME', 'report.json')
    monkeypatch.setenv('RDF_FINGERPRINTER_REPORTS_DB_LOCATION', str(reports_location))

    zip_report = reports_location.join('report.zip')
    zip_report.write('zip')
    html_report = reports_location.join('report.html')
    html_report.write('html')
    json_report = reports_location.join('report.json')
    json_report.write('json')
    uid = str(uuid4())

    report_location = copy_report_files(uid=uid, zip_report=zip_report, html_report=html_report,
                                        json_report=json_report)

    assert (Path(report_location) / 'report.zip').is_file()
    assert (Path(report_location) / 'report.zip').read_text() == 'zip'

    assert (Path(report_location) / 'report.html').is_file()
    assert (Path(report_location) / 'report.html').read_text() == 'html'

    assert (Path(report_location) / 'report.json').is_file()
    assert (Path(report_location) / 'report.json').read_text() == 'json'


def test_generate_meta_file_and_read_file(tmpdir, monkeypatch):
    monkeypatch.setenv('RDF_FINGERPRINTER_REPORT_META_NAME', 'meta.json')

    reports_location = Path(str(tmpdir.mkdir('report')))
    file_name = 'fingerprinted.rdf'
    url = ''
    uid = str(uuid4())
    timestamp = 'today'
    validation_on = 'file'
    html_report = 'report.html'
    json_report = 'report.json'
    zip_report = 'report.zip'
    graphs = ['graph1', 'graph2']

    meta_file = generate_meta_file(reports_location=reports_location, file_name=file_name,
                                   url=url, uid=uid, timestamp=timestamp, validation_on=validation_on,
                                   html_report=html_report,
                                   json_report=json_report, zip_report=zip_report, graphs=graphs)

    meta_content = loads(Path(meta_file).read_text())

    assert meta_content['uid'] == uid
    assert meta_content['validation_on'] == validation_on
    assert meta_content['file'] == file_name
    assert meta_content['url'] == url
    assert meta_content['graphs'] == graphs
    assert meta_content['html_report'] == html_report
    assert meta_content['json_report'] == json_report
    assert meta_content['zip_report'] == zip_report
    assert meta_content['created_at'] == timestamp

    meta_content = read_meta_file(str(reports_location))

    assert meta_content['uid'] == uid
    assert meta_content['validation_on'] == validation_on
    assert meta_content['file'] == file_name
    assert meta_content['url'] == url
    assert meta_content['graphs'] == graphs
    assert meta_content['html_report'] == html_report
    assert meta_content['json_report'] == json_report
    assert meta_content['zip_report'] == zip_report
    assert meta_content['created_at'] == timestamp


def test_build_fingerprinting_reports_location_success(tmpdir):
    uid1 = str(uuid4())
    uid2 = str(uuid4())

    reports = tmpdir.mkdir('reports')
    report1 = reports.mkdir(uid1)
    meta1 = report1.join('meta.json')
    meta1.write(dumps({"uid": uid1}))
    report2 = reports.mkdir(uid2)
    meta2 = report2.join('meta.json')
    meta2.write(dumps({"uid": uid2}))

    assert build_fingerprinting_reports_location(fingerprinting_uid=uid1, db_location=reports) == str(report1)


def test_build_fingerprinting_reports_location_failure(tmpdir):
    reports = tmpdir.mkdir('reports')

    assert not build_fingerprinting_reports_location(fingerprinting_uid='non-existing', db_location=reports)


def test_get_available_fingerprintings(tmpdir):
    uuid1 = str(uuid4())
    uuid2 = str(uuid4())

    reports = tmpdir.mkdir('reports')
    report1 = reports.mkdir(uuid1)
    meta1 = report1.join('meta.json')
    meta_content1 = {
        "uid": uuid1,
        "validation_on": "file",
    }
    meta1.write(dumps(meta_content1))
    report2 = reports.mkdir(uuid2)
    meta2 = report2.join('meta.json')
    meta_content2 = {
        "uid": uuid2,
        "validation_on": "url"
    }
    meta2.write(dumps(meta_content2))

    reports = get_available_fingerprintings(reports_location=reports)

    assert len(reports) == 2
    assert meta_content1 in reports
    assert meta_content2 in reports


def test_get_report_html(tmpdir):
    uid = str(uuid4())
    reports = tmpdir.mkdir('reports')
    report = reports.mkdir(uid)
    report.join('report.html').write('html')
    meta = report.join('meta.json')
    meta_content = {
        "uid": uid,
        "created_at": "today",
        "html_report": "report.html"
    }
    meta.write(dumps(meta_content))

    report, _ = get_report(uid=uid, extension="html", reports_location=reports)

    assert Path(report).read_text() == "html"


def test_get_report_json(tmpdir):
    uid = str(uuid4())
    reports = tmpdir.mkdir('reports')
    report = reports.mkdir(uid)
    report.join('report.json').write('json')
    meta = report.join('meta.json')
    meta_content = {
        "uid": uid,
        "created_at": "today",
        "json_report": "report.json"
    }
    meta.write(dumps(meta_content))

    report, _ = get_report(uid=uid, extension="json", reports_location=reports)

    assert Path(report).read_text() == "json"


def test_get_report_zip(tmpdir):
    uid = str(uuid4())
    reports = tmpdir.mkdir('reports')
    report = reports.mkdir(uid)
    report.join('report.zip').write('zip')
    meta = report.join('meta.json')
    meta_content = {
        "uid": uid,
        "created_at": "today",
        "zip_report": "report.zip"
    }
    meta.write(dumps(meta_content))

    report, _ = get_report(uid=uid, extension="zip", reports_location=reports)

    assert Path(report).read_text() == "zip"


def test_remove_report_success(tmpdir):
    uid = str(uuid4())
    reports = tmpdir.mkdir('reports')
    report = reports.mkdir(uid)
    report.join('report.zip').write('zip')
    meta = report.join('meta.json')
    meta_content = {
        "uid": uid,
        "created_at": "today",
        "zip_report": "report.zip"
    }
    meta.write(dumps(meta_content))

    delete_report(uid=uid, reports_location=reports)

    assert not Path(report).exists()


def test_remove_report_failure(tmpdir):
    uid = str(uuid4())
    reports = tmpdir.mkdir('reports')

    is_success = delete_report(uid=uid, reports_location=reports)

    assert not is_success


@patch('fingerprinter.services.report_handling.generate_endpoint_fingerprint_report')
@patch('fingerprinter.services.report_handling.zip_report_files')
def test_fingerprint_sparql_endpoint(mock_zip_report_files, mock_generate_endpoint_fingerprint_report, tmpdir):
    location = tmpdir.mkdir('reports')
    sparql_endpoint = "http://example.com/sparql"
    html_report = tmpdir.join('report.html')
    html_report.write('html')
    json_report = tmpdir.join('report.json')
    json_report.write('json')
    zip_report = tmpdir.join('report.zip')
    zip_report.write('zip')

    mock_generate_endpoint_fingerprint_report.side_effect = [html_report, json_report]

    mock_zip_report_files.return_value = zip_report

    result_html, result_json, result_zip = fingerprint_sparql_endpoint(sparql_endpoint=sparql_endpoint,
                                                                       output_location=location)

    assert Path(result_html).read_text() == 'html'
    assert Path(result_json).read_text() == 'json'
    assert Path(result_zip).read_text() == 'zip'


@patch('fingerprinter.services.report_handling.fingerprint_sparql_endpoint')
def test_generate_reports_from_sparql_endpoint(mock_fingerprint_sparql_endpoint, tmpdir):
    location = tmpdir.mkdir('reports')
    sparql_endpoint = "http://localhost:3030/sparql"
    html_report = tmpdir.join('report.html')
    html_report.write('html')
    json_report = tmpdir.join('report.json')
    json_report.write('json')
    zip_report = tmpdir.join('report.zip')
    zip_report.write('zip')

    mock_fingerprint_sparql_endpoint.return_value = (str(html_report), str(json_report), str(zip_report))

    reports_location = build_report_from_sparql_endpoint(location=str(location), sparql_endpoint=sparql_endpoint)

    assert (Path(reports_location) / 'report.html').read_text() == 'html'
    assert (Path(reports_location) / 'report.json').read_text() == 'json'
    assert (Path(reports_location) / 'report.zip').read_text() == 'zip'


def test_build_report_from_sparql_endpoint(tmpdir):
    pass
