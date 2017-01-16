"""
query = {
    OrderHistory: {
        args: {
            token: '...',
            n: 100,
        },
        result: {
            date: '*',
            time: {
                hour:   'String',
                month:  'String',
                day:    'String',
            },
            orderList: [{
                id:         'String',
                menuItemID: 'String',
            }]

        },
    }
}
"""

import json
import time
import inspect
import traceback
import gevent
from collections import UserDict

from curry.typing import \
    ( typeddict, from_json, to_json
    , TypedDict, Dict, List, Alias, Enum, BasicType, Optional, MaybeNone
    )

from flask import request, jsonify, redirect

def expect(value, type):
    if not isinstance(value, type):
        raise ValueError("Expected value of type '%s', got '%s'" % (type.__name__, value))

def expect_list(xs, size):
    expect(xs, list)
    if len(xs) != size:
        raise ValueError("Expected list of size '%d', got list of size '%d'" % (size, len(xs)))

def expect_dict(d, keys):
    expect(d, dict)
    for key in keys:
        if key not in d:
            raise ValueError("Dictionary '%s' is missing key '%s'" % (d, key))

def make_type(query_spec) -> TypedDict:
    if isinstance(query_spec, list):
        [spec] = query_spec
        return [make_type(spec)]
    elif isinstance(query_spec, dict):
        return {make_type(k) : make_type(v) for k, v in query_spec.items()}
    elif not inspect.isclass(query_spec) or not issubclass(query_spec, QuerySpec):
        return query_spec
    fields = [(field_name, make_type(query_spec))
                  for field_name, query_spec in query_spec.result_spec]
    return typeddict(fields, name=query_spec.__name__)

def slice_fields(result_fields, json_obj):
    # TODO: Resolve specific fields here, so that we do not need to pass
    #       around 'result_fields' in 'query()'
    if isinstance(json_obj, list):
        [result_fields] = result_fields
        return [slice_fields(result_fields, obj) for obj in json_obj]
    elif isinstance(json_obj, (dict, UserDict)):
        return { k: slice_fields(result_fields[k], v)
                     for k, v in json_obj.items() if k in result_fields }
    else:
        return json_obj

def unpack_enum(enum_value):
    [enum_name, value_name] = enum_value.split('.')
    return value_name

type_strings = {
    bool: 'Bool',
    str: 'String',
    int: 'Int',
    float: 'Float',
}

# TODO: Write a 'match_types' function that generalizes the below two functions

def validate_args(args, typeddict, query_spec):
    for field_name in args:
        if field_name not in typeddict.type_spec:
            raise ValueError("Invalid argument with name '%s' for query of type '%s'" % (
                field_name, query_spec.__name__))

    missing_fields = set(typeddict.type_spec) - set(args)
    if missing_fields:
        raise ValueError("Missing arguments '%s' for query of type '%s'" % (
            ', '.join(sorted(missing_fields)), query_spec.__name__))

def validate_result_fields(result_fields, typeddict, query_spec):
    for field_name, field_type in result_fields.items():
        if field_name not in typeddict.type_spec:
            raise ValueError("Invalid field with name '%s' for query of type '%s'" % (
                field_name, query_spec.__name__))
        ty = typeddict.type_spec[field_name]
        if isinstance(field_type, str):
            if ty in type_strings and type_strings[ty] != field_type:
                raise ValueError(
                    "Expect type string '%s' for field name '%s', got '%s'" % (
                        type_strings[ty], field_name, field_type))
        # if isinstance(ty, specs.List) and not isinstance(field_type, list):
        #     raise ValueError("Expected a list for field name '%s', got '%s'" % (
        #         field_name, field_type))

def resolve_fragments(query_spec, fragments):
    if isinstance(query_spec, list):
        return [resolve_fragments(query_spec[0], fragments)]
    elif isinstance(query_spec, dict):
        return {k : resolve_fragments(v, fragments) for k, v in query_spec.items()}
    elif isinstance(query_spec, str) and query_spec in fragments:
        # This does not support recursion... :)
        return resolve_fragments(fragments[query_spec], fragments)
    else:
        return query_spec

