def make_order_status_query(orderID, auth_token, extra_results={}, expect=None):
    query = {
        "OrderStatus": {
            "args": {
                "orderID": orderID,
                "authToken": auth_token,
            },
            "result": {
                "orderResult": dict({
                    "errorMessage": "String",
                    "orderID":      "String",
                }, **extra_results),
            },
        },
    }
    if expect:
        query['expect'] = expect
    return query

def make_place_order_query(
        auth_token,
        barID,
        orderItemID,
        extra_args={},
        extra_results={},
        ):
    return {
        "PlaceOrder": {
            "args": dict({
                "barID":     barID,
                "authToken": auth_token,
                "userName":  "mark",
                "currency":  "Sterling",
                "price":     340,
                "tip":       60,
                "orderList": [{
                    "id":               orderItemID,
                    "menuItemID":       "barolo",
                    "selectedOptions":  [
                        ["medium glass"],
                    ],
                    "amount":           1,
                }],
                "stripeToken": "stripe_token_here",
                "delivery": "Table",
                "tableNumber": "5",
                "pickupLocation": None,
            }, **extra_args),
            "result": {
                "orderResult": dict({
                    "errorMessage": "String",
                    "barID":        "String",
                }, **extra_results),
            },
        },
    }


def make_refund_query(barID, orderID, auth_token, refund_items=[], reason=None, expect=None):
    query = {
        "RefundOrder": {
            "args": {
                "authToken": auth_token,
                "barID":     barID,
                "orderID":   orderID,
                "reason":    reason,
                "refundItems": refund_items,
            },
            "result": {
                "status": 'String',
            },
        }
    }
    if expect:
        query['expect'] = expect
    return query


def make_complete_order_query(auth_token, orderID, expect=None):
    query = {
        "CompleteOrder": {
            "args": {
                "authToken": auth_token,
                "orderID":   orderID,
            },
            "result": {
                "status": 'String',
            },
        }
    }
    if expect:
        query['expect'] = expect
    return query
