import datetime

from qdserver import ql
from flask import Flask

dispatcher = ql.Dispatcher()

@dispatcher.register
class Temperature(ql.QuerySpec):
    args_spec = [
        ('when',        float),
    ]
    result_spec = [
        ('timestamp',   str),
        ('celcius',     float),
    ]

    @classmethod
    def resolve(cls, args, result_fields):
        when = datetime.datetime.fromtimestamp(args['when'])
        return {
            'timestamp': when.isoformat(),
        }

    @classmethod
    def resolve_celcius(cls, result, **kw):
        print(result['timestamp'])
        return 24.5

app = Flask(__name__)
ql.setup_routes(app, dispatcher, '/api/v1')
app.run(host='0.0.0.0', port=9000, debug=True)
