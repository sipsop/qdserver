import json
import requests

from curry import typeddict, alias, enum, to_json, drop_nones
from qdserver import model
from .types import Message

#===------------------------------------------------------------------===
# Push Notification Types
#===------------------------------------------------------------------===

FirebaseToken = alias('FirebaseToken', str)

FirebasePriority = enum('FirebasePriority', [
    'normal',
    'high',
])

FirebaseSound = enum('FirebaseSound', [
    'default',
])

FirebaseNotification = typeddict(
    [ ('message_id',    str)
    , ('title',         str)
    , ('body',          str)
    , ('priority',      FirebasePriority)
    , ('collapse_key',  str)
    # Wake up inactive client app
    , ('content_available', bool)
    , ('sound',         FirebaseSound)
    ], name='FirebaseNotification')

PushNotification = typeddict(
    [ ('to',            FirebaseToken)
    , ('notification',  FirebaseNotification)
    , ('data',          Message)
    ], name='FireBaseMessage')


def make_push_notification(
        user_profile : model.UserProfile,
        message : Message
        ) -> PushNotification:
    firebase_token = user_profile['firebase_token']
    notification = drop_nones({
        'message_id': message.get('messageID'),
        'title':      message['title'],
        'body':       message['content'],
        'priority':   message.get('priority'),
    })
    if message.get('sound'):
        notification['sound'] = FirebaseSound.default

    return PushNotification(
        to=firebase_token,
        notification=notification,
        data=message,
    )

#===------------------------------------------------------------------===
# Dispatch
#===------------------------------------------------------------------===

firebase_url = "https://fcm.googleapis.com/fcm/send"
server_key = "AIzaSyBwTajDshQAWFrP6nemBXuOm525ebwGZjk"

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'key=' + server_key,
}

def send_push_notification(user_profile : model.UserProfile, message : Message):
    if 'firebase_token' not in user_profile:
        # raise ValueError("No firebase token is set")
        return
    push_notification = make_push_notification(user_profile, message)
    push(to_json(push_notification, PushNotification))

def push(data):
    # TODO: Retry + exponential backoff
    response = requests.post(
        firebase_url,
        headers=headers,
        data=json.dumps(data),
    )
    response.raise_for_status()