def match_type(spec, query_spec, fragments):
    if isinstance(spec, Dict):
        if not isinstance(query_spec, dict):
            raise ValueError("Expected a dictionary query spec, got '%s'" % (query_spec,))
        for field_name, field_type in query_spec.items():
            if field_name not in spec.key_to_value_spec:
                raise ValueError(
                    "Invalid field with name '%s' for query of type '%s'" % (
                        field_name, spec.name))

            field_spec = spec.key_to_value_spec[field_name]
            field_query_spec = query_spec[field_name]
            match_type(field_spec, field_query_spec, fragments)
    elif isinstance(spec, List):
        if not isinstance(query_spec, list):
            raise ValueError(
                "Expected a list query spec, got '%s'" % (query_spec,))
        [query_spec] = query_spec
        match_type(spec.item_spec, query_spec, fragments)
    elif isinstance(spec, Alias):
        match_type(spec.alias_spec, query_spec, fragments)
    elif isinstance(spec, Enum):
        if query_spec != 'String':
            raise ValueError(
                "Expected type 'String' for enum of type '%s'" % (spec.name,))
    elif isinstance(spec, (Optional, MaybeNone)):
        match_type(spec.item_spec, query_spec, fragments)
    elif isinstance(spec, BasicType):
        ty = spec.ty
        if isinstance(query_spec, str) and ty in type_strings:
            if type_strings[ty] != query_spec:
                raise ValueError(
                    "Expect type string '%s', got '%s'" % (
                        type_strings[ty], query_spec))
        else:
            raise ValueError("Expected type '%s', got '%s'" % (spec, query_spec))
    else:
        raise ValueError("Expected type '%s', got '%s'" % (spec, query_spec))


class QuerySpecMeta(type):

    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls.update_type()

    def update_type(cls):
        if cls.args_spec:
            arg_fields = [(field_name, make_type(arg_spec))
                              for field_name, arg_spec in cls.args_spec]
            cls.args_type = typeddict(arg_fields, name=cls.__name__)
        else:
            cls.args_type = None

        if cls.result_spec:
            cls.result_type = make_type(cls)
        else:
            cls.result_type = None

        cls.make = dict # cls.result_type


class QuerySpec(object, metaclass=QuerySpecMeta):

    args_spec   = None
    result_spec = None

    args_type   = None  # typeddict created from args_spec
    result_type = None  # typeddict created from result_spec
    make        = None  # constructor

    @classmethod
    def handle_request(cls, json_query, fragments, dev=True, query_type='query'):
        if cls.args_type:
            expect_dict(json_query, ['args', 'result'])
            args_value = json_query['args']
            args = from_json(args_value, cls.args_type)
        else:
            expect_dict(json_query, ['result'])
            args = {}
        query_spec = resolve_fragments(json_query['result'], fragments)
        if dev:
            match_type(cls.result_type, query_spec, fragments)

        return cls.query(args, query_spec, query_type)

    @classmethod
    def query(cls, args, result_fields, query_type='query'):
        if cls.args_type:
            validate_args(args, cls.args_type, cls)
        # validate_result_fields(result_fields, cls.result_type, cls)

        # Invoke the resolve() function
        if query_type == 'query':
            result = cls.resolve(args=args, result_fields=result_fields)
            return cls._resolve_result(args, result_fields, result)

        assert query_type == 'feed'
        feed = cls.feed(args=args, result_fields=result_fields)
        return (cls._resolve_result(args, result_fields, result)
                    for result in feed)

    @classmethod
    def _resolve_result(cls, args, result_fields, result):
        result = cls._resolve_fields(args, result_fields, result)
        return cls.dump_to_json(result, result_fields)

    @classmethod
    def _resolve_fields(cls, args, result_fields, result):
        """
        Resolve fields from 'resolve_*' methods, when requested by the query.
        """
        for k in result:
            if k not in cls.result_type.type_spec:
                raise ValueError("Invalid field '%s' returned from '%s.resolve()'" % (
                    k, cls.__name__))

        # Resolve specific fields
        for field_name, field_type in result_fields.items():
            resolver = getattr(cls, 'resolve_' + field_name, None)
            if resolver is not None:
                result[field_name] = resolver(
                    result_fields=result_fields[field_name],
                    args=args,
                    result=result,
                    )

        result = { k: v for k, v in result.items() if k in result_fields }

        # Check that all fields are there
        for field_name in result_fields:
            if field_name not in result:
                raise ValueError("Missing field '%s' for type '%s', got '%s'" % (
                    field_name, cls.__name__, result))

        return result

    @classmethod
    def dump_to_json(cls, result, result_fields):
        result = slice_fields(result_fields, result)
        return to_json(result, cls.result_type)

    @classmethod
    def resolve(cls, args, result_fields):
        """
        Function used to resolve the query for the given arguments.
        This should be implemented for 'top-level' queries registerd with the
        dispatcher, e.g.:

            @dispatcher.register
            class Temperature(object):
                name = 'Temparature'
                args_spec = [
                    ('when',        float),
                ]
                result_spec = [
                    ('timestamp',   str),
                    ('celcius',     float),
                ]

                @classmethod
                def resolve(cls, dispatcher, args):
                    when = datetime.datetime.fromtimestamp(args['when'])
                    return {
                        'timestamp': when.isoformat(),
                        'celcius':   calculate_temperature(when),
                    }

        See also example.py
        """
        raise NotImplementedError("'resolve' function not implemented")

    @classmethod
    def resolve_field_name_here(cls, result : dict, args, result_fields):
        """
        Resolve a specific field name if requested.

        Arguments
        =========
            result_fields: { field_name : result_fields_for_field }
            result:
                result object so far
        """
        raise NotImplemented("Implement resolve function for 'field_name_here'")


