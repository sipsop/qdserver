# from collections import OrderedDict

# from graphql.execution.executor import Executor
# from graphql.execution.middlewares.gevent import GeventExecutionMiddleware, run_in_greenlet
from graphql.execution.executors.gevent import GeventExecutor #, run_in_greenlet

import yaml
import datetime
import inspect
import string
import random
import graphene
import traceback

from qdserver import auth, model
from curry import fmap

items = model.get_item_defs()

GRAPHENE_TYPES = (
    graphene.ObjectType,
    graphene.Enum,
    graphene.InputObjectType,
)

def nonNull(ty):
    if inspect.isclass(ty) and issubclass(ty, GRAPHENE_TYPES):
        return graphene.Field(ty)
    return ty

    # For some reason this is broken...
    if inspect.isclass(ty) and issubclass(ty, GRAPHENE_TYPES):
        return graphene.NonNull(graphene.Field(ty))
    return graphene.NonNull(ty)

# Must duplicate fields, graphene is stupidly mutating stuff and scrambling data
String      = lambda: nonNull(graphene.String())
NullString  = lambda: graphene.String()
Int         = lambda: nonNull(graphene.Int())
NullInt     = lambda: graphene.Int()
Float       = lambda: nonNull(graphene.Float())

def List(ty):
    return nonNull(graphene.List(ty))

# ID  = graphene.ID().NonNull
ID          = lambda: String()
BarID       = lambda: ID()
MenuItemID  = lambda: ID()
URL         = lambda: String()


#=========================================================================#
# Stupid graphene murders your fields

# Currency
Sterling = 0
Euros    = 1
Dollars  = 2

# PriceOption
Absolute = 0
Relative = 1

# OptionType
Single      = 0
AtMostOne   = 1
ZeroOrMore  = 2
OneOrMore   = 3



#=========================================================================#

outsideURL = "http://blog.laterooms.com/wp-content/uploads/2014/01/The-Eagle-Cambridge.jpg"
insideURL = "http://www.vintagewings.ca/Portals/0/Vintage_Stories/News%20Stories%20L/EaglePubRedux/Eagle14.jpg"

class Drink(graphene.ObjectType):
    id = ID()
    name = String()
    desc = NullString()
    images = graphene.List(URL())
    tags = List(String())

class Currency(graphene.Enum):
    Sterling = Sterling
    Euros    = Euros
    Dollars  = Dollars

class PriceOption(graphene.Enum):
    Absolute = Absolute    # absolute price, e.g. 3.40
    Relative = Relative    # relative price, e.g. +0.50 (for add-ons)

class Price(graphene.ObjectType):
    currency = graphene.Field(Currency)
    option = graphene.Field(PriceOption)
    price = Float()

    @classmethod
    def pounds(cls, price, option=Absolute):
        return Price(
            currency=Sterling,
            option=option,
            price=price)

    @classmethod
    def euros(cls, price):
        return Price(
            currency=Euros,
            option=Absolute,
            price=price)

    @classmethod
    def dollars(cls, price):
        return Price(
            currency=Dollars,
            option=Absolute,
            price=price)

class OptionType(graphene.Enum):
    Single     = Single
    AtMostOne  = AtMostOne
    ZeroOrMore = ZeroOrMore
    OneOrMore  = OneOrMore


class MenuItemOption(graphene.ObjectType):
    id = ID()
    # menu option name (e.g. "Size")
    name    = String()

    # type of option list
    optionType = nonNull(OptionType)

    # List of options to choose from, e.g. ["pint", "half-pint"]
    optionList = List(String())

    # List of prices for each option, e.g. [Price(3.40), Price(2.60)]
    prices  = List(Price)

    # Index of the default option. If there is no default, this is null
    # (only allowed when optionType == 'ZeroOrMore' or 'ZeroOrOne')
    defaultOption = NullInt()

