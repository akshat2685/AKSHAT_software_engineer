import urllib.request
import urllib.error
import json

req = urllib.request.Request(
    'http://127.0.0.1:3000/auth/register',
    data=json.dumps({'email': 'akshat@edysor.ai', 'password': 'Pass@12345'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
try:
    response = urllib.request.urlopen(req)
    print("Success:", response.read().decode())
except urllib.error.HTTPError as e:
    print("Error:", e.read().decode())