class Dispatcher(object):
    def __init__(self, dev=True):
        self.queries = {}
        self.dev = dev

    def register(self, query_spec):
        # assert query_spec.name is not None, query_spec
        # assert query_spec.name not in self.queries, query_spec
        self.queries[query_spec.__name__] = query_spec
        return query_spec

    def dispatch(self, query, query_type='query'):
        try:
            start_time = time.time()
            expect(query, dict)
            fragments = query.pop('fragments', {})
            [query_name] = query.keys()
            result = {
                'result': self._run_query(query_name, query, fragments, query_type)
            }
            end_time = time.time()
            print("Resolving %s '%s' took '%.2f' seconds" % (
                            query_type, query_name, end_time - start_time))
            return result
        except Exception as e:
            return error_response(query, e)

    def dispatch_feed(self, query):
        response = self.dispatch(query, query_type='feed')
        generator = response.get('result', None)
        if generator:
            # Successful feed
            [query_name] = query.keys()
            for result in generator:
                yield {'result': result}
        else:
            # Error response
            yield response

    def _run_query(self, key, query, fragments, query_type='query'):
        query_spec = self.queries[key]
        return query_spec.handle_request(
            query[key],
            fragments,
            dev=self.dev,
            query_type=query_type,
        )


def error_response(query, e : Exception):
    print("--------------------------------------------------------")
    print("ERROR WITH QUERY", query)
    traceback.print_exc()
    print("--------------------------------------------------------")
    return {
        'error': str(e),
    }


def setup_routes(app, sockets, dispatcher, route):
    @app.route(route, methods=['GET', 'POST'])
    def request_handler():
        """
        HTTP request handler
        """
        # print(request.method, request.headers)
        if request.method == 'GET':
            return redirect(route + 'editor/')
        query = request.get_json(force=True)
        return jsonify(**dispatcher.dispatch(query))

    def _request_handler_websockets(ws, active_greenlets):
        """
        Request handler for web sockets
        """
        # TODO: Periodically restart dead feeds
        import random
        id = random.randrange(200)

        def kill(message_id):
            active_greenlets[message_id].kill(block=True)
            active_greenlets.pop(message_id)

        while ws.connected:
            message = ws.receive()
            if message is None:
                break
            if message == b'':
                continue

            print("got something on connection:", id)
            # Parse message
            try:
                message = message.decode('UTF-8')
                message = json.loads(message)
                message_id = message['messageID']
                if message_id == 'ping':
                    ws_send(ws, 'ping', {})
                    continue
                query_type = message['type']
                if query_type == 'unsubscribe':
                    print("Unsubscribing from feed", message_id)
                    kill(message_id)
                    continue
                query = message['query']
            except Exception as e:
                # Error during feed or query
                ws_send(ws, 'pong', error_response(message, e))
                break

            # Dipsatch query
            if query_type == 'query':
                result = dispatcher.dispatch(query)
                ws_send(ws, message_id, result)
            else:
                assert query_type == 'feed'

                def run_feed(ws, query, message_id):
                    feed = dispatcher.dispatch_feed(query)
                    for result in feed:
                        print("Feed '%s' produced result on conn. %s" % (message_id, id))
                        ws_send(ws, message_id, result)
                        if not ws.connected:
                            break

                if message_id in active_greenlets:
                    # Feed already exists, kill previous version
                    kill(message_id)
                active_greenlets[message_id] = gevent.spawn(run_feed, ws, query, message_id)

    def request_handler_websockets(ws):
        active_greenlets = {}
        try:
            _request_handler_websockets(ws, active_greenlets)
        finally:
            for message_id, greenlet in active_greenlets.items():
                greenlet.kill(block=True)
            print("Bye!")

    if sockets is not None:
        sockets.route('/api/v1/websocket/')(request_handler_websockets)

def ws_send(ws, message_id, result):
    result['messageID'] = message_id
    ws.send(json.dumps(result))