class MenuItem(graphene.ObjectType):
    id      = ID()
    name    = String()
    desc    = NullString()
    images  = List(URL())
    tags    = List(String())
    price   = nonNull(Price)
    options = List(MenuItemOption)


class SubMenu(graphene.ObjectType):
    image     = URL()
    menuItems = List(MenuItem)

class Menu(graphene.ObjectType):
    placeID   = ID()
    beer      = nonNull(SubMenu)
    wine      = nonNull(SubMenu)
    spirits   = nonNull(SubMenu)
    cocktails = nonNull(SubMenu)
    water     = nonNull(SubMenu)

class Day(graphene.Enum):
    Sunday    = 0
    Monday    = 1
    Tuesday   = 2
    Wednesday = 3
    Thursday  = 4
    Friday    = 5
    Saturday  = 6

class Date(graphene.ObjectType):
    year    = Int()
    month   = Int()
    day     = Int()

class Time(graphene.ObjectType):
    hour    = NullInt()
    minute  = NullInt()
    second  = NullInt()

class OpeningTime(graphene.ObjectType):
    # day = graphene.NonNull(Day)
    openTime = graphene.Field(Time)
    closeTime = graphene.Field(Time)

class Address(graphene.ObjectType):
    lat      = Float()
    lon      = Float()
    city     = String()
    street   = String()
    number   = String()
    postcode = String()

class BarType(graphene.Enum):
    Pub = 0
    Club = 1

# class Bar(graphene.ObjectType):
#     id     = ID
#     name   = String
#     desc   = graphene.String()
#     barType = graphene.NonNull(BarType)
#     signedUp = graphene.Boolean().NonNull
#     images = graphene.List(URL).NonNull
#     tags   = graphene.List(String)
#     phone  = graphene.String()
#     website = graphene.String()
#     openingTimes = graphene.List(OpeningTime).NonNull
#     address = graphene.NonNull(Address)
    # menu   = graphene.Field(Menu)

    # def resolve_menu(self, args, info):
    #     return menu

class TagInfo(graphene.ObjectType):
    tagID    = String()
    tagName  = String()
    excludes = List(ID())

class TagEdge(graphene.ObjectType):
    srcID  = String()
    dstIDs = List(String())

class Tags(graphene.ObjectType):
    tagInfo  = List(TagInfo)
    tagGraph = List(TagEdge)

def parse_tags(yaml_file):
    tags_yaml = yaml.load(yaml_file)
    groups = tags_yaml['tags']['groups']
    edges  = tags_yaml['tags']['edges']

    def resolve_tags(category):
        if category in categories:
            return categories[category]
        return ['#' + category] # category is a tag, e.g. 'beer'

    categories = {category: tags.split() for category, tags in groups.items()}
    tagGraph = []
    tagInfo  = []
    for category, children_str in edges.items():
        src_tags = resolve_tags(category)
        dst_tags = [ tag for child in children_str.split()
                             for tag in resolve_tags(child) ]
        for src_tag in src_tags:
            tagGraph.append(TagEdge(srcID=src_tag, dstIDs=dst_tags))

    for tags in categories.values():
        for tag in tags:
            excludes = list(tags)
            excludes.remove(tag)
            tagInfo.append(TagInfo(tagID=tag, tagName=tag, excludes=excludes))

    return Tags(tagInfo=tagInfo, tagGraph=tagGraph)

menuTags = parse_tags(open('Tags.yaml'))

eagleID = 'ChIJuQdxBb1w2EcRvnxVeL5abUw'

