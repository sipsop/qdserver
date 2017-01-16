from qdserver import auth, run_query, model
model.setup_testing_mode()

def make_query(auth_token):
    return {
        "UserProfile": {
            "args": {
                "authToken": auth_token,
            },
            "result": {
                "profile": {
                    "is_bar_owner": "Bool",
                    "bars": ["String"],
                },
            },
        },
    }

def test_query1():
    with auth.set_temp_auth_token('some_user_id') as auth_token:
        result = run_query(make_query(auth_token))
        print(result)
        profile = result['result']['profile']
        assert not profile['is_bar_owner']
        assert isinstance(profile['bars'], list)
        assert len(profile['bars']) == 0


if __name__ == '__main__':
    test_query1()
