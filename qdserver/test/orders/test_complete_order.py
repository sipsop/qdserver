from qdserver import run_test_query, model, auth
from . import utils
from .queries import make_complete_order_query

model.setup_testing_mode()

def test_complete_order():
    utils.add_bar_with_owner()
    orderID = utils.place_order()
    with auth.set_temp_auth_token(utils.params['barAdminID']) as auth_token:
        # Complete an order
        run_test_query(make_complete_order_query(auth_token, orderID,
            expect={
                "result": {
                    "status": "OK"
                }
            },
        ))
        run_test_query(make_complete_order_query(auth_token, orderID,
            expect={
                "result": {
                    "status": "OK"
                }
            },
        ))
