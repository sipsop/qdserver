from qdserver import ql, model, auth, profile
from qdserver.common import ID
import rethinkdb as r

from curry import typeddict

PickupLocation = typeddict(
    [ ('name', str)
    , ('open', bool)
    ], name='PickupLocation')

AddBar = typeddict(
    [ ('name', model.BarName)
    , ('listPosition', int)
    ], name='AddBar')

SetBarOpen = typeddict(
    [ ('name', model.BarName)
    , ('open', bool)
    ], name='SetBarOpen')

# TODO: Support DataType
StatusUpdate = typeddict(
    [ ('TakingOrders',          bool)
    , ('SetTableService',       model.TableService)
    , ('AddBar',                AddBar)
    , ('SetBarOpen',            SetBarOpen)
    ], name='StatusUpdate')

BarStatusResult = typeddict(
    [ ('barID',               model.BarID)
    , ('qdodger_bar',         bool)
    , ('taking_orders',       bool)
    , ('table_service',       model.TableService)
    , ('pickup_locations',    [PickupLocation])
    ], name='BarStatusResult')


class BarStatus(ql.QuerySpec):
    args_spec = [
        ('barID', ID),
    ]
    result_spec = [
        ('bar_status', BarStatusResult),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        result = model.run(model.Bars.get(args['barID']))
        return make_bar_status(result)

    @classmethod
    def feed(cls, args, result_fields):
        with model.connect() as c:
            changefeed = model.Bars             \
                .get(args['barID'])             \
                .changes(include_initial=True)  \
                .run(c)
            for change in changefeed:
                result = change['new_val']
                yield make_bar_status(result)


def make_bar_status(result : model.BarStatus) -> BarStatus:
    if result is None:
        result = {}

    result.setdefault('qdodger_bar', False)
    result.setdefault('taking_orders', False)
    result.setdefault('table_service', model.TableService.Disabled)
    result.setdefault('pickup_locations', {})

    # Convert pickup_locations
    def pickup_location_key(t):
        (name, pickup_location) = t
        return pickup_location['list_position']

    pickup_locations = sorted(result['pickup_locations'].items(),
                              key=pickup_location_key)
    result['pickup_locations'] = [
        { 'name': k, 'open': v['open'] }
            for k, v in pickup_locations ]

    return BarStatus.make(
        bar_status = result,
    )


class UpdateBarStatus(ql.QuerySpec):
    """
    Change the bar status:

        - disable/enable order taking
        - disable/enable table service
            specify whether table service is available for food, drinks, or both
        - add a bar (for pickup)
        - open/close a bar (for pickup)
    """

    args_spec = [
        ('barID',         ID),
        # ('bar_status', model.BarStatus),
        ('statusUpdate', StatusUpdate),
        ('authToken',     str)
    ]
    result_spec = [
        ('status', str),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        userID = auth.validate_token(args['authToken'])
        barID = args['barID']
        status_update = args['statusUpdate']

        if not profile.is_bar_owner(userID, barID):
            raise ValueError("You have not been approved as an owner of this bar (yet).")

        if 'TakingOrders' in status_update:
            model.upsert(model.Bars, model.BarStatus({
                'id': barID,
                'taking_orders': status_update['TakingOrders'],
            }))

        if 'SetTableService' in status_update:
            model.upsert(model.Bars, model.BarStatus({
                'id': barID,
                'table_service': status_update['SetTableService'],
            }))

        if 'AddBar' in status_update:
            command = status_update['AddBar']
            add_pickup_location(barID, command['name'], command['listPosition'])

        if 'SetBarOpen' in status_update:
            command = status_update['SetBarOpen']
            model.run(
                model.Bars.get(barID).update(
                    model.BarStatus({
                        'pickup_locations': {
                            command['name']: {
                                'open': command['open'],
                            },
                        }
                    })
                )
            )

        return UpdateBarStatus.make(status='OK')


class QDodgerPubs(ql.QuerySpec):
    result_spec = [
        ('barIDs', [model.BarID]),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        qd_pubs = model.run(
            model.Bars.filter({'qdodger_bar': True})
                      .pluck('id')
        )
        return QDodgerPubs.make(
            barIDs=[qd_pub['id'] for qd_pub in qd_pubs],
        )

def add_qdodger_bar(barID):
    model.run(
        model.Bars.insert(
            model.BarStatus({
                'id': barID,
                'qdodger_bar': True,
                'taking_orders': False,
                'table_service': model.TableService.Disabled,
                'pickup_locations': {
                    'Main Bar': {
                        'open': False,
                        'list_position': 0,
                    }
                },
            })
        )
    )


def add_pickup_locations(barID, pickup_locations):
    """Add the given pickup locations to the bar"""
    bar_status = model.run(model.Bars.get(barID))
    assert bar_status is not None, barID
    bar_status = make_bar_status(bar_status)
    list_position_offset = len(bar_status['bar_status']['pickup_locations'])
    for i, pickup_location in enumerate(pickup_locations):
        add_pickup_location(barID, pickup_location, list_position_offset + i)

def add_pickup_location(barID, pickup_location, list_position):
    model.run(
        model.Bars.get(barID).update(
            model.BarStatus({
                'pickup_locations': {
                    pickup_location: {
                        'open': False,
                        'list_position': list_position,
                    },
                }
            })
        )
    )

def register(dispatcher):
    dispatcher.register(BarStatus)
    dispatcher.register(UpdateBarStatus)
    dispatcher.register(QDodgerPubs)
