import jwt
import time
import uuid
import base64
from contextlib import contextmanager

client_secret = 'jXtBkWhMD-UEk16iXeS1jLwEw9fCBrPXFasX0EKHSZIhmt-JxeRdyw3ipvxz9I6V'
client_id = 'phA8QFWKknNtcDwVefccBf82sIp4bw6c'

secret = base64.b64decode(client_secret.replace("_","/").replace("-","+"))

_temp_auth_token = None
_temp_user_id = None

@contextmanager
def set_temp_auth_token(user_id):
    global _temp_auth_token, _temp_user_id
    auth_token = str(uuid.uuid4())
    _temp_auth_token = auth_token
    _temp_user_id = user_id
    yield auth_token
    _temp_auth_token = None
    _temp_user_id = None

def validate_token(token):
    """
    Validate the authorization token ('idToken') issued by Auth0.

    Returns the userID of the user.
    """
    if token is None:
        # NOTE: This check is important because we short-circuit below
        #       with _temp_auth_token
        raise ValueError("Expected non-null user id")

    if token == _temp_auth_token:
        return _temp_user_id

    try:
        payload = jwt.decode(token, secret, audience=client_id)
    except (jwt.ExpiredSignature, jwt.InvalidAudienceError, jwt.DecodeError):
        raise ValueError("Credentials invalid or expired, please try again")

    # Example response:
    #    { 'iat': 1474629433
    #    , 'azp': 'phA8QFWKknNtcDwVefccBf82sIp4bw6c'
    #    , 'exp': 1474665433
    #    , 'iss': 'https://tuppu.eu.auth0.com/'
    #    , 'sub': 'email|57c2d977469d42056d3f7376'
    #    , 'aud': 'phA8QFWKknNtcDwVefccBf82sIp4bw6c'
    #    }

    if time.time() > payload['exp']:
        raise ValueError("Credentials expired, please try again")

    return payload['sub']
