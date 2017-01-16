import datetime
import rethinkdb as r
from curry.typing import validate, alias, typeddict, URL, maybe_none, optional, enum
from curry.task import ConnectionPool

#===------------------------------------------------------------------===
# Tables
#===------------------------------------------------------------------===

# def connect():
#     host = 'gcp-europe-west1-cpu.0.dblayer.com'
#     port = 15170
#     username = 'admin'
#     pwd = 'kpghpkNAwRYMf8140OEkQBGwL0fUrcboeZcUxHG28us'
#     # pwd = 'XbH4a4.@/D,WzdJ)pE(fkDu)d2[g$De[}Ze4ExSPN5y(!*_7Eh'
#     return r.connect(
#         host=host,
#         port=port,
#         user=username,
#         password=pwd,
#         ssl={'ca_certs': 'rethink.crt'},
#         )

connect = r.connect

def make_pool(connect):
    "Create a Greenlet-based connection pool"
    return ConnectionPool(
        connect_func  = connect,
        is_alive_func = lambda conn: True,
        close_func    = lambda conn: conn.close(),
    )

def setup_testing_mode():
    global connect
    connect = r.connect
    setup_pool()

def setup_pool():
    global pool, _conn
    _conn = connect()
    pool = make_pool(connect)

setup_pool()


MenuItemDefs    = r.db('qdodger').table('MenuItemDefs')
Orders          = r.db('qdodger').table('Orders')
MenuItems       = r.db('qdodger').table('MenuItems')
UserProfiles    = r.db('qdodger').table('UserProfiles')
Bars            = r.db('qdodger').table('Bars')

#===------------------------------------------------------------------===
# Types
#===------------------------------------------------------------------===

ID              = alias('ID', str)
PlaceID         = ID        # google maps PlaceID
UserID          = ID
BarID           = PlaceID   # uniquely identifies a bar, same as place id
MenuItemDefID   = alias('MenuItemDefID', ID)
MenuItemID      = alias('MenuItemID', ID)
OrderID         = ID
OrderItemID     = ID

BarName = alias('BarName', str)


UserProfile = typeddict(
    [ ('id', UserID)
    , ('is_bar_owner', bool)
    , ('bars', [BarID])
    , ('email', str)
    , ('firebase_token', str)
    ], name='UserProfile')

TableService = enum('TableService', [
    'Disabled',
    'Food',
    'Drinks',
    'FoodAndDrinks',
])

HappyHour = enum('HappyHour', [
    'TwoForOne',
    'Discount',
])

PickupLocation = typeddict(
    [ ('open', bool)
    , ('list_position', int)
    ], name='PickupLocation')

BarStatus = typeddict(
    [ ('id',                        BarID)
    , ('qdodger_bar',               bool)
    , ('taking_orders',             bool)
    , ('table_service',             TableService)
    # , ('table_service_min_price',   int)    # in pence/cents
    , ('pickup_locations',          {str: PickupLocation})
    # , ('happy_hour',                HappyHour)
    # , ('hh_discount',               int)    # discount in %
    ], name='BarStatus')

TagName = alias('TagName', str)

OptionType = enum('OptionType', [
    'Single',
    'AtMostOne',
    'ZeroOrMore',
    'OneOrMore',
])

Currency = enum('Currency', [
    'Sterling',
    'Euros',
    'Dollars',
])

PriceOption = enum('PriceOption', [
    'Absolute',
    'Relative',
])

Price = typeddict(
    [ ('currency', Currency)
    , ('option', PriceOption)
    , ('price', int) # in cents/pence
    ], name='Price')

MenuItemOption = typeddict(
    [ ('id',            ID)
    , ('name',          str)
    , ('optionType',    OptionType)
    , ('optionList',    [str])
    , ('prices',        [Price])
    , ('defaultOption', maybe_none(int))
    ], name='MenuItemOption')

