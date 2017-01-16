from curry import typeddict, alias, enum, optional
from qdserver.model import ID

DeepLink = alias('DeepLink', str)

Priority = enum('Priority', [
    'normal',
    'high',
])

AboutType = enum('AboutType', [
    'Bar',
    'Order',
    'Booking',
])

Message = typeddict(
    [ ('messageID',   ID)
    , ('timestamp',   float)
    , ('title',       optional(str))
    , ('content',     str)
    , ('priority',    Priority)
    , ('aboutType',   AboutType)
    , ('aboutID',     ID)
    , ('deepLink',    DeepLink)
    , ('flash',       bool)
    , ('vibrate',     bool)
    , ('sound',       bool)
    , ('popup',       bool)
    , ('topic',       optional(ID))
    , ('buttonLabel', optional(str))
    ], name='Message')

Medium = enum('Medium', ['Push', 'Email', 'InApp'])
Media  = alias('Media', [Medium])
