from qdserver import model, profile
from .types import Message, Media, Medium
from .push import send_push_notification
from .email import send_email
from .inapp import send_in_app_message

def send_message_async(userID : model.UserID, message : Message, media : Media):
    # TODO: Spawn in separate greenlet?
    send_message(userID, message, media)

def send_message(userID : model.UserID, message : Message, media : Media):
    user_profile = profile.get_user_profile(userID)
    for medium in media:
        if medium == Medium.Push:
            send_push_notification(user_profile, message)
        elif medium == Medium.Email:
            send_email(user_profile, message)
        elif medium == Medium.InApp:
            send_in_app_message(user_profile, message)
        else:
            raise ValueError("Unsupported medium: '%s'" % (medium,))