MenuItemDef = typeddict(
    [ ('id',        str)
    , ('name',      str)
    , ('desc',      maybe_none(str))
    , ('images',    [URL])
    # Alcohol percentage
    , ('abv',       optional(maybe_none(str)))
    # Year (e.g. for wines)
    , ('year',      optional(maybe_none(int)))
    , ('tags',      [TagName])
    , ('price',     Price) # TODO: Remove
    , ('optionsID', optional(ID))
    , ('options',   optional([MenuItemOption]))
    ], name='MenuItemDef')

MenuItem = typeddict(
    [ ('id',      MenuItemID)
    , ('itemDef', MenuItemDefID)
    , ('barID',   BarID)
    , ('options', [MenuItemOption])
    # Field overrides
    # TODO: tags, images, abv, year, etc
    ], name='MenuItem')

#-----------------------------------------------------------------------#

OrderItem = typeddict(
    [ ('id',                OrderItemID)
    , ('menuItemID',        MenuItemID)
    , ('selectedOptions',   [[str]])
    , ('amount',            int)
    ], name='OrderItem')

DeliveryMethod = enum('DeliveryMethod', [
    'Table',
    'Pickup',
])

RefundOrderItem = typeddict(
    [ ('id',                OrderItemID)
    , ('amount',            int)
    ], name='RefundOrderItem')

Refund = typeddict(
    [ ('timestamp',         datetime.datetime)
    , ('refundedItems',    [RefundOrderItem])
    , ('reason',           maybe_none(str))
    ], name='Refund')

Order = typeddict(
    [ ('id',                OrderID)
    , ('barID',             BarID)
    , ('timestamp',         datetime.datetime)
    , ('userID',            str)
    , ('userName',          str)
    , ('totalAmount',       int) # total number of drinks
    , ('totalPrice',        int) # total price (in cents)
    , ('tip',               int) # total tip (in cents)
    , ('currency',          Currency)
    , ('orderList',         [OrderItem])
    , ('receipt',           maybe_none(str))

    , ('delivery',          DeliveryMethod)
    , ('tableNumber',       maybe_none(str))
    , ('pickupLocation',    maybe_none(str))

    , ('refunds',           [Refund])

    # An order is completed when it is either fulfilled, or when it is fully
    # refunded
    , ('completed',           bool)
    , ('completed_timestamp', maybe_none(datetime.datetime))

    , ('errorMessage',        maybe_none(str))
    ], name='Order')

#===------------------------------------------------------------------===
# Actions
#===------------------------------------------------------------------===

def run(query):
    with connect() as conn:
        return query.run(conn)

def upsert(table, value):
    run(table.insert(value, conflict='update'))

def get_item_defs() -> [MenuItemDef]:
    return list(run(MenuItemDefs))

def get_active_menu_items(barID):
    return get_item_defs()
    # TODO:
    # return run(MenuItems.filter({'barID': barID, 'isActive': True}))

def submit_order(order : Order) -> ID:
    validate(order, Order)
    order = dict(order, timestamp=r.epoch_time(order['timestamp'].timestamp()))
    result = run(Orders.insert(order, conflict="error"))
    if result['inserted'] != 1:
        raise ValueError("Error submitting order")
    [orderID] = result['generated_keys']
    return orderID

def get_order_by_id(userID, orderID):
    order = run(Orders.get(orderID))
    if order is None:
        raise ValueError("Order not found")
    if order['userID'] != userID:
        raise ValueError("Invalid user ID")
    return order

def get_drinks_queue_size(barID) -> int:
    return run(
        Orders.filter({'completed': False})['totalAmount'].sum()
    )

def get_bar_queue_size(barID) -> int:
    return run(
        Orders.filter({'completed': False}).count()
    )

def get_menu_items(menuItemIDs : [MenuItemID]) -> [MenuItem]:
    table = MenuItemDefs # TODO: use MenuItems
    return run(table.get_all(*menuItemIDs))
