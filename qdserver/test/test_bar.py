from qdserver import run_query, run_feed, run_test_query, model, bar, auth, profile
model.setup_testing_mode()

BarStatusType = {
    "qdodger_bar": "Bool",
    "taking_orders": "Bool",
    "table_service": "String",
    "pickup_locations": [{"name": "String", "open": "Bool"}],
}

def make_query(barID):
    return {
        "BarStatus": {
            "args": {
                "barID": barID,
            },
            "result": {
                "bar_status": BarStatusType,
            },
        }
    }

def test_bar_status1():
    query = make_query('some_bar_id')
    run_test_query(dict(query, **{
        "expect": {
            "result": {
                "bar_status": {
                    "qdodger_bar":   False,
                    "taking_orders": False,
                    "table_service": "Disabled",
                    "pickup_locations": [],
                }
            }
        }
    }))

def test_update_bar_status_invalid_auth_token():
    barID = 'some_random_bar_id'
    model.run(model.Bars.get(barID).delete())
    bar.add_qdodger_bar(barID)
    run_test_query({
        "UpdateBarStatus": {
            "args": {
                "barID": barID,
                "authToken": "some garbage here",
                "statusUpdate": {
                    "TakingOrders": True,
                },
            },
            "result": {
                "bar_status": BarStatusType,
            },
        },
        "expect": {
            "error": "Credentials invalid or expired, please try again",
        }
    })

def test_update_bar_status_not_a_bar_owner():
    barID = 'some_random_bar_id'
    model.run(model.Bars.get(barID).delete())
    bar.add_qdodger_bar(barID)
    with auth.set_temp_auth_token('some_user_id') as auth_token:
        run_test_query({
            "UpdateBarStatus": {
                "args": {
                    "barID": barID,
                    "authToken": auth_token,
                    "statusUpdate": {
                        "TakingOrders": True,
                    }
                },
                "result": {
                    "bar_status": BarStatusType,
                },
            },
            "expect": {
                'error': 'You have not been approved as an owner of this bar (yet).',
            },
        })

def test_bar_status_feed():
    userID = 'some_user_id'
    barID = 'some_random_bar_id'
    bar.add_qdodger_bar(barID)
    feed = run_feed(make_query(barID))
    result1 = next(feed)
    try:
        with auth.set_temp_auth_token(userID) as auth_token:
            profile.add_bar_owner(userID, [barID])
            run_query({
                "UpdateBarStatus": {
                    "args": {
                        "barID": barID,
                        "authToken": auth_token,
                        'statusUpdate': {
                            'SetTableService': 'Food',
                        }
                    },
                    "result": {
                        "bar_status": BarStatusType,
                    },
                }
            })
        result2 = next(feed)
    finally:
        model.run(model.UserProfiles.get(userID).delete())
        model.run(model.Bars.get(barID).delete())

    assert 'error' not in result1, result1
    assert 'error' not in result2, result2

    bar_status1 = result1['result']['bar_status']
    bar_status2 = result2['result']['bar_status']

    assert bar_status1['table_service'] == 'Disabled'
    assert bar_status2['table_service'] == 'Food'

def test_update_bar_status():
    userID = 'some_user_id'
    barID = 'some_random_bar_id'
    bar.add_qdodger_bar(barID)
    try:
        update_bar_status(userID, barID)
    finally:
        model.run(model.UserProfiles.get(userID).delete())
        model.run(model.Bars.get(barID).delete())

def update_bar_status(userID, barID):
    with auth.set_temp_auth_token(userID) as auth_token:
        profile.add_bar_owner(userID, [barID])
        run_test_query({
            "UpdateBarStatus": {
                "args": {
                    "barID": barID,
                    "authToken": auth_token,
                    'statusUpdate': {
                        'TakingOrders': True,
                        'SetTableService': 'Food',
                        'AddBar': {'name': 'First Floor', 'listPosition': 1},
                        'SetBarOpen': {'name': 'First Floor', 'open': True},
                    }
                },
                "result": {
                    "bar_status": BarStatusType,
                },
            },
            "expect": {
                "result": {
                    "bar_status": {
                        "qdodger_bar":   True,
                        "taking_orders": True,
                        "table_service": 'Food',
                        "pickup_locations": [
                            {'name': 'Main Bar', 'open': False},
                            {'name': 'First Floor', 'open': True},
                        ],
                    }
                },
            },
        })
