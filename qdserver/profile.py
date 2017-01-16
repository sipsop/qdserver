from curry import typeddict, optional
from qdserver import ql, model, auth
from qdserver.common import ID

class UserProfile(ql.QuerySpec):
    args_spec = [
        ('authToken', str),
    ]
    result_spec = [
        ('profile', model.UserProfile),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        userID = auth.validate_token(args['authToken'])
        return UserProfile.make(
            profile=get_user_profile(userID)
        )

ProfileParams = typeddict(
    [ ('firebaseToken', optional(str))
    , ('email', str)
    ], name='ProfileParams')


class RegisterUser(ql.QuerySpec):
    """
    Register a user with email and firebase token, so that we can send
    him/her emails and push notifications.
    """

    args_spec = [
        ('authToken', str),
        ('profileParams', ProfileParams),
    ]
    result_spec = [
        ('success', bool),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        userID = auth.validate_token(args['authToken'])

        params = args['profileParams']
        email = params['email']
        firebase_token = params.get('firebaseToken')

        print("REGISTERING USER:", email, firebase_token)

        model.upsert(
            model.UserProfiles,
            model.UserProfile({
                'id': userID,
                'email': email,
                'firebase_token': firebase_token,
            })
        )
        return RegisterUser.make({
            'success': True,
        })

def get_user_profile(userID) -> model.UserProfile or None:
    user_profile = model.run(model.UserProfiles.get(userID)) or {}
    return dict(default_profile, **user_profile)

def add_bar_owner(userID, barIDs):
    """Add `userID` as the owner of `barIDs`"""
    # TODO: Use 'update' query to make this atomic...
    profile = model.run(model.UserProfiles.get(userID))
    if profile is None:
        profile = model.UserProfile(
            is_bar_owner=True,
            bars=barIDs,
        )
    else:
        for barID in barIDs:
            if barID not in profile['bars']:
                profile['bars'].append(barID)

    profile = dict(profile, id=userID)
    model.run(model.UserProfiles.insert(profile))


def is_bar_owner(userID, barID) -> bool:
    """See if `userID` is an owner of bar `barID`"""
    profile = model.run(model.UserProfiles.get(userID))
    if profile is None:
        return False
    return barID in profile['bars']


default_profile = model.UserProfile(
    is_bar_owner=False,
    bars=[],
)

#===------------------------------------------------------------------===
# Register
#===------------------------------------------------------------------===

def register(dispatcher):
    dispatcher.register(UserProfile)
    dispatcher.register(RegisterUser)
