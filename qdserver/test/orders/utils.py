from curry import typeddict

from qdserver import run_query, model, bar, auth, profile
from . import queries

TestParams = typeddict(
    [ ('barID',       model.ID)
    , ('barAdminID',  model.ID)
    , ('userID',      model.ID)
    , ('orderItemID', model.ID)
    ], name='TestParams')

params = TestParams(
    barID       = 'bar_id',
    barAdminID  = 'bar_admin_id',
    userID      = 'some_user_id',
    orderItemID = 'order_item_id',
)

def add_bar_with_owner(params : TestParams = params):
    model.run(model.Bars.get(params['barID']).delete())
    bar.add_qdodger_bar(params['barID'])
    profile.add_bar_owner(params['barAdminID'], [params['barID']])

def place_order(params : TestParams = params) -> model.OrderID:
    # Place an order
    with auth.set_temp_auth_token(params['userID']) as auth_token:
        result = run_query(
            queries.make_place_order_query(
                auth_token,
                barID=params['barID'],
                orderItemID=params['orderItemID'],
                extra_results={"orderID": "String"},
            )
        )

    assert 'result' in result, result
    order_result = result['result']['orderResult']
    return order_result['orderID']

def refund(orderID, params : TestParams = params, refund_items=[]):
    with auth.set_temp_auth_token(params['barAdminID']) as auth_token:
        run_query(
            queries.make_refund_query(
                params['barID'],
                orderID,
                auth_token,
                refund_items,
            )
        )

def complete_order(orderID, params : TestParams = params):
    with auth.set_temp_auth_token(params['barAdminID']) as auth_token:
        run_query(
            queries.make_complete_order_query(
                auth_token,
                orderID,
            )
        )
