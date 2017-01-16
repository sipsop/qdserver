import ssl
import json
import websocket
# ws = websocket.WebSocket() #sslopt={"check_hostname": False})
# ws.connect("ws://localhost:9000/api/v1/websocket")

# URL = "wss://localhost:9000/api/v1/websocket/"
frontendURL = "ws://104.199.81.246:8080/api/v1/websocket/"
backendURL  = "ws://192.168.2.2:9000/api/v1/websocket/"
backendURL  = "ws://192.168.1.223/api/v1/websocket/"
# backendURL  = "ws://localhost/api/v1/websocket/"
# backendURL2 = "wss://104.199.12.19:8081/api/v1/websocket/"
# backendURL3 = "wss://api.qdodger.com:8081/api/v1/websocket/"
URL = backendURL
# URL = "ws://localhost/echo"
# ws = websocket.create_connection(URL)

ws = websocket.WebSocket(
    sslopt={
        "cert_reqs": ssl.CERT_NONE,
        "check_hostname": False,
    }
)
ws.connect(URL)

def test_query():
    query = {
        'messageID': '3838299178',
        'type': 'query',
        'query': {
            "Hello": {
                "result": {
                    "world": "String",
                }
            }
        }
    }

    ws.send(json.dumps(query))
    result = json.loads(ws.recv())
    print(result)
    assert result == {'result': {'world': 'Hello World!'}, 'messageID': '3838299178'}

    ws.send(json.dumps(query))
    result = json.loads(ws.recv())
    print(result)
    assert result == {'result': {'world': 'Hello World!'}, 'messageID': '3838299178'}

def test_feed():
    query1 = {
        'messageID': '237616167',
        'type': 'feed',
        'query': {
            "Hello": {
                "result": {
                    "world": "String",
                }
            }
        }
    }
    query2 = {
        'messageID': '237616167',
        'type': 'feed',
        'query': {
            "Hello": {
                "result": {
                    "world": "String",
                    "universe": "String",
                }
            }
        }
    }

    ws.send(json.dumps(query1))
    result1 = json.loads(ws.recv())
    print(result1)

    ws.send(json.dumps(query2))
    result2 = json.loads(ws.recv())
    print(result2)
    result3 = json.loads(ws.recv())
    result4 = json.loads(ws.recv())

    assert result1 == {'result': {'world': 'Hello World!'}, 'messageID': '237616167'}
    assert result2 == {'result': {'world': 'Hello World!', 'universe': 'Hello Universe!'}, 'messageID': '237616167'}
    assert result2 == result3 == result4

test_query()
test_feed()