beer = "http://www.menshealth.com/sites/menshealth.com/files/styles/slideshow-desktop/public/images/slideshow2/beer-intro.jpg?itok=hhBQBwWj"
wine = "https://employee.foxandhound.com/Portals/0/images/slideshow/wine-pour-slide2.jpg"
spirits = "https://biotechinasia.files.wordpress.com/2015/10/two-whisky-glasses.jpg"
cocktails = "http://notable.ca/wp-content/uploads/2015/06/canada-day-cocktails.jpg"
water = "http://arogyam.zest.md/uploads/gallery/df4fe8a8bcd5c95cdb640aa9793bb32b/images/201212042159565.jpg"
snacks = "https://www.google.co.uk/search?q=peanuts&client=ubuntu&hs=sBq&source=lnms&tbm=isch&sa=X&ved=0ahUKEwiT_47KnLnOAhXJuRoKHaNqD7QQ_AUICCgB&biw=1920&bih=919#tbm=isch&q=snacks&imgrc=sjXgiZ2yIgbsCM%3A"

guiness = "https://i.kinja-img.com/gawker-media/image/upload/s--neYeJnUZ--/c_fit,fl_progressive,q_80,w_636/zjlpotk0twzrtockzipu.jpg"
heineken = "https://upload.wikimedia.org/wikipedia/commons/a/ad/Heineken_lager_beer_made_in_China.jpg"
rockBottom = "http://3.bp.blogspot.com/_R8IDaEfZhDs/SwPlVIClDwI/AAAAAAAAA9M/UrPntmIjnA4/s1600/PB170236.JPG"

Relative = 1
zero     = Price.pounds(0.0, Relative)
fiftyP   = Price.pounds(50,  Relative)
onePound = Price.pounds(100, Relative)

beer_top_options = MenuItemOption(
    name="Options",
    optionType=AtMostOne,
    optionList=[
        "tops (lemonade)",
        "shandy",
        "lime",
        "blackcurrant",
    ], #+ ["x%d" % i for i in range(100)],
    prices=[
        zero,
        zero,
        fiftyP,
        zero,
    ], #+ [zero] * 100,
    defaultOption=None,
)

spirit_top_options = MenuItemOption(
    name="Options",
    optionType=AtMostOne,
    optionList=[
        "Coke",
        "Redbull",
        "etc",
    ],
    prices=[
        fiftyP,
        onePound,
        zero,
    ],
    defaultOption=None,
)
#============================================================================#

def beer_option(price1, price2):
    return MenuItemOption(
        name="Choose",
        optionType=Single,
        optionList=[
            "pint",
            "half-pint",
        ],
        prices=[
            price1, price2
        ],
        defaultOption=0,
    )

def wine_options(small, medium, large, bottle):
    return MenuItemOption(
        name="Choose",
        optionType=Single,
        optionList=[
            "small glass",
            "medium glass",
            "large glass",
            "bottle",
        ],
        prices=[small, medium, large, bottle],
        defaultOption=1,
    )

def spirit_options(single, double):
    return MenuItemOption(
        name="Choose",
        optionType=Single,
        optionList=[
            "single",
            "double",
        ],
        prices=[single, double],
        defaultOption=0,
    )

#= Price Generation ========================================================#

def generate_decreasing(lower_bounds, max_price):
    upper = max_price
    for lower in lower_bounds:
        price = random.choice(generate_prices(lower, upper))
        yield price
        upper = price.price


def generate_prices(lower, upper):
    prices = [lower + 10 * i for i in range(int((upper - lower) / 10))]
    return [Price.pounds(price) for price in prices]

#= Menu =====================================================================#

for item in items:
    if '#beer' in item['tags']:
        price1, price2 = generate_decreasing([220, 170], 650)
        item['price']   = price1
        item['options'] = [ beer_option(price1, price2), beer_top_options ]

    elif '#wine' in item['tags']:
        bottle, large, medium, small = generate_decreasing(
            [850, 420, 320, 270], 2300)
        item['price']   = medium
        item['options'] = [ wine_options(small, medium, large, bottle) ]

    elif '#spirit' in item['tags']:
        double, single = generate_decreasing([420, 310], 910)
        item['price'] = single
        item['options'] = [ spirit_options(single, double), spirit_top_options ]

