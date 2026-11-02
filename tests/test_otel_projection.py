import importlib.util
import json
from pathlib import Path
import sqlite3
from threading import Thread
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'implementation/workspace_cockpit/otel_projection.py'

def load():
    spec = importlib.util.spec_from_file_location('otel_projection', MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def store(path):
    with sqlite3.connect(path) as c:
        c.execute('CREATE TABLE events(seq INTEGER PRIMARY KEY,kind,trace_id,span_id,parent_span_id,name,status,start_ns,end_ns,duration_ms,data)')
        for n in range(230):
            c.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?)', (n,'span','a'*32,'b'*16,'c'*16,'tool.private_name','OK',100,200,1.25,'TOP_SECRET'))

def test_projection_bounded_readonly_and_content_free(tmp_path):
    m=load(); db=tmp_path/'store.db'; store(db)
    before=db.read_bytes()
    result=m.collect(db)
    assert db.read_bytes()==before
    assert len(result['spans'])==200
    assert result['spans'][0]['seq']==229
    raw=json.dumps(result)
    assert 'TOP_SECRET' not in raw and 'private_name' not in raw and 'data' not in result['spans'][0]
    assert result['spans'][0]['kind']=='tool'
    out=tmp_path/'snapshot.json';m.publish(db,out)
    assert out.stat().st_mode & 0o777==0o640
    assert m.read_snapshot(out)['available']

def test_missing_database_never_created(tmp_path):
    m=load(); db=tmp_path/'absent'; out=tmp_path/'snapshot'
    m.publish(db,out)
    assert not db.exists()
    assert m.read_snapshot(out)['available'] is False
    assert m.read_snapshot(None)['error']=='otel_not_configured'

def test_stale_oversize_corrupt_and_untrusted_fields(tmp_path):
    m=load(); db=tmp_path/'db';store(db);out=tmp_path/'snapshot';m.publish(db,out)
    data=json.loads(out.read_text());data['secret']='no';data['spans'][0]['secret']='no'
    out.write_text(json.dumps(data))
    assert 'secret' not in json.dumps(m.read_snapshot(out))
    data['generated_at']='2000-01-01T00:00:00+00:00';out.write_text(json.dumps(data))
    assert not m.read_snapshot(out)['available']
    out.write_text('x'*(m.MAX_BYTES+1));assert not m.read_snapshot(out)['available']
    out.write_text('[]');assert not m.read_snapshot(out)['available']

def test_cockpit_http_telemetry(tmp_path):
    m=load();db=tmp_path/'db';store(db);out=tmp_path/'snapshot';m.publish(db,out)
    spec=importlib.util.spec_from_file_location('test_otel_server',ROOT/'implementation/workspace_cockpit/server.py')
    server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
    class Handler(server.CockpitHandler):
        otel_snapshot=out
    http=server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=http.serve_forever,daemon=True);thread.start()
    try:
        with urlopen(f'http://127.0.0.1:{http.server_port}/workspace/api/telemetry') as response:
            result=json.load(response)
            assert result['available'] and len(result['spans'])==200
            assert response.headers['Cache-Control']=='no-store'
    finally:
        http.shutdown();thread.join(2);http.server_close()
