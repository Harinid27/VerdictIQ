import requests
try:
    res = requests.post("http://localhost:8000/api/agent0/process/35d82dfc5c0c29f93ad1c583", json={})
    print("STATUS:", res.status_code)
    print("HEADERS:", res.headers)
    print("BODY:", res.text[:2000])
except Exception as e:
    print("ERROR:", e)
