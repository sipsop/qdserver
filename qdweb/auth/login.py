import uuid
from datetime import datetime

from flask import session
from curry import typeddict, alias, URL, Email, maybe_none, load_json, dump_json
from curry.typing.jsonify import datetime_opts

UserID = alias('UserID', str)

# User profile as set globally whenever the user is logged in:
#
#   var userProfile = ...
#
UserProfile = typeddict(
    [ ('user_id',           UserID)
    , ('email',             Email)
    , ('picture',           URL)
    , ('nickname',          maybe_none(str))
    ], name='UserProfile')

# User session as set in the session cookie
UserSession = typeddict(
    [ ('user_id',           UserID)
    , ('session_id',        str)
    , ('creation',          datetime)
    , ('email',             Email)
    , ('picture',           URL)
    , ('nickname',          maybe_none(str))
    ], name='UserSession')

def serialize_session(session : UserSession) -> str:
    return dump_json(session, UserSession, json_opts=datetime_opts)

def deserialize_session(session_str : str) -> UserSession:
    return load_json(session_str, UserSession, json_opts=datetime_opts)

def user_login(user_profile : UserProfile):
    user_session = UserSession(
        { 'user_id':    user_profile['user_id']
        , 'session_id': str(uuid.uuid4())
        , 'creation':   datetime.now()
        , 'email':      user_profile['email']
        , 'picture':    user_profile['picture']
        , 'nickname':   user_profile['nickname']
        })
    session['user_session'] = serialize_session(user_session)

def load_user_session() -> UserSession:
    return deserialize_session(session['user_session'])

def get_profile(user_session : UserSession) -> UserProfile:
    return UserProfile(
        { 'user_id':    user_session['user_id']
        , 'email':      user_session['email']
        , 'picture':    user_session['picture']
        , 'nickname':   user_session['nickname']
        })

def user_is_logged_in():
    if 'user_session' not in session:
        return False
    # See if we can properly load the session
    load_user_session()
    return True

def get_user_id() -> UserID:
    user_session = load_user_session()
    return user_session['user_id']

def user_logout():
    del session['user_session']
    assert not user_is_logged_in()
    
