import sys
import requests

query = sys.stdin.read().replace('\\n', '\n').replace('\\t', '\t')

response = requests.post(
    'http://localhost:9000/api/v1',
    data=query,
    headers={'content-type': 'application/json'},
    )

print(response.status_code)
response.raise_for_status()
print(response.json())
