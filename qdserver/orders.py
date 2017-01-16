import time
import datetime

from qdserver import auth, model, ql, menu, messaging, profile
from qdserver.common import ID, TimeStamp, UserName, Receipt, shortid
from curry import fmap
from curry.typing import typeddict, maybe_none, to_json

import rethinkdb as r

Refund = typeddict(
    [ ('timestamp',     TimeStamp)
    , ('refundedItems', [model.RefundOrderItem])
    , ('reason',        maybe_none(str))
    ], name='Refund')

HistoryItem = typeddict(
    [ ('barID',   model.BarID)
    , ('orderID', model.OrderID)
    ], name='HistoryItem')

#=========================================================================#
# Queries / Feeds
#=========================================================================#

class OrderResult(ql.QuerySpec):
    args_spec = [
        ('order',           model.Order),
    ]
    result_spec = [
        ('errorMessage',    maybe_none(str)),
        ('orderID',         str),
        ('barID',           str),
        ('timestamp',       TimeStamp),
        ('userName',        UserName),

        # Receipt details
        ('queueSize',       int),
        # ('estimatedTime',   int),   # estimated time in seconds
        ('receipt',         Receipt),

        # Order details
        ('menuItems',       [model.MenuItemDef]),
        ('orderList',       [model.OrderItem]),
        ('totalAmount',     int),   # quantity (no. of total items ordered)
        ('totalPrice',      int),   # price in pence/cents
        ('tip',             int),
        ('currency',        model.Currency),

        # Delivery
        ('delivery',        model.DeliveryMethod),    # Table | Pickup
        ('tableNumber',     maybe_none(str)),
        ('pickupLocation',  maybe_none(str)),

        ('refunds',         [Refund]),
        # An order is completed when it is either fulfilled, or when it is fully
        # refunded
        ('completed',          bool),
        ('completedTimestamp', maybe_none(TimeStamp)),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        order = args['order']
        dt = order['timestamp']
        refunds = [convert_refund(refund) for refund in order.get('refunds', [])]
        completed_timestamp = order['completed_timestamp']
        if completed_timestamp:
            completed_timestamp = completed_timestamp.timestamp()
        return OrderResult.make(
            errorMessage    = order['errorMessage'],
            orderID         = order['id'],
            barID           = order['barID'],
            timestamp       = dt.timestamp(),
            # date            = Date(year=dt.year, day=dt.day, month=dt.month),
            # time            = Time(hour=dt.hour, minute=dt.minute, second=dt.second),
            # queueSize       = queueSize,
            # estimatedTime   = estimatedTime,
            totalAmount     = order['totalAmount'],
            totalPrice      = order['totalPrice'],
            tip             = order['tip'],
            currency        = order['currency'],
            receipt         = order['receipt'],
            userName        = order['userName'],
            orderList       = order['orderList'],

            delivery        = order['delivery'],
            tableNumber     = order['tableNumber'],
            pickupLocation  = order['pickupLocation'],

            refunds         = refunds,
            completed       = order['completed'],
            completedTimestamp = completed_timestamp,
            # delivered_timestamp       = order['delivered'],
        )

    @classmethod
    def resolve_menuItems(cls, result, args, result_fields):
        menuItemIDs = set(orderItem['menuItemID'] for orderItem in result['orderList'])
        # menuItems = model.get_menu_items(list(menuItemIDs))
        # return fmap(get_menu_item, menuItems)
        return fmap(find_item, menuItemIDs)

    # @classmethod
    # def resolve_queueSize(cls, result, args, result_fields):
    #     return model.get_bar_queue_size(result['barID'])

    # @classmethod
    # def resolve_estimatedTime(cls, result, args, result_fields):
    #     return 60 + model.get_drinks_queue_size(result['barID']) * 20


class OrderStatus(ql.QuerySpec):
    args_spec = [
        ('authToken',   str),
        ('orderID',     str),
    ]
    result_spec = [
        ('orderResult', OrderResult),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        userID = auth.validate_token(args['authToken'])
        order = model.get_order_by_id(userID, args['orderID'])
        order_result_spec = result_fields['orderResult']
        order_result = OrderResult.query({'order': order}, order_result_spec)
        return OrderStatus.make({'orderResult': order_result})

    @classmethod
    def feed(cls, args, result_fields):
        userID = auth.validate_token(args['authToken'])
        orderID = args['orderID']
        userID = auth.validate_token(args['authToken'])
        order_result_fields = result_fields['orderResult']
        with model.connect() as conn:
            changefeed = model.Orders           \
                .get(orderID)                   \
                .changes(include_initial=True)  \
                .run(conn)
            for result in changefeed:
                order = result['new_val']
                if order is None:
                    raise ValueError("Order not found!")
                if order['userID'] != userID:
                    raise ValueError("User does not own order")
                order_result = OrderResult.query({'order': order}, order_result_fields)
                yield OrderStatus.make({'orderResult': order_result})


class OrderHistory(ql.QuerySpec):
    args_spec = [
        ('authToken',   str),
        ('n',           int),
    ]
    result_spec = [
        ('orderHistory', [HistoryItem]),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        userID = auth.validate_token(args['authToken'])
        n      = int(args.get('n', 10))
        order_history = model.run(
            model.Orders.filter({'userID': userID})
                  .order_by(r.desc('timestamp'))
                  .pluck('id', 'barID')
                  .limit(n)
        )
        return OrderHistory.make({
            'orderHistory': [{'orderID': item['id'], 'barID': item['barID']}
                                for item in order_history],
        })


class ActiveOrders(ql.QuerySpec):
    """
    Active orders for a bar.
    """
    args_spec = [
        ('authToken',   str),
        ('barID',       str),
    ]
    result_spec = [
        ('orderResult', OrderResult),
    ]

    @classmethod
    def feed(cls, args, result_fields):
        userID = auth.validate_token(args['authToken'])
        barID  = args['barID']
        if not profile.is_bar_owner(userID, barID):
            raise ValueError("Not an admin for this bar")

        with model.connect() as conn:
            changefeed = model.Orders    \
                .filter({
                    'barID': barID,
                    'completed': False,
                })          \
                .changes()  \
                .run(conn)
            for result in changefeed:
                order = result['new_val']
                order_result = OrderResult.query({'order': order}, result_fields)
                yield ActiveOrders.make({'orderResult': order_result})

#=========================================================================#
# Mutations
#=========================================================================#

class PlaceOrder(ql.QuerySpec):
    args_spec = [
        ('barID',           ID),
        ('authToken',       str),
        ('userName',        str),
        ('currency',        model.Currency),
        ('price',           int),
        ('tip',             int),
        ('orderList',       [model.OrderItem]),
        ('stripeToken',     str),
        ('delivery',        model.DeliveryMethod),
        ('tableNumber',     maybe_none(str)),
        ('pickupLocation',  maybe_none(str)),
    ]
    result_spec = [
        ('orderID',         model.OrderID),
        ('orderResult',     OrderResult),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        now         = datetime.datetime.utcnow()
        barID       = args['barID']
        token       = args['authToken']
        userName    = args['userName']
        currency    = args['currency']
        price       = args['price']
        tip         = args['tip']
        orderList   = args['orderList']
        receipt     = shortid()
        totalAmount = sum(orderItem['amount'] for orderItem in orderList)

        delivery    = args['delivery']
        tableNumber = args['tableNumber'] or None
        pickupLocation = args['pickupLocation'] or None

        userID = auth.validate_token(token)

        if tableNumber is None and pickupLocation is None:
            raise ValueError("Require either table number or pickup location")
        if tip < 0:
            raise ValueError("Tip must be positive, got %r" % (tip,))

        # TODO: Payment with Stripe
        # TODO: Verify barID and bar opening time
        # TODO: Verify 'price'
        # TODO: Verify pickup location

        order = model.Order(
            errorMessage=None,

            barID=barID,
            timestamp=now,
            userID=userID,
            userName=userName,
            totalAmount=totalAmount,
            totalPrice=price,
            tip=tip,
            currency=currency,
            orderList=orderList,
            receipt=receipt,

            delivery=delivery,
            tableNumber=tableNumber,
            pickupLocation=pickupLocation,

            completed = False,
            completed_timestamp = None,
        )
        orderID = model.submit_order(order)
        order['id'] = orderID
        # order_result = OrderResult.query({'order': order}, result_fields['orderResult'])
        messaging.send_message_async(userID, messaging.Message({
            'title':     'Order Placed Successfully',
            'content':   'Successfully placed an order',
            'timestamp': now.timestamp(),
            'priority':  'high',
        }), media=['Push', 'InApp'])
        return PlaceOrder.make({
            'orderID': orderID,
        })

    @classmethod
    def resolve_orderResult(cls, result, args, result_fields):
        order = model.run(model.Orders.get(result['orderID']))
        return OrderResult.query({'order': order}, result_fields)


class RefundOrder(ql.QuerySpec):
    args_spec = [
        # Auth token from bar
        ('authToken', str),
        ('barID',     str),
        ('orderID',   str),
        ('refundItems', [model.RefundOrderItem]),
        ('reason',    maybe_none(str))
    ]
    result_spec = [
        ('status', str),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        now     = datetime.datetime.utcnow()
        userID  = auth.validate_token(args['authToken'])
        barID   = args['barID']
        orderID = args['orderID']

        if not profile.is_bar_owner(userID, barID):
            raise ValueError("Not an administrator for this bar")
        order = model.run(model.Orders.get(orderID))
        if order is None:
            raise ValueError("Order not found")
        if order['barID'] != barID:
            raise ValueError("Bar ID does not match bar ID of order!")

        # Verify that the refunded amount does not exceed the total amount
        refund = {
            'timestamp':     r.epoch_time(now.timestamp()),
            'refundedItems': args['refundItems'],
            'reason':        args['reason'],
        }

        orderList = order['orderList']
        refunds = order.get('refunds', [])
        refunds.append(refund)
        validate_order_list(orderList, refunds)

        # TODO: Calculate refund price
        # TODO: Process payment

        total_amount = sum(orderItem['amount'] for orderItem in orderList)
        if order['completed']:
            completed = True
            completed_timestamp = order['completed_timestamp']
        else:
            completed = total_amount == 0
            completed_timestamp = now.timestamp() if completed else None

        # Record refund as part of Order
        model.run(
            model.Orders
                .get(orderID)
                .update({
                    'refunds':     r.row['refunds'].default([]).append(refund),
                    'totalAmount': total_amount,
                    'completed':   completed,
                    'completed_timestamp': completed_timestamp,
                })
        )

        return RefundOrder.make({
            'status': 'OK',
        })


class CompleteOrder(ql.QuerySpec):
    args_spec = [
        # Auth token from bar
        ('authToken', str),
        ('orderID',   str),
    ]
    result_spec = [
        ('status', str),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        now     = datetime.datetime.utcnow()
        userID  = auth.validate_token(args['authToken'])
        orderID = args['orderID']

        order = model.run(model.Orders.get(orderID))

        if not profile.is_bar_owner(userID, order['barID']):
            raise ValueError("Not an administrator for this bar")

        # TODO: Adjust estimated time for subsequent orders?

        if order['delivery'] == model.DeliveryMethod.Table:
            message = (
                "Wooh! Your order will be delivered to your table shortly."
            )
        else:
            location = order['pickupLocation']
            message = (
                "Yaay! Your order is available for pickup (location: %s)!" % (location,)
            )

        messaging.send_message(
            order['userID'],
            message = messaging.Message({
                'title':     'Your order is ready!',
                'content':   message,
                'timestamp': now.timestamp(),
                'priority':  'high',
            }),
            media = ['Push', 'InApp'],
        )

        model.upsert(model.Orders, {
            'id': orderID,
            'completed': True,
            'completed_timestamp': r.epoch_time(now.timestamp()),
        })

        return CompleteOrder.make({
            'status': 'OK',
        })


def validate_order_list(order_list : [model.OrderItem], refunds : [model.Refund]):
    """
    Normalize the order list.

    WARNING: mutates order_list in-place.
    """
    for refund in refunds:
        for refund_order_item in refund['refundedItems']:
            for order_item in order_list:
                if refund_order_item['id'] == order_item['id']:
                    order_item['amount'] -= refund_order_item['amount']
                    if order_item['amount'] < 0:
                        raise ValueError("Refunded amount exceeds paid amount")
                    break
            else:
                raise ValueError("Refunded order item not found...")


def find_item(menuItemID : ID):
    [item] = [item for item in menu.items if item['id'] == menuItemID]
    return item

def convert_refund(refund : model.Refund) -> Refund:
    return dict(refund, {
        'timestamp': refund['timestamp'].timestamp(),
    })

#=========================================================================#
# Register
#=========================================================================#

def register(dispatcher):
    dispatcher.register(PlaceOrder)
    dispatcher.register(OrderStatus)
    dispatcher.register(OrderHistory)
    dispatcher.register(CompleteOrder)
    dispatcher.register(RefundOrder)
