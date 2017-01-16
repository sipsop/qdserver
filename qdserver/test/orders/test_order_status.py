from qdserver import run_query, run_feed, run_test_query, auth, model
from . import utils
from .queries import make_order_status_query

model.setup_testing_mode()

def test_query():
    orderID = utils.place_order()
    with auth.set_temp_auth_token(utils.params['userID']) as auth_token:
        # Check order status
        run_test_query(
            make_order_status_query(orderID, auth_token, expect={
                "result": {
                    "orderResult": {
                        "errorMessage": None,
                        "orderID": orderID,
                    },
                },
            })
        )

def test_feed():
    utils.add_bar_with_owner()
    orderID = utils.place_order()

    # Establish a feed and get the first orderResult
    with auth.set_temp_auth_token(utils.params['userID']) as auth_token:
        feed = run_feed(
            make_order_status_query(orderID, auth_token, extra_results={
                'completed': 'Bool',
                'completedTimestamp': 'Float',
            })
        )
        result1 = next(feed)

        # Generate an order event and get the changed orderResult
        utils.complete_order(orderID)
        result2 = next(feed)

    # See that orderResult has actually changed properly
    orderResult1 = result1['result']['orderResult']
    orderResult2 = result2['result']['orderResult']

    print(orderResult1)
    print(orderResult2)

    assert not orderResult1['completed']
    assert orderResult1['completedTimestamp'] is None

    assert orderResult2['completed']
    assert orderResult2['completedTimestamp'] is not None
