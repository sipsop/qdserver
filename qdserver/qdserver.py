from flask import Flask
# NOTE: These imports are necessary to register components
import time
from qdserver import ql, orders, menu, tags, editor, profile, bar

#=========================================================================#
# Flask App
#=========================================================================#

class Hello(ql.QuerySpec):
    result_spec = [
        ('world', str),
        ('universe', str),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        return {
            "world": "Hello World!",
            "universe": "Hello Universe!",
        }

    @classmethod
    def feed(cls, args, result_fields):
        # Send a hello world update message every second
        while True:
            yield cls.resolve(args, result_fields)
            time.sleep(1)

def setup_dispatcher(dev=False):
    # Set up dispatcher
    dispatcher = ql.Dispatcher(dev=dev)
    orders.register(dispatcher)
    menu.register(dispatcher)
    tags.register(dispatcher)
    profile.register(dispatcher)
    bar.register(dispatcher)
    dispatcher.register(Hello)
    return dispatcher

def setup_routes(app, sockets, path='/api/v1/', dev=False):
    # Setup dispatcher
    dispatcher = setup_dispatcher(dev=dev)

    # Setup routes
    ql.setup_routes(app, sockets, dispatcher, path)
    editor.setup_routes(app, dispatcher, path + 'editor/')
