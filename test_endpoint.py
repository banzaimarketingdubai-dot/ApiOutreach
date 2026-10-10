import urllib.request, json

req = urllib.request.Request(
    'https://web-production-c4d98.up.railway.app/api/v1/leads/tools/reset_enrichment', 
    data=json.dumps({'lead_ids':['some-uuid']}).encode('utf-8'), 
    headers={'Content-Type': 'application/json'}, 
    method='POST'
)

try: 
    print(urllib.request.urlopen(req).read().decode()) 
except Exception as e:
    print(getattr(e, 'code', str(e)), getattr(e, 'read', lambda: b'None')().decode())
