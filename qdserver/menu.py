import random
from qdserver import model, ql, domain
from qdserver.common import ID
from curry.typing import URL

#=========================================================================#
# Menu Item Definitions
#=========================================================================#

class SubMenu(ql.QuerySpec):
    result_spec = [
        ('image',       URL),
        ('menuItems',   [model.MenuItemDef]),
    ]

class Menu(ql.QuerySpec):
    args_spec = [
        ('barID', ID),
    ]
    result_spec = [
        ('barID',     ID),
        ('beer',      SubMenu),
        ('wine',      SubMenu),
        ('spirits',   SubMenu),
        ('cocktails', SubMenu),
        ('water',     SubMenu),
        ('snacks',    SubMenu),
        ('food',      SubMenu),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        # raise ValueError('tee hee')
        return makeMenu(args['barID'])


def makeMenu(barID):
    return Menu.make(
        barID=barID,
        beer=SubMenu.make(
            image=beer,
            menuItems=[model.MenuItemDef(**item) for item in get_items() if '#beer' in item['tags']],
        ),
        wine=SubMenu.make(
            image=wine,
            menuItems=[model.MenuItemDef(**item) for item in get_items() if '#wine' in item['tags']],
        ),
        spirits=SubMenu.make(
            image=spirits,
            menuItems=[model.MenuItemDef(**item) for item in get_items() if '#spirit' in item['tags']],
        ),
        cocktails=SubMenu.make(
            image=cocktails,
            menuItems=[model.MenuItemDef(**item) for item in get_items() if '#cocktail' in item['tags']],
        ),
        water=SubMenu.make(
            image=water,
            menuItems=[model.MenuItemDef(**item) for item in get_items() if '#water' in item['tags']],
        ),
        snacks=SubMenu.make(
            image=snacks,
            menuItems=[model.MenuItemDef(**item) for item in get_items() if '#snack' in item['tags']],
        ),
        food=SubMenu.make(
            image=food,
            menuItems=[model.MenuItemDef(**item) for item in get_items() if '#food' in item['tags']],
        ),
    )

beer      = domain + "/static/beer1-medium.jpg"
wine      = domain + "/static/wine1-medium.jpg"
spirits   = domain + "/static/spirit1-medium.jpg"
cocktails = domain + "/static/cocktails1-medium.jpg"
water     = domain + "/static/water-medium.jpg"
food      = domain + "/static/food1-medium.jpg"
snacks    = domain + "/static/snacks1-medium.jpg"

#=========================================================================#
# Menu Options
#=========================================================================#

def pounds(price, option = model.PriceOption.Relative):
    return dict(
        currency = model.Currency.Sterling,
        option   = option,
        price    = price,
    )

zero     = pounds(0)
fiftyP   = pounds(50)
onePound = pounds(100)

beer_top_options = model.MenuItemOption(
    name="Options",
    optionType=model.OptionType.AtMostOne,
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

spirit_top_options = model.MenuItemOption(
    name="Options",
    optionType=model.OptionType.AtMostOne,
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
    return model.MenuItemOption(
        name="Choose",
        optionType=model.OptionType.Single,
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
    return model.MenuItemOption(
        name="Choose",
        optionType=model.OptionType.Single,
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
    return model.MenuItemOption(
        name="Choose",
        optionType=model.OptionType.Single,
        optionList=[
            "single",
            "double",
        ],
        prices=[single, double],
        defaultOption=0,
    )

def generate_decreasing(lower_bounds, max_price):
    upper = max_price
    for lower in lower_bounds:
        price = random.choice(generate_prices(lower, upper))
        yield price
        upper = price['price']

def generate_prices(lower, upper):
    prices = [lower + 10 * i for i in range(int((upper - lower) / 10))]
    return [pounds(price, option=model.PriceOption.Absolute) for price in prices]


def update_items(items):
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

        elif '#spirit' in item['tags'] or '#cocktail' in item['tags']:
            double, single = generate_decreasing([420, 310], 910)
            item['price'] = single
            item['options'] = [ spirit_options(single, double), spirit_top_options ]

        elif '#water' in item['tags']:
            item['price'] = pounds(0)
            item['options'] = []

items = None

def get_items():
    global items
    if items is None:
        items = model.get_item_defs() # [model.MenuItemDef]
        update_items(items)
    return items

#=========================================================================#
# Dispatch
#=========================================================================#

def register(dispatcher):
    dispatcher.register(Menu)
