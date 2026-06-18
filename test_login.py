import urllib.request
import urllib.error
import json

# Try first password
for password in ["Pass@12345", "AKSHAtJAIN#2685"]:
    try:
        req = urllib.request.Request(
            'http://127.0.0.1:3000/auth/login',
            data=json.dumps({'email': 'i.jain.akshat@gmail.com', 'password': password}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        print(f"SUCCESS with password: {password}")
        print(f"Token: {data.get('token', 'N/A')[:50]}...")
        print(f"Email: {data.get('email')}")
        print(f"User ID: {data.get('user_id')}")
        break
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"FAILED with password '{password}': {error_body}")
    except Exception as e:
        print(f"Connection error: {e}")