def makeMenu(placeID):
    return Menu(
        placeID=placeID,
        beer=SubMenu(
            image=beer,
            menuItems=[MenuItem(**item) for item in items if '#beer' in item['tags']],
        ),
        wine=SubMenu(
            image=wine,
            menuItems=[MenuItem(**item) for item in items if '#wine' in item['tags']],
        ),
        spirits=SubMenu(
            image=spirits,
            menuItems=[MenuItem(**item) for item in items if '#spirit' in item['tags']],
        ),
        cocktails=SubMenu(
            image=cocktails,
            menuItems=[],
        ),
        water=SubMenu(
            image=water,
            menuItems=[],
        ),
        # snacks=SubMenu(
        #     image=snacks,
        # ),
    )


############################################################################
# Mutation
############################################################################

class OrderItem(graphene.ObjectType):
    # barID = BarID
    id = ID()
    menuItemID = MenuItemID()
    # e.g. [['pint'], ['lime']]
    selectedOptions = List(List(graphene.String()))
    amount = Int()

# For inputs you have to use 'InputObjectType' for some reason...
# http://stackoverflow.com/questions/32304486/how-to-make-a-mutation-query-for-inserting-a-list-of-array-fields-in-graphql
class OrderItemInput(graphene.InputObjectType):
    # barID = BarID
    # ID of the OrderItem
    id = ID()
    menuItemID = MenuItemID()
    # e.g. [['pint'], ['lime']]
    selectedOptions = List(List(String()))
    amount = Int()


characters = string.ascii_letters + '0123456789!?@*$+/|'

def shortid():
    return ''.join(random.sample(characters, 3))

# class PlaceOrder(graphene.Mutation):
#     class Input:
#         barID       = String
#         userName    = String
#         currency    = String
#         price       = Float
#         orderList   = List(OrderItemInput)
#         stripeToken = String

class OrderResult(graphene.ObjectType):
    errorMessage    = NullString()
    barID           = String()
    date            = graphene.Field(Date)
    time            = graphene.Field(Time)
    queueSize       = Int()
    estimatedTime   = Int()
    receipt         = String()
    userName        = String()
    menuItems       = List(MenuItem)
    orderList       = List(OrderItem)
    totalAmount     = Int()
    totalPrice      = Int()
    tip             = Int()
    currency        = graphene.Field(Currency)

    delivery        = String()
    tableNumber     = graphene.String()
    pickupLocation  = graphene.String()

    def resolve_menuItems(self, args, *_):
        menuItemIDs = set(orderItem.menuItemID for orderItem in self.orderList)
        # menuItems = model.get_menu_items(list(menuItemIDs))
        # return fmap(get_menu_item, menuItems)
        return fmap(find_item, menuItemIDs)

def find_item(menuItemID : model.MenuItemID):
    [item] = [item for item in items if item['id'] == menuItemID]
    return MenuItem(**item)

class OrderHistory(graphene.ObjectType):
    orderHistory    = List(OrderResult)

class Query(graphene.ObjectType):

    # bar  = graphene.Field(Bar, id=ID)
    barListTags = graphene.Field(Tags)
    menuTags = graphene.Field(Tags)
    menu = graphene.Field(Menu, placeID=ID())

    placeOrder = graphene.Field(OrderResult,
        barID       = String(),
        token       = String(),
        userName    = String(),
        currency    = String(),
        price       = Int(),
        tip         = Int(),
        orderList   = List(OrderItemInput),
        stripeToken = String(),
        delivery    = String(),
        tableNumber = String(),    # optional table number
        pickupLocation = String(), # optional label of pickup point
        )

    recentOrders = graphene.Field(OrderHistory,
        token       = String(),
        n           = NullInt(),
        )

    def resolve_menu(self, args, *_):
        placeID = args['placeID']
        return makeMenu(placeID)

    def resolve_menuTags(self, args, *_):
        return menuTags

    def resolve_placeOrder(self, args, *_):
        try:
            return _resolve_placeOrder(self, args, *_)
        except:
            traceback.print_exc()

    def resolve_recentOrders(self, args, *_):
        userID = auth.validate_token(args['token'])
        n      = int(args.get('n', 10))
        orders = model.get_order_history(userID, n)
        return OrderHistory(orderHistory=fmap(get_order_result, orders))


