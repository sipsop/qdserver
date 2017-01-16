from qdserver import run_test_query, model, auth
from . import utils
from .queries import make_refund_query

model.setup_testing_mode()

def test_refund():
    utils.add_bar_with_owner()
    orderID = utils.place_order()
    with auth.set_temp_auth_token(utils.params['barAdminID']) as auth_token:
        # Issue a refund
        run_test_query(make_refund_query(utils.params['barID'], orderID, auth_token,
            refund_items=[{
                "id": utils.params['orderItemID'],
                "amount": 1,
            }],
            expect={
                "result": {
                    "status": "OK"
                }
            },
        ))
        run_test_query(make_refund_query(utils.params['barID'], orderID, auth_token,
            refund_items=[{
                "id": utils.params['orderItemID'],
                "amount": 1,
            }],
            expect={
                "error": "Refunded amount exceeds paid amount",
            },
        ))
