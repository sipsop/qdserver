import json
import requests

from curry.typing import typeddict, enum

firebase_url = "https://fcm.googleapis.com/fcm/send"

server_key = "AIzaSyBwTajDshQAWFrP6nemBXuOm525ebwGZjk"
# token = input("Firebase Token of Device: ")
token = "dTzmRbOEkBo:APA91bGGcVBqwizmnacTcPatuNVQETkqVjjABDvwDujm6c0w240rO0__Z9TJ79i2vyQP2Zv4fdmbFTRPnLLTmd1lkEvCCH6KSsQc0gNoYTLJwzcsXZOnMVt7tRwWDGU-45W6Ln8o_MIw"

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'key=' + server_key,
}

data1 = {
    "to": token,
    "data": {
        "type": "DataPushNotification",
    },
}

data2 = {
    "to": token,
    "notification": {
        "title": "Remote NOTIFICATION!",
        "body":  "remote message...!",
        "priority": "high",
        "sound": "default",
        # "icon": "ic_notification",
    },
    "data": {
        "title":    "Remote push notification title2!",
        "content":  "Remote push notificaiton message!",
        "deepLink": "deep link here...",
        "topic":    "order notification <orderID here>",
        # "popup":    True,
    },
}

Priority = enum('Priority', ['normal', 'high'])
Sound = enum('Sound', ['default'])

Notification = typeddict(
    [ ('message_id', str)
    , ('title', str)
    , ('body', str)
    , ('priority', Priority)
    , ('collapse_key', str)
    # Wake up inactive client app
    , ('content_available', bool)
    , ('sound', Sound)
    ], name='Notification')

def push(data):
    requests.post(
        firebase_url,
        headers=headers,
        data=json.dumps(data),
    )

# push(data1)
push(data2)