def _resolve_placeOrder(self, args, *_):
    print("PLACING ORDER!")

    now         = datetime.datetime.utcnow()
    barID       = args['barID']
    token       = args['token']
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
    if delivery not in ('Table', 'Pickup'):
        raise ValueError("Invalid delivery specified: %r" % (delivery,))
    if tableNumber is None and pickupLocation is None:
        raise ValueError("Require eitehr table number or pickup location")
    if currency not in ['Sterling', 'Euros', 'Dollars']:
        raise ValueError("Unknown currency: %r" % (currency,))
    if tip < 0:
        raise ValueError("Tip must be positive, got %r" % (tip,))

    currency = getattr(model.Currency, currency)

    # TODO: Payment with Stripe
    # TODO: Verify barID and bar opening time
    # TODO: Verify 'price'
    # TODO: Verify pickup location

    order = model.Order(
        barID=barID,
        utcstamp=now,
        userID=userID,
        userName=userName,
        totalAmount=totalAmount,
        totalPrice=price,
        tip=tip,
        currency=currency,
        orderList=orderList,
        receipt=receipt,

        delivery=getattr(model.DeliveryMethod, delivery),
        tableNumber=tableNumber,
        pickupLocation=pickupLocation,

        completed=False,
        errorMessage=None,
    )
    model.submit_order(order)

    queueSize = model.get_bar_queue_size(barID)
    estimatedTime = 60 + model.get_drinks_queue_size(barID) * 20

    return get_order_result(
        order,
        queueSize     = queueSize,
        estimatedTime = estimatedTime
        )


def get_order_result(
        order : model.Order,
        queueSize=0,
        estimatedTime=0
        ) -> [OrderResult]:
    dt = order['utcstamp']

    return OrderResult(
        errorMessage    = order['errorMessage'],
        barID           = order['barID'],
        date            = Date(year=dt.year, day=dt.day, month=dt.month),
        time            = Time(hour=dt.hour, minute=dt.minute, second=dt.second),
        queueSize       = queueSize,
        estimatedTime   = estimatedTime,
        totalAmount     = order['totalAmount'],
        totalPrice      = order['totalPrice'],
        tip             = order['tip'],
        currency        = get_currency(order['currency']),
        receipt         = order['receipt'],
        userName        = order['userName'],
        orderList       = fmap(get_order_item, order['orderList']),

        delivery        = get_delivery(order['delivery']),
        tableNumber     = order['tableNumber'],
        pickupLocation  = order['pickupLocation'],
    )

_currencies = {
    model.Currency.Sterling: Sterling,
    model.Currency.Dollars:  Dollars,
    model.Currency.Euros:    Euros,
}

def get_delivery(delivery : model.DeliveryMethod) -> str:
    if delivery == model.DeliveryMethod.Table:
        return 'Table'
    return 'Pickup'

def get_currency(currency : model.Currency) -> Currency:
    return _currencies[currency]

def get_order_item(order_item : model.OrderItem) -> OrderItem:
    return OrderItem(**order_item)

def get_menu_item(menu_item : model.MenuItem) -> MenuItem:
    menu_item = dict(
        menu_item,
        price   = get_price(menu_item['price']),
        options = get_options(menu_item['options']),
    )
    return MenuItem(**menu_item)

schema = graphene.Schema(query=Query, executor=GeventExecutor())


if __name__ == '__main__':
    from flask import Flask, send_from_directory
    from flask_graphql import GraphQLView
    # from qdserver import app # This breaks for some reason...
    import qdserver.routes
    import qdweb.routes

    app = Flask(__name__)

    app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))
    qdserver.routes.setup_routes(app)
    qdweb.routes.setup_routes(app)

    app.run(host='0.0.0.0', port=9000)
