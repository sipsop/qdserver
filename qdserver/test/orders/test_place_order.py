from qdserver import run_query, run_test_query, auth, model
from .queries import make_place_order_query

model.setup_testing_mode()

def make_expect_query(auth_token):
    query = make_place_order_query(
        auth_token,
        barID='bar_id_here',
        orderItemID='order_item_id',
    )
    query.update({
        "expect": {
            "result": {
                "orderResult": {
                    "errorMessage": None,
                    "barID":        "bar_id_here",
                },
            },
        },
    })
    return query

def test_query1():
    with auth.set_temp_auth_token('some_user_id') as auth_token:
        run_test_query(make_expect_query(auth_token))

def test_query_error1():
    query = make_expect_query(None)
    result = run_query(query)
    assert result['error']
    assert 'result' not in result

def test_query_error2():
    query = make_expect_query("invalid_token_here")
    query['expect'] = {'error': 'Credentials invalid or expired, please try again'}
    run_test_query(query)

def test_query_error3():
    run_test_query({
        "PlaceOrderrrzzz": {
            "args": {
                "barID":    "bar_id_here",
            },
            "result": {
                "orderResult": {
                    "errorMessage": "String",
                    "barID":        "String",
                }
            },
        },
        "expect": {
            'error': "'PlaceOrderrrzzz'",
        },
    })

def test_query_error4():
    run_test_query({
        "PlaceOrder": {
            "args": {
                "barID":    "bar_id_here",
                # missing arguments here...
            },
            "result": {
                "orderResult": {
                    "errorMessage": "String",
                    "barID":        "String",
                }
            },
        },
        "expect": {
            "error": "Missing arguments 'authToken, currency, delivery, "
                     "orderList, pickupLocation, price, stripeToken, "
                     "tableNumber, tip, userName' for query of type 'PlaceOrder'",
        }
    })


if __name__ == '__main__':
    test_query1()
    test_query_error1()
