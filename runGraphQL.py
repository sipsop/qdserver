import sys
import requests

query = sys.stdin.read().replace('\\n', '\n').replace('\\t', '\t')

response = requests.post(
    'http://localhost:5000/graphql',
    data=query,
    headers={'content-type': 'application/graphql'},
    )

print(response.status_code)
response.raise_for_status()
print(response.json())
